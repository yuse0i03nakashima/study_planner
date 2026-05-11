import sys
sys.path.insert(0, r"C:\Users\ynaka\study_planner")
from database import get_schedule, get_plan_v2
from excel_export import assign_days_v2, get_adjusted_minutes

student_id = "S003"
start_date = "2026-04-29"
end_date = "2026-05-06"

schedule = get_schedule(student_id, start_date, end_date)
print("=== スケジュール ===")
for d, m in sorted(schedule.items()):
    if m > 0:
        print(f"  {d}: {m}分")

plan = get_plan_v2(student_id, start_date, end_date)
print(f"\n=== 出題予定 {len(plan)}問 ===")
for p in plan[:10]:
    adj = get_adjusted_minutes(p)
    print(f"  [{p['category']}] {p['subject']} {p['problem_number']} "
          f"mastery_int={p.get('mastery_int')} "
          f"estimated={p['estimated_minutes']}分 adjusted={adj}分")

assigned, unassigned = assign_days_v2(
    plan, schedule, student_id, start_date, end_date)
print(f"\n=== 割り当て結果 ===")
print(f"割り当て済み: {len(assigned)}問 / 未割り当て: {len(unassigned)}問")
for d, m in sorted(schedule.items()):
    if m > 0:
        day_items = [i for i in assigned if i["assigned_date"] == d]
        print(f"  {d}: {len(day_items)}問")