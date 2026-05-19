import os, re

app_path = r"C:\Users\ynaka\study_planner\app.py"

with open(app_path, "r", encoding="utf-8") as f:
    app = f.read()

# problemsルートのPOST処理を抜き出して確認
match = re.search(
    r'def problems\(\):.*?(?=\n@app\.route|\nif __name__)',
    app, re.DOTALL
)
if match:
    print(match.group(0)[:3000])
else:
    print("❌ problemsルートが見つかりません")