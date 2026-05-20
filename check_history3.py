with open(r"C:\Users\ynaka\study_planner\database.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# plan_historyテーブル定義とsave/get関数を表示
printing = False
for i, line in enumerate(lines, 1):
    if "plan_history" in line and "CREATE" in line:
        printing = True
    if printing:
        print(f"{i}: {line.rstrip()}")
    if printing and line.strip().startswith(")") and "CREATE" not in line:
        printing = False
        print("---")

# save_plan_history・get_plan_histories関数を表示
for i, line in enumerate(lines, 1):
    if "def save_plan_history" in line or "def get_plan_histories" in line:
        start = i - 1
        for j in range(start, min(start+25, len(lines))):
            print(f"{j+1}: {lines[j].rstrip()}")
        print("---")

with open(r"C:\Users\ynaka\study_planner\app.py", "r", encoding="utf-8") as f:
    alines = f.readlines()

# historyルートとdownload/deleteルートを表示
for i, line in enumerate(alines, 1):
    if "def history" in line or "def history_download" in line or \
       "def history_delete" in line:
        for j in range(i-2, min(i+25, len(alines))):
            print(f"{j+1}: {alines[j].rstrip()}")
        print("---")