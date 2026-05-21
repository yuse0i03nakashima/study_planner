import os

base = r"C:\Users\ynaka\study_planner"

# problems.htmlの220〜260行目を確認
with open(os.path.join(base, "templates", "problems.html"), "r", encoding="utf-8") as f:
    lines = f.readlines()
print("=== problems.html 215〜260行目 ===")
for i in range(214, min(260, len(lines))):
    print(f"  {i+1}: {lines[i].rstrip()}")

# assignments_list.htmlのBulk Edit・changed-row関連を確認
with open(os.path.join(base, "templates", "assignments_list.html"), "r", encoding="utf-8") as f:
    alines = f.readlines()
print("\n=== assignments_list.html: Bulk Edit・changed-row ===")
for i, line in enumerate(alines, 1):
    if any(kw in line for kw in ["選択行", "Apply to", "changed-row", "flash-row", "Search", "問題番号"]):
        print(f"  {i}: {line.rstrip()}")

# textbooks.htmlのなしを確認
with open(os.path.join(base, "templates", "textbooks.html"), "r", encoding="utf-8") as f:
    tblines = f.readlines()
print("\n=== textbooks.html: なし・ー関連 ===")
for i, line in enumerate(tblines, 1):
    if "なし" in line or "ー" in line or "—" in line:
        print(f"  {i}: {line.rstrip()}")

# problems_list.htmlのFilterボタンを確認
with open(os.path.join(base, "templates", "problems_list.html"), "r", encoding="utf-8") as f:
    pllines = f.readlines()
print("\n=== problems_list.html: Filterボタン周辺 ===")
for i, line in enumerate(pllines, 1):
    if "Filter" in line or "Clear" in line:
        print(f"  {i}: {line.rstrip()}")