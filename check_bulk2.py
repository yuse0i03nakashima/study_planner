with open(r"C:\Users\ynaka\study_planner\app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if "bulk_update" in line or "assignments_bulk" in line:
        print(f"  {i}: {line.rstrip()}")