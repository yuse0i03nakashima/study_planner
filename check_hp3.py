with open(r"C:\Users\ynaka\study_planner\excel_export.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"総行数: {len(lines)}")

# 110〜195行目（yosyuロジック全体）を表示
print("\n=== 110〜195行目 ===")
for i in range(109, min(195, len(lines))):
    print(f"{i+1}: {lines[i].rstrip()}")

# SELECT文（55〜75行目付近）を表示
print("\n=== 55〜75行目 ===")
for i in range(54, min(75, len(lines))):
    print(f"{i+1}: {lines[i].rstrip()}")