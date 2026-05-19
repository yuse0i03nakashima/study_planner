import re

with open(r"C:\Users\ynaka\study_planner\excel_export.py", "r", encoding="utf-8") as f:
    excel = f.read()

match = re.search(r'def assign_days_v2\(.*?(?=\ndef |\Z)', excel, re.DOTALL)
if match:
    print(match.group(0)[:3000])