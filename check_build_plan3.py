import re

with open(r"C:\Users\ynaka\study_planner\excel_export.py", "r", encoding="utf-8") as f:
    excel = f.read()

match = re.search(r'def build_plan_data\(.*?(?=\ndef |\Z)', excel, re.DOTALL)
if match:
    func = match.group(0)
    lines = func.split('\n')
    # rowsの組み立て部分を探す
    for i, line in enumerate(lines):
        if 'rows' in line or 'assigned' in line or 'subjects' in line:
            print(f"{i:3}: {line}")