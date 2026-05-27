import os

base = r"C:\Users\ynaka\study_planner"

with open(os.path.join(base, "templates", "sections.html"), "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"sections.html: {len(lines)}行")
print("\n=== 195〜235行目 ===")
for i in range(194, min(235, len(lines))):
    print(f"  {i+1}: {lines[i].rstrip()}")

print("\n=== updateSPCount関数 ===")
for i, line in enumerate(lines, 1):
    if "updateSPCount" in line or "bulk-section-bar" in line or "sp-sel-count" in line:
        print(f"  {i}: {line.rstrip()}")

# problems.html: Textbook selectとSection selectの位置確認
with open(os.path.join(base, "templates", "problems.html"), "r", encoding="utf-8") as f:
    plines = f.readlines()

print("\n=== problems.html 160〜210行目 ===")
for i in range(159, min(210, len(plines))):
    print(f"  {i+1}: {plines[i].rstrip()}")

print("\n=== loadProblemSections関数 ===")
in_fn = False
for i, line in enumerate(plines, 1):
    if "function loadProblemSections" in line:
        in_fn = True
    if in_fn:
        print(f"  {i}: {line.rstrip()}")
    if in_fn and line.strip() == "}" and i > 1:
        break