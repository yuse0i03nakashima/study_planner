import os

base = r"C:\Users\ynaka\study_planner"

with open(os.path.join(base, "mcp_server.py"), "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"総行数: {len(lines)}")
print("\n=== カテゴリ・score・total_minutes関連 ===")
for i, line in enumerate(lines, 1):
    if any(kw in line for kw in [
        "予習", "復習", "定着", "再定着", "New", "Recall", "Drill", "Reinforce",
        "total_minutes", "score", "category", "Category"
    ]):
        print(f"  {i}: {line.rstrip()}")