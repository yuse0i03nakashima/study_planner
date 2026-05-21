import os

base = r"C:\Users\ynaka\study_planner"

with open(os.path.join(base, "templates", "record_list.html"), "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"総行数: {len(lines)}")
print("\n=== Mastery・Apply関連行 ===")
for i, line in enumerate(lines, 1):
    if any(kw in line for kw in [
        "Mastery", "mastery", "Apply", "apply", "✎", "✓",
        "changed", "bulk", "onchange", "startMastery"
    ]):
        print(f"  {i}: {line.rstrip()}")