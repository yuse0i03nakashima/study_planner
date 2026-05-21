with open(r"C:\Users\ynaka\study_planner\app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("=== assignments_bulk_update (1147〜1170行目) ===")
for i in range(1146, min(1170, len(lines))):
    print(f"  {i+1}: {lines[i].rstrip()}")