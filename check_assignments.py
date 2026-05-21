import os

base = r"C:\Users\ynaka\study_planner"

# assignments_list.htmlの一括操作部分を確認
with open(os.path.join(base, "templates", "assignments_list.html"), "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"総行数: {len(lines)}")
print("\n=== 一括操作・Bulk Edit関連行 ===")
for i, line in enumerate(lines, 1):
    if any(kw in line for kw in [
        "bulk", "Bulk", "apply", "Apply", "category", "checkbox",
        "check-all", "selected", "一括"
    ]):
        print(f"  {i}: {line.rstrip()}")

# app.pyの一括操作ルートを確認
with open(os.path.join(base, "app.py"), "r", encoding="utf-8") as f:
    app_lines = f.readlines()

print("\n=== app.py: bulk/apply関連ルート ===")
for i, line in enumerate(app_lines, 1):
    if any(kw in line for kw in ["bulk", "apply", "assignments_bulk"]):
        print(f"  {i}: {line.rstrip()}")