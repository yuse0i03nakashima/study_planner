with open(r"C:\Users\ynaka\study_planner\pdf_export.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"総行数: {len(lines)}")
print("\n=== 関数定義行 ===")
for i, line in enumerate(lines, 1):
    if line.startswith("def ") or "_pdf_prob_text" in line:
        print(f"  {i}: {line.rstrip()}")

print("\n=== 170〜185行目 ===")
for i in range(169, min(185, len(lines))):
    print(f"  {i+1}: {lines[i].rstrip()}")