import os

base = r"C:\Users\ynaka\study_planner"
excel_path = os.path.join(base, "excel_export.py")

with open(excel_path, "r", encoding="utf-8") as f:
    content = f.read()

old = """    def try_assign(item, search_dates):
        minutes = get_adjusted_minutes(item)
        textbook = item["textbook"]
        valid = [d for d in search_dates if remaining.get(d, 0) >= minutes]
        sorted_d = sorted(valid,
                          key=lambda d: date_textbook_count[d][textbook])
        for d in sorted_d:
            remaining[d] -= minutes
            item["assigned_date"] = d
            date_textbook_count[d][textbook] += 1
            assigned.append(item)
            return True
        return False"""

new = """    def try_assign(item, search_dates):
        minutes = get_adjusted_minutes(item)
        textbook = item["textbook"]
        valid = [d for d in search_dates if remaining.get(d, 0) >= minutes]
        if not valid:
            return False
        # テキスト分散：同じテキストが少ない日を優先するが、
        # 時間があれば同じテキストでも割り当てる
        sorted_d = sorted(valid,
                          key=lambda d: (date_textbook_count[d][textbook],
                                         -remaining[d]))
        d = sorted_d[0]
        remaining[d] -= minutes
        item["assigned_date"] = d
        date_textbook_count[d][textbook] += 1
        assigned.append(item)
        return True"""

if old in content:
    content = content.replace(old, new)
    with open(excel_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ try_assign関数を修正しました")
else:
    print("❌ 対象箇所が見つかりません")
    # 現在のtry_assign周辺を表示
    idx = content.find("def try_assign")
    if idx >= 0:
        print(content[idx:idx+400])