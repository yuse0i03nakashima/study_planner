import sys
sys.path.insert(0, r"C:\Users\ynaka\study_planner")
from datetime import date, timedelta
from excel_export import build_plan_data

student_id = "S000"
start_date = date.today().isoformat()
end_date   = (date.today() + timedelta(days=14)).isoformat()

print(f"start={start_date}, end={end_date}")
result = build_plan_data(student_id, start_date, end_date, None)
if result:
    print(f"student_name : {result.get('student_name')}")
    print(f"plan_mode    : {result.get('plan_mode')}")
    print(f"subjects     : {result.get('subjects')}")
    rows = result.get("rows", [])
    print(f"rows件数     : {len(rows)}")
    for day in rows:
        print(f"  {day.get('date')} : {list(day.get('subjects',{}).keys())}")
    print(f"unassigned   : {result.get('unassigned')}")
else:
    print("build_plan_data returned None")

# database.pyのget_plan_v2も確認
from database import get_plan_v2, get_schedule
plan = get_plan_v2(student_id, start_date, end_date)
print(f"\nget_plan_v2件数: {len(plan)}")
if plan:
    print(f"最初のplan: {plan[0]}")
sched = get_schedule(student_id, start_date, end_date)
print(f"\nget_schedule: {sched}")