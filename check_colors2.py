import os

templates = r"C:\Users\ynaka\study_planner\templates"

for fname in ["preview.html", "record.html", "assignments_list.html"]:
    fpath = os.path.join(templates, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    print(f"\n=== {fname} ===")
    for i, line in enumerate(lines):
        if "page-title" in line and "{" in line:
            # CSS定義行：前後3行も表示
            start = max(0, i-1)
            end = min(len(lines), i+4)
            for j in range(start, end):
                print(f"  {j+1}: {lines[j].rstrip()}")
            print()