import os, subprocess

base = r"C:\Users\ynaka\study_planner"
excel_path = os.path.join(base, "excel_export.py")

with open(excel_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# valsを構築している箇所を確認（510〜540行目付近）
print("=== 505〜545行目 ===")
for i in range(504, min(545, len(lines))):
    print(f"  {i+1}: {lines[i].rstrip()}")