import os

base = r"C:\Users\ynaka\study_planner"

with open(os.path.join(base, "templates", "preview.html"), "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"総行数: {len(lines)}")
print("\n=== 100〜175行目 ===")
for i in range(99, min(175, len(lines))):
    print(f"  {i+1}: {lines[i].rstrip()}")