import os, re

excel_path = r"C:\Users\ynaka\study_planner\excel_export.py"

with open(excel_path, "r", encoding="utf-8") as f:
    excel = f.read()

old = """\
    # 教科別スケジュールがあるか確認
    subject_schedules = {}
    use_subject_schedule = False
    for subject in subjects:
        subj_sched = get_schedule_subject(
            student_id, subject, start_date_str, target_date_str)
        if subj_sched is not None:
            subject_schedules[subject] = subj_sched
            use_subject_schedule = True
        else:
            subject_schedules[subject] = global_schedule"""

new = """\
    # 教科別スケジュールがあるか確認
    # 全て0分の場合はNoneとみなしてglobal_scheduleを使用
    subject_schedules = {}
    use_subject_schedule = False
    for subject in subjects:
        subj_sched = get_schedule_subject(
            student_id, subject, start_date_str, target_date_str)
        if subj_sched is not None and any(m > 0 for m in subj_sched.values()):
            subject_schedules[subject] = subj_sched
            use_subject_schedule = True
        else:
            subject_schedules[subject] = global_schedule"""

if old in excel:
    excel = excel.replace(old, new)
    with open(excel_path, "w", encoding="utf-8") as f:
        f.write(excel)
    print("✅ 修正しました")
else:
    print("❌ 対象箇所が見つかりません")