with open(r"C:\Users\ynaka\study_planner\templates\assignments_list.html", "r", encoding="utf-8") as f:
    lines = f.readlines()
for i in range(437, min(500, len(lines))):
    print(f"{i+1}: {lines[i].rstrip()}")