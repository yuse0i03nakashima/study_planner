import sqlite3

DB_PATH = r"C:\Users\ynaka\study_planner\study_planner.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

student_id = "S001"

# 全対象ID（71〜79, 81〜96）
all_ids = list(range(71, 80)) + list(range(81, 97))

# 定着に変更（例題143〜165）：id71〜79, 81〜91
teichaku_ids = list(range(71, 80)) + list(range(81, 92))

# 5/5に出題予定変更（例題166〜170）：id92〜96
yosyu_ids = list(range(92, 97))

# ─── 1. テキスト名を変更 ───────────────────────────────
placeholders = ",".join(["?"] * len(all_ids))
c.execute(f"""
    UPDATE problems SET textbook='青チャート数I+A'
    WHERE problem_id IN ({placeholders})
""", all_ids)
print(f"✅ テキスト名変更：{c.rowcount}件")

# ─── 2. 定着に変更（id71〜79, 81〜91） ────────────────
placeholders2 = ",".join(["?"] * len(teichaku_ids))
c.execute(f"""
    UPDATE assignments SET category='定着'
    WHERE student_id=? AND problem_id IN ({placeholders2})
""", [student_id] + teichaku_ids)
print(f"✅ カテゴリを定着に変更：{c.rowcount}件")

# ─── 3. 例題166〜170を5/5の予習に設定（id92〜96） ──────
for pid in yosyu_ids:
    # 既存の出題予定を削除
    c.execute("DELETE FROM assignments WHERE student_id=? AND problem_id=?",
              (student_id, pid))
    # 5/5の予習として登録
    c.execute("""
        INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
        VALUES (?, ?, ?, ?)
    """, (student_id, pid, "2026-05-05", "予習"))
print(f"✅ 例題166〜170を5/5予習として登録：{len(yosyu_ids)}件")

conn.commit()

# ─── 確認 ─────────────────────────────────────────────
print("\n=== 定着確認（例題143〜165） ===")
c.execute(f"""
    SELECT p.problem_number, p.textbook, a.category, a.scheduled_date
    FROM assignments a JOIN problems p ON a.problem_id = p.problem_id
    WHERE a.student_id=? AND a.problem_id IN ({placeholders2})
    ORDER BY p.problem_id
""", [student_id] + teichaku_ids)
for r in c.fetchall():
    print(f"  {r[0]} | {r[1]} | {r[2]} | {r[3]}")

print("\n=== 5/5予習確認（例題166〜170） ===")
c.execute("""
    SELECT p.problem_number, p.textbook, a.category, a.scheduled_date
    FROM assignments a JOIN problems p ON a.problem_id = p.problem_id
    WHERE a.student_id=? AND a.problem_id IN (92,93,94,95,96)
    ORDER BY p.problem_id
""", (student_id,))
for r in c.fetchall():
    print(f"  {r[0]} | {r[1]} | {r[2]} | {r[3]}")

conn.close()