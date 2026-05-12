import sqlite3

DB_PATH = r"C:\Users\ynaka\study_planner\study_planner.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=== シリーズの修正 ===")

# ─── 追加シリーズを登録 ──────────────────────────────
additional_series = [
    "Graspシリーズ",
    "しっかりわかる問題集",
    "やさしいシリーズ",
    "二次方程式演習",
]

for name in additional_series:
    c.execute("INSERT OR IGNORE INTO series (name) VALUES (?)", (name,))
conn.commit()

# ─── 各テキストにシリーズを紐づけ ───────────────────
series_assignments = {
    "Grasp 数I+A":                  "Graspシリーズ",
    "Grasp 数II+B":                 "Graspシリーズ",
    "しっかりわかる問題集":              "しっかりわかる問題集",
    "しっかりわかる問題集 PART4":       "しっかりわかる問題集",
    "しっかりわかる問題集 PART10":      "しっかりわかる問題集",
    "しっかりわかる問題集 PART12":      "しっかりわかる問題集",
    "しっかりわかる問題集 PART14":      "しっかりわかる問題集",
    "やさしい地理":                   "やさしいシリーズ",
    "やさしい歴史":                   "やさしいシリーズ",
    "二次方程式の利用　演習":            "二次方程式演習",
    "二次方程式の利用　講義":            "二次方程式演習",
    "二次方程式の解法選択　演習":         "二次方程式演習",
    "二次方程式の解法選択　講義":         "二次方程式演習",
}

for textbook_name, series_name in series_assignments.items():
    c.execute("SELECT series_id FROM series WHERE name=?", (series_name,))
    sr = c.fetchone()
    if not sr:
        continue
    series_id = sr["series_id"]
    c.execute("UPDATE textbooks SET series_id=? WHERE name=?",
              (series_id, textbook_name))
    print(f"  ✅ {textbook_name} → {series_name}")

conn.commit()

# ─── 確認 ────────────────────────────────────────────
print("\n【更新後テキスト一覧】")
c.execute("""
    SELECT s.name as series, t.name as textbook, t.subject,
           COUNT(p.problem_id) as cnt
    FROM textbooks t
    LEFT JOIN series s ON t.series_id = s.series_id
    LEFT JOIN problems p ON t.textbook_id = p.textbook_id
    GROUP BY t.textbook_id
    ORDER BY s.name, t.subject, t.name
""")
for r in c.fetchall():
    series_name = r["series"] or "（シリーズなし）"
    print(f"  {series_name} > {r['textbook']} [{r['subject']}] {r['cnt']}問")

conn.close()
print("\n✅ シリーズ修正完了")