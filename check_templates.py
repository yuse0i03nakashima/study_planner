import os

base = r"C:\Users\ynaka\study_planner"

for fname in ["problems.html", "problems_list.html", "assignments_list.html"]:
    path = os.path.join(base, "templates", fname)
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    print(f"\n=== {fname}: Min/estimated関連行 ===")
    for i, line in enumerate(lines, 1):
        if any(kw in line for kw in [
            "estimated_minutes", "Min", "分", "total_minutes"
        ]):
            print(f"  {i}: {line.rstrip()}")