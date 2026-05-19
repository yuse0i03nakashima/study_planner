import sys
sys.path.insert(0, r"C:\Users\ynaka\study_planner")
from datetime import date, timedelta
from database import get_schedule_subject

student_id = "S000"
subject    = "テスト"
start_date = date.today().isoformat()
end_date   = (date.today() + timedelta(days=14)).isoformat()

result = get_schedule_subject(student_id, subject, start_date, end_date)
print(f"get_schedule_subject の戻り値: {result}")
print(f"type: {type(result)}")