import os

base = r"C:\Users\ynaka\study_planner"

with open(os.path.join(base, "templates", "preview.html"), "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"総行数: {len(lines)}")

# 120〜145行目（Subject選択周辺）を表示
print("\n=== 118〜150行目 ===")
for i in range(117, min(150, len(lines))):
    print(f"  {i+1}: {lines[i].rstrip()}")

# JSのshowToast周辺を表示
print("\n=== showToast周辺 ===")
for i, line in enumerate(lines, 1):
    if "showToast" in line and "function" in line:
        for j in range(max(0,i-3), min(len(lines),i+3)):
            print(f"  {j+1}: {lines[j].rstrip()}")
        break