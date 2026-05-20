with open(r"C:\Users\ynaka\study_planner\templates\sections.html", "r", encoding="utf-8") as f:
    lines = f.readlines()
print(f"総行数: {len(lines)}")
for i, line in enumerate(lines, 1):
    print(f"{i}: {line.rstrip()}")