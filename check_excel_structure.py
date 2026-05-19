import re

with open(r"C:\Users\ynaka\study_planner\excel_export.py", "r", encoding="utf-8") as f:
    content = f.read()

# export_excelとwrite_excel_sheetの全体を表示
match = re.search(r'def export_excel\(.*?(?=\ndef |\Z)', content, re.DOTALL)
if match:
    lines = match.group(0).split('\n')
    print(f"export_excel: {len(lines)}行")
    for i, l in enumerate(lines[:50], 1):
        print(f"  {i}: {l}")