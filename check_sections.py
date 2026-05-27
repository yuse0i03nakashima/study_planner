import os

base = r"C:\Users\ynaka\study_planner"

# sections.htmlの構造確認
with open(os.path.join(base, "templates", "sections.html"), "r", encoding="utf-8") as f:
    lines = f.readlines()
print(f"sections.html: {len(lines)}行")
print("\n=== Problems in this Textbook部分 ===")
for i, line in enumerate(lines, 1):
    if any(kw in line for kw in [
        "problem", "section_id", "Problems in", "checkbox",
        "assign", "Add to", "section"
    ]):
        print(f"  {i}: {line.rstrip()}")

# problems.htmlのSection選択欄を確認
with open(os.path.join(base, "templates", "problems.html"), "r", encoding="utf-8") as f:
    plines = f.readlines()
print(f"\nproblems.html: {len(plines)}行")
print("\n=== Section関連行 ===")
for i, line in enumerate(plines, 1):
    if "section" in line.lower():
        print(f"  {i}: {line.rstrip()}")

# app.pyのsection_id関連を確認
with open(os.path.join(base, "app.py"), "r", encoding="utf-8") as f:
    alines = f.readlines()
print("\n=== app.py: section_id関連 ===")
for i, line in enumerate(alines, 1):
    if "section_id" in line and i < 200:
        print(f"  {i}: {line.rstrip()}")