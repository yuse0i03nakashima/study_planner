import os

base = r"C:\Users\ynaka\study_planner"

# assignments_list.htmlのAdd Assignment部分を確認
with open(os.path.join(base, "templates", "assignments_list.html"), "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"=== assignments_list.html ({len(lines)}行): Add部分 ===")
for i, line in enumerate(lines, 1):
    if any(kw in line for kw in ["Add", "add", "al-search", "Problem Search", "al-problem"]):
        print(f"  {i}: {line.rstrip()}")

# record.htmlの構造確認
with open(os.path.join(base, "templates", "record.html"), "r", encoding="utf-8") as f:
    rlines = f.readlines()

print(f"\n=== record.html ({len(rlines)}行): 主要部分 ===")
for i, line in enumerate(rlines, 1):
    if any(kw in line for kw in [
        "student", "textbook", "problem", "score", "select",
        "form", "submit", "label", "<select"
    ]):
        if i < 120:
            print(f"  {i}: {line.rstrip()}")

# app.pyのrecordルートとassignments/addルートを確認
with open(os.path.join(base, "app.py"), "r", encoding="utf-8") as f:
    alines = f.readlines()

print("\n=== app.py: /assignments/add・/record ルート ===")
for i, line in enumerate(alines, 1):
    if any(kw in line for kw in [
        'route("/assignments/add"', 'route("/record"',
        'def assignments_add', 'def record'
    ]):
        print(f"  {i}: {line.rstrip()}")