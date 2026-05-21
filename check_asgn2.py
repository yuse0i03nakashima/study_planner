import os

base = r"C:\Users\ynaka\study_planner"

with open(os.path.join(base, "templates", "assignments_list.html"), "r", encoding="utf-8") as f:
    lines = f.readlines()

# startNumEdit・markChanged・changed-row周辺を確認
print("=== startNumEdit・changed-row関連 ===")
for i, line in enumerate(lines, 1):
    if any(kw in line for kw in [
        "startNumEdit", "markChanged", "changed-row", "flash-row",
        "update_field", "problem_id", "data-problem"
    ]):
        print(f"  {i}: {line.rstrip()}")

# 333〜410行目（startNumEdit関数）を確認
print("\n=== 333〜415行目 ===")
for i in range(332, min(415, len(lines))):
    print(f"  {i+1}: {lines[i].rstrip()}")

# app.pyのassignments_bulk_updateを確認
with open(os.path.join(base, "app.py"), "r", encoding="utf-8") as f:
    alines = f.readlines()

print("\n=== app.py: mastery_single_update ===")
for i, line in enumerate(alines, 1):
    if "mastery_single" in line or "startMastery" in line:
        print(f"  {i}: {line.rstrip()}")