import os

base = r"C:\Users\ynaka\study_planner"

# preview.htmlの問題番号表示周辺を確認
prev_path = os.path.join(base, "templates", "preview.html")
with open(prev_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"preview.html: {len(lines)}行")
print("\n=== problem_number / session関連行 ===")
for i, line in enumerate(lines, 1):
    if any(kw in line for kw in [
        "problem_number", "session", "progress", "bar", "pct"
    ]):
        print(f"  {i}: {line.rstrip()}")

# excel_export.pyのプログレスバー箇所確認
excel_path = os.path.join(base, "excel_export.py")
with open(excel_path, "r", encoding="utf-8") as f:
    elines = f.readlines()

print("\n=== excel_export.py: session/progress/bar関連行 ===")
for i, line in enumerate(elines, 1):
    if any(kw in line for kw in [
        "_stot", "_sidx", "_bar2", "_pct2", "session_total",
        "progress_after", "_sess"
    ]):
        print(f"  {i}: {line.rstrip()}")

# build_plan_dataのdict変換箇所を確認（total_minutesが含まれているか）
print("\n=== excel_export.py: 270〜320行目付近（planデータ構築） ===")
for i, line in enumerate(elines):
    if '"total_minutes"' in line or "'total_minutes'" in line:
        print(f"  {i+1}: {line.rstrip()}")

# database.pyのdict変換でtotal_minutesが含まれているか確認
db_path = os.path.join(base, "database.py")
with open(db_path, "r", encoding="utf-8") as f:
    dblines = f.readlines()

print("\n=== database.py: total_minutes関連行 ===")
for i, line in enumerate(dblines, 1):
    if "total_minutes" in line:
        print(f"  {i}: {line.rstrip()}")