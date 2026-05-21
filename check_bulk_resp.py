with open(r"C:\Users\ynaka\study_planner\app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("=== assignments_bulk_update ===")
for i, line in enumerate(lines, 1):
    if 1113 <= i <= 1140:
        print(f"  {i}: {line.rstrip()}")