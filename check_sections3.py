with open(r"C:\Users\ynaka\study_planner\templates\sections.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if "<script" in line or "</script" in line or "buildTable" in line:
        print(f"{i}: {line.rstrip()}")