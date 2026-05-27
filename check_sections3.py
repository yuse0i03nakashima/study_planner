import os

base = r"C:\Users\ynaka\study_planner"

# sections.htmlの230行目以降（既存ヘッダーの重複確認）
with open(os.path.join(base, "templates", "sections.html"), "r", encoding="utf-8") as f:
    lines = f.readlines()
print("=== sections.html 230〜255行目 ===")
for i in range(229, min(255, len(lines))):
    print(f"  {i+1}: {lines[i].rstrip()}")

# problems.htmlのTextbook選択周辺（165〜200行目）
with open(os.path.join(base, "templates", "problems.html"), "r", encoding="utf-8") as f:
    plines = f.readlines()
print("\n=== problems.html 160〜200行目 ===")
for i in range(159, min(200, len(plines))):
    print(f"  {i+1}: {plines[i].rstrip()}")

# loadProblemSections関数の確認
print("\n=== problems.html: loadProblemSections/onchange ===")
for i, line in enumerate(plines, 1):
    if "loadProblemSections" in line or ('onchange' in line and 'textbook' in line.lower()):
        print(f"  {i}: {line.rstrip()}")