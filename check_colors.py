import os, re

templates = r"C:\Users\ynaka\study_planner\templates"

for fname in ["preview.html", "record.html", "assignments_list.html"]:
    fpath = os.path.join(templates, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"\n=== {fname} ===")
    for i, line in enumerate(content.split("\n")):
        if "page-title" in line:
            print(f"  {i+1}: {line.strip()}")