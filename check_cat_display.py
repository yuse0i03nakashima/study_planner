import os

base = r"C:\Users\ynaka\study_planner"

with open(os.path.join(base, "templates", "assignments_list.html"), "r", encoding="utf-8") as f:
    lines = f.readlines()

# カテゴリ表示・セレクトオプション周辺を確認
print("=== カテゴリ表示・セレクト関連行 ===")
for i, line in enumerate(lines, 1):
    if any(kw in line for kw in [
        "a.category", "cat_en", "option value", "row-", "inline-select",
        "data-field=\"category\""
    ]):
        print(f"  {i}: {line.rstrip()}")