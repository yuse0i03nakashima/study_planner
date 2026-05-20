import re

for fname in ["app.py", "excel_export.py", "pdf_export.py"]:
    path = rf"C:\Users\ynaka\study_planner\{fname}"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # plan_historyへの書き込み箇所を確認
    matches = [(i+1, l.rstrip()) for i, l in enumerate(content.splitlines())
               if "plan_history" in l or "plan_archives" in l]
    print(f"\n=== {fname} ===")
    for lineno, line in matches:
        print(f"  {lineno}: {line}")