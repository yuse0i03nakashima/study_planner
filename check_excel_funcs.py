import re
with open(r"C:\Users\ynaka\study_planner\excel_export.py", "r", encoding="utf-8") as f:
    content = f.read()
funcs = re.findall(r'^def (\w+)\(', content, re.MULTILINE)
print("excel_export.pyの関数一覧:")
for f in funcs:
    print(f"  {f}")