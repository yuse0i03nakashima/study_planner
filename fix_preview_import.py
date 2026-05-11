import os

base = r"C:\Users\ynaka\study_planner"
app_path = os.path.join(base, "app.py")

with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

old = "from excel_export import assign_days"
new = "from excel_export import assign_days_v2 as assign_days"

if old in content:
    content = content.replace(old, new)
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ app.py を修正しました")
else:
    print("❌ 対象箇所が見つかりません")