import os

base = r"C:\Users\ynaka\study_planner"

# excel_export.pyの578行目付近を確認
with open(os.path.join(base, "excel_export.py"), "r", encoding="utf-8") as f:
    elines = f.readlines()

print("=== excel_export.py: problem_text周辺 ===")
for i, line in enumerate(elines, 1):
    if "problem_text" in line or "_stot" in line or "_bar2" in line:
        print(f"  {i}: {line.rstrip()}")

# pdf_export.pyのproblem_number表示箇所を確認
with open(os.path.join(base, "pdf_export.py"), "r", encoding="utf-8") as f:
    plines = f.readlines()

print("\n=== pdf_export.py: problem_number/session関連 ===")
for i, line in enumerate(plines, 1):
    if any(kw in line for kw in [
        "problem_number", "session", "progress", "bar", "_stot", "_bar"
    ]):
        print(f"  {i}: {line.rstrip()}")

# excel_export.pyで実際にsession_totalを参照している箇所を確認
print("\n=== excel_export.py: 540〜600行目 ===")
for i in range(539, min(600, len(elines))):
    print(f"  {i+1}: {elines[i].rstrip()}")