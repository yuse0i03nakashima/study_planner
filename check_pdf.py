import re

with open(r"C:\Users\ynaka\study_planner\pdf_export.py", "r", encoding="utf-8") as f:
    content = f.read()

funcs = re.findall(r'^def (\w+)\(', content, re.MULTILINE)
print(f"関数一覧: {funcs}")
print(f"\n総行数: {len(content.splitlines())}")
print("\n最初の50行:")
for i, line in enumerate(content.splitlines()[:50], 1):
    print(f"  {i}: {line}")