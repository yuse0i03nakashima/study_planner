import sys
sys.path.insert(0, r"C:\Users\ynaka\study_planner")
from datetime import date, timedelta
from database import get_plan_v2, get_schedule
from collections import defaultdict

student_id = "S000"
start = date.today().isoformat()
end   = (date.today() + timedelta(days=7)).isoformat()

plan = get_plan_v2(student_id, start, end)
sched = get_schedule(student_id, start, end)

yosyu_items = sorted(
    [p for p in plan if p["category"] == "予習"],
    key=lambda x: (
        x.get("textbook_id") or 0,
        x.get("order_in_textbook") or x.get("problem_id", 0)
    )
)
print("ソート後:")
for p in yosyu_items:
    print(f"  {p['order_in_textbook']} {p['problem_number']}")

yosyu_by_textbook = defaultdict(list)
for item in yosyu_items:
    tb_id = item.get("textbook_id") or item.get("textbook", "unknown")
    yosyu_by_textbook[tb_id].append(item)

print(f"\nテキスト数: {len(yosyu_by_textbook)}")
for tb_id, items in yosyu_by_textbook.items():
    print(f"  textbook_id={tb_id}: {[p['problem_number'] for p in items]}")

interleaved = []
textbook_queues = list(yosyu_by_textbook.values())
indices = [0] * len(textbook_queues)
while True:
    added = False
    for i, queue in enumerate(textbook_queues):
        if indices[i] < len(queue):
            interleaved.append(queue[indices[i]])
            indices[i] += 1
            added = True
    if not added:
        break

print("\nインターリーブ後:")
for p in interleaved:
    print(f"  {p['order_in_textbook']} {p['problem_number']}")

# scheduleの確認
remaining = {d: m for d, m in sched.items() if m > 0}
dates_sorted = sorted(remaining.keys())
print(f"\n利用可能な日: {dates_sorted}")