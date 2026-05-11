import os

base = r"C:\Users\ynaka\study_planner"
excel_path = os.path.join(base, "excel_export.py")

with open(excel_path, "r", encoding="utf-8") as f:
    content = f.read()

old = """def assign_days(plan, schedule):
    remaining = {d: m for d, m in schedule.items()}
    dates_sorted = sorted(remaining.keys())
    assigned = []
    unassigned = []
    for item in plan:
        minutes = item["estimated_minutes"]
        placed = False
        for d in dates_sorted:
            if remaining[d] >= minutes:
                remaining[d] -= minutes
                item["assigned_date"] = d
                assigned.append(item)
                placed = True
                break
        if not placed:
            item["assigned_date"] = None
            unassigned.append(item)
    return assigned, unassigned"""

new = """MASTERY_MULTIPLIER = {1: 1.3, 2: 1.0, 3: 0.5}

def get_adjusted_minutes(item):
    mastery_str = item.get("mastery", "★")
    mastery_level = len(mastery_str) if mastery_str else 1
    mastery_level = max(1, min(3, mastery_level))
    multiplier = MASTERY_MULTIPLIER.get(mastery_level, 1.0)
    base_minutes = item["estimated_minutes"]
    return max(5, round(base_minutes * multiplier / 5) * 5)

def assign_days(plan, schedule):
    remaining = {d: m for d, m in schedule.items()}
    dates_sorted = sorted(remaining.keys())
    assigned = []
    unassigned = []
    for item in plan:
        minutes = get_adjusted_minutes(item)
        item["adjusted_minutes"] = minutes
        placed = False
        for d in dates_sorted:
            if remaining[d] >= minutes:
                remaining[d] -= minutes
                item["assigned_date"] = d
                assigned.append(item)
                placed = True
                break
        if not placed:
            item["assigned_date"] = None
            unassigned.append(item)
    return assigned, unassigned"""

if old in content:
    content = content.replace(old, new)
    with open(excel_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ excel_export.py を更新しました")
else:
    print("❌ 対象箇所が見つかりません。excel_export.pyの内容を確認してください。")