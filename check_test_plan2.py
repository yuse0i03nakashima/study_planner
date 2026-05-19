import sys
sys.path.insert(0, r"C:\Users\ynaka\study_planner")
from datetime import date, timedelta
from database import get_schedule, get_class_dates_in_range
from excel_export import assign_days_v2

student_id = "S000"
start_date = date.today().isoformat()
end_date   = (date.today() + timedelta(days=14)).isoformat()

sched = get_schedule(student_id, start_date, end_date)
print("スケジュール（0以外）:")
for d, m in sched.items():
    if m > 0:
        print(f"  {d}: {m}分")
if all(m == 0 for m in sched.values()):
    print("  → 全て0分！勉強時間が反映されていません")

print(f"\n授業日:")
class_dates = get_class_dates_in_range(student_id, "テスト", start_date, end_date)
print(f"  {class_dates}")

# assign_days_v2を直接テスト
from database import get_plan_v2
plan = get_plan_v2(student_id, start_date, end_date)
print(f"\nplan件数: {len(plan)}")

assigned, unassigned = assign_days_v2(plan, sched, student_id, start_date, end_date)
print(f"assigned: {len(assigned)}")
print(f"unassigned: {len(unassigned)}")
if assigned:
    print(f"最初のassigned: {assigned[0].get('assigned_date')}, {assigned[0].get('problem_number')}")