import sys
sys.path.insert(0, r"C:\Users\ynaka\study_planner")
from datetime import date, timedelta
import sqlite3

DB = r"C:\Users\ynaka\study_planner\study_planner.db"
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# S000の基本情報
c.execute("SELECT * FROM students WHERE student_id='S000'")
s = c.fetchone()
print(f"生徒情報: {dict(s) if s else 'なし'}")

if s:
    # 出題予定
    c.execute("""
        SELECT a.*, p.subject, p.textbook, p.problem_number
        FROM assignments a
        JOIN problems p ON a.problem_id = p.problem_id
        WHERE a.student_id='S000'
        LIMIT 5
    """)
    rows = c.fetchall()
    print(f"\n出題予定件数（全体）: ", end="")
    c.execute("SELECT COUNT(*) FROM assignments WHERE student_id='S000'")
    print(c.fetchone()[0])
    for r in rows:
        print(f"  [{r['category']}] {r['subject']} {r['textbook']} {r['problem_number']} → {r['scheduled_date']}")

    # スケジュール
    c.execute("SELECT * FROM schedule_base WHERE student_id='S000'")
    sched = c.fetchall()
    print(f"\n勉強時間設定: {[dict(r) for r in sched]}")

    # class_schedule
    c.execute("SELECT * FROM class_schedule_base WHERE student_id='S000'")
    cs = c.fetchall()
    print(f"授業曜日設定: {[dict(r) for r in cs]}")

conn.close()