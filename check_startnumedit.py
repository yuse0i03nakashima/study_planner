with open(r"C:\Users\ynaka\study_planner\templates\assignments_list.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

# startNumEdit関数全体を表示
in_func = False
for i, line in enumerate(lines, 1):
    if "function startNumEdit" in line:
        in_func = True
    if in_func:
        print(f"{i}: {line.rstrip()}")
    if in_func and line.strip() == "}" and i > 420:
        breakwith open(r"C:\Users\ynaka\study_planner\templates\assignments_list.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i in range(437, min(490, len(lines))):
    print(f"{i+1}: {lines[i].rstrip()}")