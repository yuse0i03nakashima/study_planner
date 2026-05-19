import sys
sys.path.insert(0, r"C:\Users\ynaka\study_planner")
from database import get_auto_next_class_date

# 各生徒・教科の自動計算結果を確認
tests = [
    ("S001", "数学"),
    ("S001", "古典"),
    ("S001", "社会"),
    ("S002", "数学"),
    ("S003", "代数"),
    ("S003", "幾何"),
    ("S004", "数学"),
    ("S004", "英語"),
]

for student_id, subject in tests:
    result = get_auto_next_class_date(student_id, subject)
    print(f"{student_id} / {subject}: {result or '（授業曜日未設定）'}")