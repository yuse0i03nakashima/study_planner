import os

base = r"C:\Users\ynaka\study_planner"
excel_path = os.path.join(base, "excel_export.py")

with open(excel_path, "r", encoding="utf-8") as f:
    content = f.read()

old = '''def priority_score(item):
    group = CATEGORY_GROUP.get(item["category"], 1)
    mastery = item.get("mastery_int", 1)
    review_value = item.get("review_value", 3)
    importance = item.get("importance", 3)
    difficulty = item.get("difficulty", 3)
    return (group, mastery, -review_value, -importance, difficulty)'''

new = '''def priority_score(item):
    group = CATEGORY_GROUP.get(item["category"], 1)
    mastery = int(item.get("mastery_int", 1) or 1)
    review_value = int(item.get("review_value", 3) or 3)
    importance = int(item.get("importance", 3) or 3)
    difficulty = int(item.get("difficulty", 3) or 3)
    return (group, mastery, -review_value, -importance, difficulty)'''

if old in content:
    content = content.replace(old, new)
    with open(excel_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ excel_export.py を修正しました")
else:
    print("❌ 対象箇所が見つかりません")