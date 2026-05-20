import os, re

base = r"C:\Users\ynaka\study_planner"
excel_path = os.path.join(base, "excel_export.py")

with open(excel_path, "r", encoding="utf-8") as f:
    content = f.read()
lines = content.splitlines()

# estimated_minutesを含む行を全表示
print("=== estimated_minutes関連行 ===")
for i, line in enumerate(lines, 1):
    if "estimated_minutes" in line:
        print(f"  {i}: {line}")

# total_minutesを含む行を全表示
print("\n=== total_minutes関連行 ===")
for i, line in enumerate(lines, 1):
    if "total_minutes" in line:
        print(f"  {i}: {line}")

# planリストを構築しているdict箇所（50行前後のSELECT結果をdictにしている箇所）
print("\n=== dict/plan構築箇所 ===")
for i, line in enumerate(lines, 1):
    if any(kw in line for kw in [
        '"subject"', '"textbook"', '"problem_number"',
        '"estimated_minutes"', '"category"', '"mastery"'
    ]):
        print(f"  {i}: {line}")