with open(r"C:\Users\ynaka\study_planner\excel_export.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"総行数: {len(lines)}")

# 重要箇所を表示
targets = [
    "interleaved_yosyu", "n_yosyu", "yosyu", "total_minutes",
    "build_plan_data", "def build", "SELECT", "estimated_minutes",
    "order_in_textbook", "session", "progress"
]
for i, line in enumerate(lines, 1):
    if any(kw in line for kw in targets):
        print(f"{i}: {line.rstrip()}")