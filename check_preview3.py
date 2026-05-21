import os

base = r"C:\Users\ynaka\study_planner"
prev_path = os.path.join(base, "templates", "preview.html")

with open(prev_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"総行数: {len(lines)}")

# 175行目以降を確認
print("\n=== 175〜210行目 ===")
for i in range(174, min(210, len(lines))):
    print(f"  {i+1}: {lines[i].rstrip()}")