import sqlite3

DB = r"C:\Users\ynaka\study_planner\study_planner.db"
conn = sqlite3.connect(DB)
c = conn.cursor()

tables = [
    "schedule_base", "schedule_override",
    "schedule_base_subject", "schedule_override_subject",
    "class_schedule_base", "class_schedule_override"
]
for t in tables:
    try:
        c.execute(f"PRAGMA table_info({t})")
        cols = [r[1] for r in c.fetchall()]
        print(f"{t}: {cols}")
    except Exception as e:
        print(f"{t}: ERROR {e}")

conn.close()