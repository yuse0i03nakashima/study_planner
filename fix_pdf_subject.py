import os

base = r"C:\Users\ynaka\study_planner"
pdf_path = os.path.join(base, "pdf_export.py")

with open(pdf_path, "r", encoding="utf-8") as f:
    content = f.read()

old = "def export_pdf(target_date_str, output_path, student_id=None, start_date=None):"
new = "def export_pdf(target_date_str, output_path, student_id=None, start_date=None, subject_filter=None):"

if old in content:
    content = content.replace(old, new)
    with open(pdf_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ pdf_export.py を修正しました")
else:
    print("❌ 対象箇所が見つかりません")