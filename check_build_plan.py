import re

with open(r"C:\Users\ynaka\study_planner\excel_export.py", "r", encoding="utf-8") as f:
    excel = f.read()

match = re.search(r'def build_plan_data\(.*?(?=\ndef |\Z)', excel, re.DOTALL)
if match:
    func = match.group(0)
    # returnの箇所を抜き出す
    lines = func.split('\n')
    for i, line in enumerate(lines):
        if 'return' in line:
            start = max(0, i-2)
            end = min(len(lines), i+8)
            print(f"--- return箇所 (line {i}) ---")
            for l in lines[start:end]:
                print(f"  {l}")
            print()