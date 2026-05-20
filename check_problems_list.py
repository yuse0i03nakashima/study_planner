import re
with open(r"C:\Users\ynaka\study_planner\app.py", "r", encoding="utf-8") as f:
    app = f.read()
match = re.search(r'def problems_list\(\):.*?(?=\n@app\.route|\nif __name__)', app, re.DOTALL)
if match:
    print(match.group(0)[:2000])