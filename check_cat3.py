import os, subprocess

base = r"C:\Users\ynaka\study_planner"

for fname in ["excel_export.py", "pdf_export.py"]:
    fpath = os.path.join(base, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"\n=== {fname}: CAT_COLORS定義 ===")
    for i, line in enumerate(lines, 1):
        if "CAT_COLORS" in line or "C_BLUE" in line or "C_AMBER" in line:
            if i < 60:
                print(f"  {i}: {line.rstrip()}")

    print(f"\n=== {fname}: cat_raw・cat・cat_color ===")
    for i, line in enumerate(lines, 1):
        if any(kw in line for kw in ["cat_raw", "cat =", "cat_color"]):
            print(f"  {i}: {line.rstrip()}")