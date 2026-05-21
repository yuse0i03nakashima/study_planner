import os

base = r"C:\Users\ynaka\study_planner"

# assignments_list.htmlのchanged-rowスタイルを確認
with open(os.path.join(base, "templates", "assignments_list.html"), "r", encoding="utf-8") as f:
    alines = f.readlines()
print("=== assignments_list.html: changed-row関連 ===")
for i, line in enumerate(alines, 1):
    if "changed-row" in line or "changed_row" in line:
        print(f"  {i}: {line.rstrip()}")

# problems_list.htmlのフィルターJS確認
with open(os.path.join(base, "templates", "problems_list.html"), "r", encoding="utf-8") as f:
    plines = f.readlines()
print("\n=== problems_list.html: filter/onchange関連 ===")
for i, line in enumerate(plines, 1):
    if any(kw in line for kw in ["onchange", "filter-form", "filter-subject", "filter-textbook", "Filter →"]):
        print(f"  {i}: {line.rstrip()}")

# problems.htmlのEst.Minutes・Total Minutes周辺を確認
with open(os.path.join(base, "templates", "problems.html"), "r", encoding="utf-8") as f:
    pblines = f.readlines()
print("\n=== problems.html: Est.Minutes・Total Minutes周辺（225〜260行目） ===")
for i in range(224, min(270, len(pblines))):
    print(f"  {i+1}: {pblines[i].rstrip()}")

# app.pyのAdd Problem（学生未選択時の処理）を確認
with open(os.path.join(base, "app.py"), "r", encoding="utf-8") as f:
    applines = f.readlines()
print("\n=== app.py: student_ids・textbook_id関連（70〜100行目） ===")
for i in range(69, min(105, len(applines))):
    print(f"  {i+1}: {applines[i].rstrip()}")