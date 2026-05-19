import sys
sys.path.insert(0, r"C:\Users\ynaka\study_planner")
from datetime import date, timedelta
from database import get_plan_v2

student_id = "S000"
start = date.today().isoformat()
end   = (date.today() + timedelta(days=7)).isoformat()

plan = get_plan_v2(student_id, start, end)
yosyu = [p for p in plan if p["category"] == "予習"]
print(f"予習問題数: {len(yosyu)}")
for p in yosyu:
    print(f"  order={p.get('order_in_textbook')}, "
          f"problem_id={p.get('problem_id')}, "
          f"textbook_id={p.get('textbook_id')}, "
          f"number={p.get('problem_number')}")

print("\nソート後:")
sorted_yosyu = sorted(
    yosyu,
    key=lambda x: (
        x.get("textbook_id") or 0,
        x.get("order_in_textbook") or x.get("problem_id", 0)
    )
)
for p in sorted_yosyu:
    print(f"  order={p.get('order_in_textbook')}, "
          f"number={p.get('problem_number')}")