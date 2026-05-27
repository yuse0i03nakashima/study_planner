import os

base = r"C:\Users\ynaka\study_planner"

# sections.htmlのテーブルヘッダー周辺を確認
with open(os.path.join(base, "templates", "sections.html"), "r", encoding="utf-8") as f:
    lines = f.readlines()
print("=== sections.html 196〜230行目 ===")
for i in range(195, min(230, len(lines))):
    print(f"  {i+1}: {lines[i].rstrip()}")

# problems.htmlのSection選択とTextbook選択周辺を確認
with open(os.path.join(base, "templates", "problems.html"), "r", encoding="utf-8") as f:
    plines = f.readlines()
print("\n=== problems.html: section/textbook関連 ===")
for i, line in enumerate(plines, 1):
    if any(kw in line for kw in ["section_id", "f-textbook", "loadProblem", "f-section"]):
        print(f"  {i}: {line.rstrip()}")

print("\n=== problems.html 183〜200行目 ===")
for i in range(182, min(200, len(plines))):
    print(f"  {i+1}: {plines[i].rstrip()}")