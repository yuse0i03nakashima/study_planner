import os

base = r"C:\Users\ynaka\study_planner"

# index.htmlのNew and Export箇所を確認
with open(os.path.join(base, "templates", "index.html"), "r", encoding="utf-8") as f:
    lines = f.readlines()
print("=== index.html: New/Preview関連 ===")
for i, line in enumerate(lines, 1):
    if any(kw in line for kw in ["New", "Preview", "Export", "plan", "preview"]):
        print(f"  {i}: {line.rstrip()}")

# excel_export.pyのcat_raw・CAT_COLORS周辺を確認
with open(os.path.join(base, "excel_export.py"), "r", encoding="utf-8") as f:
    lines = f.readlines()
print("\n=== excel_export.py: cat_raw・CAT_COLORS・cat_color ===")
for i, line in enumerate(lines, 1):
    if any(kw in line for kw in ["cat_raw", "cat =", "CAT_COLORS", "cat_color", "C_BLUE"]):
        if i < 50 or "cat_raw" in line or "cat_color" in line:
            print(f"  {i}: {line.rstrip()}")