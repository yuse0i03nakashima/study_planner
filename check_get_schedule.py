import re

with open(r"C:\Users\ynaka\study_planner\database.py", "r", encoding="utf-8") as f:
    db = f.read()

match = re.search(r'def get_schedule\(.*?(?=\ndef )', db, re.DOTALL)
if match:
    print(match.group(0)[:2000])