import sqlite3, re

# DBの現状確認
DB = r"C:\Users\ynaka\study_planner\study_planner.db"
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("PRAGMA table_info(plan_history)")
cols = c.fetchall()
print("=== plan_historyカラム ===")
for col in cols:
    print(f"  {col['name']} {col['type']}")
c.execute("SELECT * FROM plan_history ORDER BY history_id DESC LIMIT 5")
rows = c.fetchall()
print(f"\n=== 最新5件 ===")
for r in rows:
    print(dict(r))
conn.close()

# app.pyのexport_excel・export_pdfルートの確認
with open(r"C:\Users\ynaka\study_planner\app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("\n=== export_excel周辺（save_plan_history前後10行） ===")
for i, line in enumerate(lines, 1):
    if "save_plan_history" in line or "subject_filter" in line:
        for j in range(max(0,i-5), min(len(lines), i+5)):
            print(f"  {j+1}: {lines[j].rstrip()}")
        print()