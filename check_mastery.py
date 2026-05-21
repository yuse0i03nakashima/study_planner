import sqlite3
conn = sqlite3.connect(r"C:\Users\ynaka\study_planner\study_planner.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()

# assignmentsのSELECTでmasteryが正しく取得できているか確認
c.execute("""
    SELECT a.assignment_id, a.student_id, a.problem_id,
           (SELECT h.mastery FROM history h
            WHERE h.student_id=a.student_id AND h.problem_id=a.problem_id
            ORDER BY h.date DESC, h.history_id DESC LIMIT 1) as mastery
    FROM assignments a
    WHERE a.student_id='S000' AND a.problem_id=340
""")
for r in c.fetchall():
    print("assignment:", dict(r))

# historyの最新レコードを確認
c.execute("""
    SELECT history_id, date, mastery, category
    FROM history WHERE student_id='S000' AND problem_id=340
    ORDER BY history_id DESC LIMIT 3
""")
for r in c.fetchall():
    print("history:", dict(r))

conn.close()