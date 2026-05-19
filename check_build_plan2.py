import re

with open(r"C:\Users\ynaka\study_planner\excel_export.py", "r", encoding="utf-8") as f:
    excel = f.read()

match = re.search(r'def build_plan_data\(.*?(?=\ndef |\Z)', excel, re.DOTALL)
if match:
    func = match.group(0)
    lines = func.split('\n')
    for i, line in enumerate(lines):
        if 'return {' in line:
            for l in lines[i:i+20]:
                print(l)
            break