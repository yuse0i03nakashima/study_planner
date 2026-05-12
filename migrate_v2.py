import sqlite3
import os

DB_PATH = r"C:\Users\ynaka\study_planner\study_planner.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=== Step1: DBマイグレーション開始 ===")

# ─── 1. 新テーブルの作成 ──────────────────────────────

c.execute("""
    CREATE TABLE IF NOT EXISTS series (
        series_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT
    )
""")
print("✅ seriesテーブルを作成しました")

c.execute("""
    CREATE TABLE IF NOT EXISTS textbooks (
        textbook_id INTEGER PRIMARY KEY AUTOINCREMENT,
        series_id INTEGER,
        name TEXT NOT NULL,
        subject TEXT NOT NULL,
        description TEXT,
        FOREIGN KEY (series_id) REFERENCES series(series_id)
    )
""")
print("✅ textbooksテーブルを作成しました")

c.execute("""
    CREATE TABLE IF NOT EXISTS textbook_sections (
        section_id INTEGER PRIMARY KEY AUTOINCREMENT,
        textbook_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        order_index INTEGER DEFAULT 0,
        FOREIGN KEY (textbook_id) REFERENCES textbooks(textbook_id)
    )
""")
print("✅ textbook_sectionsテーブルを作成しました")

c.execute("""
    CREATE TABLE IF NOT EXISTS student_textbooks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        textbook_id INTEGER NOT NULL,
        UNIQUE(student_id, textbook_id),
        FOREIGN KEY (student_id) REFERENCES students(student_id),
        FOREIGN KEY (textbook_id) REFERENCES textbooks(textbook_id)
    )
""")
print("✅ student_textbooksテーブルを作成しました")

c.execute("""
    CREATE TABLE IF NOT EXISTS suppression (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        problem_id INTEGER NOT NULL,
        suppressed_until TEXT NOT NULL,
        reason TEXT,
        created_at TEXT NOT NULL,
        UNIQUE(student_id, problem_id),
        FOREIGN KEY (student_id) REFERENCES students(student_id),
        FOREIGN KEY (problem_id) REFERENCES problems(problem_id)
    )
""")
print("✅ suppressionテーブルを作成しました")

# ─── 2. problemsテーブルに新カラムを追加 ─────────────

try:
    c.execute("ALTER TABLE problems ADD COLUMN textbook_id INTEGER")
    print("✅ problems.textbook_idカラムを追加しました")
except sqlite3.OperationalError:
    print("ℹ️  problems.textbook_idはすでに存在します")

try:
    c.execute("ALTER TABLE problems ADD COLUMN section_id INTEGER")
    print("✅ problems.section_idカラムを追加しました")
except sqlite3.OperationalError:
    print("ℹ️  problems.section_idはすでに存在します")

try:
    c.execute("ALTER TABLE problems ADD COLUMN order_in_textbook INTEGER")
    print("✅ problems.order_in_textbookカラムを追加しました")
except sqlite3.OperationalError:
    print("ℹ️  problems.order_in_textbookはすでに存在します")

conn.commit()

# ─── 3. 既存のtextbook文字列からtextbooksテーブルを生成 ──

print("\n=== 既存テキストデータの移行 ===")

# 既存の全テキスト名を取得
c.execute("SELECT DISTINCT subject, textbook FROM problems ORDER BY subject, textbook")
existing_textbooks = c.fetchall()

print(f"移行対象テキスト数：{len(existing_textbooks)}件")
for row in existing_textbooks:
    print(f"  [{row['subject']}] {row['textbook']}")

# シリーズを自動推定して登録
# テキスト名からシリーズ名を推定するマッピング
series_mapping = {
    "青チャート": "青チャート",
    "体系数学": "体系数学",
    "入門英文問題精講": "英文問題精講シリーズ",
    "速読英単語": "速読英単語",
}

textbook_to_id = {}

for row in existing_textbooks:
    subject = row["subject"]
    textbook_name = row["textbook"]

    # シリーズを推定
    series_id = None
    for key, series_name in series_mapping.items():
        if key in textbook_name:
            # シリーズを登録（なければ）
            c.execute("SELECT series_id FROM series WHERE name=?", (series_name,))
            sr = c.fetchone()
            if sr:
                series_id = sr["series_id"]
            else:
                c.execute("INSERT INTO series (name) VALUES (?)", (series_name,))
                series_id = c.lastrowid
            break

    # テキストを登録（なければ）
    c.execute("SELECT textbook_id FROM textbooks WHERE name=? AND subject=?",
              (textbook_name, subject))
    tb = c.fetchone()
    if tb:
        textbook_id = tb["textbook_id"]
    else:
        c.execute("""
            INSERT INTO textbooks (series_id, name, subject)
            VALUES (?, ?, ?)
        """, (series_id, textbook_name, subject))
        textbook_id = c.lastrowid

    textbook_to_id[(subject, textbook_name)] = textbook_id
    print(f"  ✅ [{subject}] {textbook_name} → textbook_id={textbook_id}")

conn.commit()

# ─── 4. problemsテーブルのtextbook_idを更新 ──────────

print("\n=== problems.textbook_idを更新 ===")

c.execute("SELECT problem_id, subject, textbook FROM problems")
problems = c.fetchall()

for p in problems:
    key = (p["subject"], p["textbook"])
    textbook_id = textbook_to_id.get(key)
    if textbook_id:
        c.execute("UPDATE problems SET textbook_id=? WHERE problem_id=?",
                  (textbook_id, p["problem_id"]))

conn.commit()

# order_in_textbookをproblem_id順に設定
c.execute("SELECT DISTINCT textbook_id FROM problems WHERE textbook_id IS NOT NULL")
tids = [r["textbook_id"] for r in c.fetchall()]
for tid in tids:
    c.execute("""
        SELECT problem_id FROM problems
        WHERE textbook_id=?
        ORDER BY problem_id
    """, (tid,))
    pids = [r["problem_id"] for r in c.fetchall()]
    for order, pid in enumerate(pids, start=1):
        c.execute("UPDATE problems SET order_in_textbook=? WHERE problem_id=?",
                  (order, pid))

conn.commit()
print(f"✅ {len(problems)}問のtextbook_idを更新しました")

# ─── 5. student_textbooksを自動生成 ──────────────────

print("\n=== student_textbooksを生成 ===")

c.execute("""
    SELECT DISTINCT a.student_id, p.textbook_id
    FROM assignments a
    JOIN problems p ON a.problem_id = p.problem_id
    WHERE p.textbook_id IS NOT NULL
""")
pairs = c.fetchall()

for pair in pairs:
    c.execute("""
        INSERT OR IGNORE INTO student_textbooks (student_id, textbook_id)
        VALUES (?, ?)
    """, (pair["student_id"], pair["textbook_id"]))

conn.commit()
print(f"✅ {len(pairs)}件のstudent_textbooks紐づけを生成しました")

# ─── 6. 確認 ─────────────────────────────────────────

print("\n=== 確認 ===")
c.execute("SELECT COUNT(*) as cnt FROM series")
print(f"seriesテーブル：{c.fetchone()['cnt']}件")

c.execute("SELECT COUNT(*) as cnt FROM textbooks")
print(f"textbooksテーブル：{c.fetchone()['cnt']}件")

c.execute("SELECT COUNT(*) as cnt FROM student_textbooks")
print(f"student_textbooksテーブル：{c.fetchone()['cnt']}件")

c.execute("SELECT COUNT(*) as cnt FROM problems WHERE textbook_id IS NOT NULL")
print(f"textbook_id設定済み問題：{c.fetchone()['cnt']}件")

c.execute("""
    SELECT s.name as series, t.name as textbook, t.subject,
           COUNT(p.problem_id) as problem_count
    FROM textbooks t
    LEFT JOIN series s ON t.series_id = s.series_id
    LEFT JOIN problems p ON t.textbook_id = p.textbook_id
    GROUP BY t.textbook_id
    ORDER BY t.subject, t.name
""")
print("\n【テキスト一覧】")
for r in c.fetchall():
    series_name = r["series"] or "（シリーズなし）"
    print(f"  {series_name} > {r['textbook']} [{r['subject']}] {r['problem_count']}問")

c.execute("""
    SELECT s.name, st.student_id, t.name as textbook
    FROM student_textbooks st
    JOIN students s ON st.student_id = s.student_id
    JOIN textbooks t ON st.textbook_id = t.textbook_id
    ORDER BY s.student_id
""")
print("\n【生徒×テキスト紐づけ】")
for r in c.fetchall():
    print(f"  {r['name']}：{r['textbook']}")

conn.close()
print("\n=== Step1完了 ===")
print("次のステップに進む前に結果を確認してください。")