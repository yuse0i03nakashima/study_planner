import os

base = r"C:\Users\ynaka\study_planner"

# preview.htmlのloadSections関数を確認
with open(os.path.join(base, "templates", "preview.html"), "r", encoding="utf-8") as f:
    lines = f.readlines()

print("=== preview.html: loadSections関数 ===")
in_func = False
for i, line in enumerate(lines, 1):
    if "loadSections" in line or "sel-subject" in line or "student_id" in line:
        print(f"  {i}: {line.rstrip()}")

# app.pyのapi_sections_by_subject確認
with open(os.path.join(base, "app.py"), "r", encoding="utf-8") as f:
    content = f.read()

import re
m = re.search(r'def api_sections_by_subject.*?(?=\n@app\.route|\nif __name__)', content, re.DOTALL)
if m:
    print(f"\n=== api_sections_by_subject ===")
    print(m.group(0)[:800])