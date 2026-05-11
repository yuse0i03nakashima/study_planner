import sqlite3

DB_PATH = r"C:\Users\ynaka\study_planner\study_planner.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

student_id = "S003"
scheduled_date = "2026-05-05"

# 大問29〜38（復習）：problem_id 176〜185
fukushu_ids = list(range(176, 186))

# 大問17〜28（予習）：problem_id 164〜175
yosyu_ids = list(range(164, 176))

# 登録前に既存の出題予定を確認・削除
all_ids = fukushu_ids + yosyu_ids
for pid in all_ids:
    c.execute("DELETE FROM assignments WHERE student_id=? AND problem_id=?",
              (student_id, pid))

# 復習として登録
for pid in fukushu_ids:
    c.execute("""
        INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
        VALUES (?, ?, ?, ?)
    """, (student_id, pid, scheduled_date, "復習"))

print(f"✅ 復習 {len(fukushu_ids)}問 登録しました（大問29〜38）")

# 予習として登録
for pid in yosyu_ids:
    c.execute("""
        INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
        VALUES (?, ?, ?, ?)
    """, (student_id, pid, scheduled_date, "予習"))

print(f"✅ 予習 {len(yosyu_ids)}問 登録しました（大問17〜28）")

conn.commit()

# 確認
c.execute("""
    SELECT a.category, a.scheduled_date, p.problem_number, p.problem_id
    FROM assignments a
    JOIN problems p ON a.problem_id = p.problem_id
    WHERE a.student_id=? AND a.scheduled_date=?
    ORDER BY a.category, p.problem_id
""", (student_id, scheduled_date))
rows = c.fetchall()
print(f"\n=== 登録確認（{scheduled_date}） ===")
for r in rows:
    print(f"  [{r[0]}] {r[2]} (ID:{r[3]})")

conn.close()