import os

base = r"C:\Users\ynaka\study_planner"
excel_path = os.path.join(base, "excel_export.py")

with open(excel_path, "r", encoding="utf-8") as f:
    content = f.read()

# try_assign以降を丸ごと置き換え
marker = "    assigned = []\n    unassigned = []\n    date_textbook_count"
end_marker = "    return assigned, unassigned"

start_idx = content.find(marker)
end_idx = content.rfind(end_marker)

if start_idx == -1:
    print("開始マーカーが見つかりません")
elif end_idx == -1:
    print("終了マーカーが見つかりません")
else:
    new_block = """    assigned = []
    unassigned = []

    def try_assign(item, search_dates):
        minutes = get_adjusted_minutes(item)
        valid = [d for d in search_dates if remaining.get(d, 0) >= minutes]
        if not valid:
            return False
        d = max(valid, key=lambda x: remaining[x])
        remaining[d] -= minutes
        item["assigned_date"] = d
        assigned.append(item)
        return True

    plan_sorted = sorted(plan, key=priority_score)
    review_list = [p for p in plan_sorted
                   if p["category"] in ("復習", "定着", "再定着")]
    yosyu_list = sorted(
        [p for p in plan if p["category"] == "予習"],
        key=lambda x: x.get("problem_id", 0))

    for item in [p for p in review_list if p["category"] == "復習"]:
        class_dates = subject_class_dates.get(item["subject"], [])
        search_from = dates_sorted[0]
        past = [d for d in class_dates if d <= start_date_str]
        if past:
            search_from = past[-1]
        search = [d for d in dates_sorted if d >= search_from]
        if not try_assign(item, search):
            item["assigned_date"] = None
            unassigned.append(item)

    for item in [p for p in review_list
                 if p["category"] in ("定着", "再定着")]:
        if not try_assign(item, dates_sorted):
            item["assigned_date"] = None
            unassigned.append(item)

    for item in yosyu_list:
        class_dates = subject_class_dates.get(item["subject"], [])
        future = sorted([d for d in class_dates if d > start_date_str])
        if future:
            next_class = future[0]
            search = [d for d in dates_sorted if d <= next_class]
        else:
            search = list(dates_sorted)
        if not try_assign(item, search):
            item["assigned_date"] = None
            unassigned.append(item)

    return assigned, unassigned"""

    content = (content[:start_idx] + new_block +
               content[end_idx + len(end_marker):])
    with open(excel_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ assign_days_v2を修正しました")