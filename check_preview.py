import os, re

app_path = r"C:\Users\ynaka\study_planner\app.py"
with open(app_path, "r", encoding="utf-8") as f:
    app = f.read()

match = re.search(r'def preview\(\):.*?(?=\n@app\.route|\nif __name__)', app, re.DOTALL)
if match:
    print(match.group(0)[:2000])