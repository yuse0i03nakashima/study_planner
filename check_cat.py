import os

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")

for fname, keywords in [
    ("preview.html", ["category", "badge", "cat_en", "New", "Recall", "prob\."]),
    ("assignments_list.html", ["option value", "row-予習", "row-New", "badge-", "cat_en"]),
    ("record_list.html", ["category", "session", "cat_en", "score_en", "correct", "Session"]),
]:
    fpath = os.path.join(templates, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    print(f"\n=== {fname} ===")
    for i, line in enumerate(lines, 1):
        if any(kw.lower() in line.lower() for kw in keywords):
            print(f"  {i}: {line.rstrip()}")