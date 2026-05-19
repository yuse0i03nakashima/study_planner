import sys
sys.path.insert(0, r"C:\Users\ynaka\study_planner")
from datetime import date, timedelta
from excel_export import build_plan_data

# 神田くんで試す
student_id = "S001"
start_date = date.today().isoformat()
end_date = (date.today() + timedelta(days=7)).isoformat()

result = build_plan_data(student_id, start_date, end_date, None)
if result:
    rows = result.get("rows", [])
    print(f"rows件数: {len(rows)}")
    if rows:
        print(f"最初のrow type: {type(rows[0])}")
        print(f"最初のrow keys: {rows[0].keys() if hasattr(rows[0], 'keys') else dir(rows[0])}")
        print(f"最初のrow内容: {dict(rows[0]) if hasattr(rows[0], 'keys') else rows[0]}")
else:
    print("build_plan_data returned None")