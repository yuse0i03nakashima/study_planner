import re

with open(r"C:\Users\ynaka\study_planner\app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# save_plan_history・historyルート・plan_outputを確認
targets = ["save_plan_history", "plan_history", "plan_output",
           "def history", "@app.route.*history"]
for i, line in enumerate(lines, 1):
    if any(kw in line for kw in targets[:4]) or \
       re.search(r'@app\.route.*history', line):
        print(f"{i}: {line.rstrip()}")

with open(r"C:\Users\ynaka\study_planner\database.py", "r", encoding="utf-8") as f:
    db = f.read()

print("\n=== database.py: plan_history関連 ===")
for i, line in enumerate(db.splitlines(), 1):
    if "plan_history" in line or "plan_output" in line or \
       "save_plan" in line or "get_plan" in line:
        print(f"{i}: {line.rstrip()}")