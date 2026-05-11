import os

base = r"C:\Users\ynaka\study_planner"
app_path = os.path.join(base, "app.py")

with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

old = '''        assigned, unassigned = assign_days(plan, schedule)'''
new = '''        assigned, unassigned = assign_days(plan, schedule, student_id, start_date, target_date)'''

if old in content:
    content = content.replace(old, new)
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ app.py を修正しました")
else:
    print("❌ 対象箇所が見つかりません")
    # 周辺を確認
    idx = content.find("assign_days")
    if idx >= 0:
        print("現在のassign_days呼び出し：")
        print(content[idx-50:idx+100])