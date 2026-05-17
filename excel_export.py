import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from database import (get_connection, get_plan_v2, get_schedule,
                      get_schedule_subject, get_class_dates_in_range)
from datetime import date, timedelta
from collections import defaultdict

DOW_JA = ["月", "火", "水", "木", "金", "土", "日"]

CATEGORY_COLORS = {
    "予習":   "DDEEFF",
    "復習":   "DDFFDD",
    "定着":   "FFFADD",
    "再定着": "FFE5DD",
    "未割当": "F0F0F0",
}

MASTERY_MULTIPLIER = {1: 1.3, 2: 1.0, 3: 0.5}
CATEGORY_GROUP = {"復習": 0, "定着": 0, "再定着": 0, "予習": 1}
DISPLAY_ORDER = {"復習": 0, "定着": 1, "再定着": 2, "予習": 3}


def get_adjusted_minutes(item):
    mastery_level = int(item.get("mastery_int", 1) or 1)
    mastery_level = max(1, min(3, mastery_level))
    multiplier = MASTERY_MULTIPLIER.get(mastery_level, 1.0)
    return max(5, round(item["estimated_minutes"] * multiplier / 5) * 5)


def priority_score(item):
    group = CATEGORY_GROUP.get(item["category"], 1)
    mastery = int(item.get("mastery_int", 1) or 1)
    review_value = int(item.get("review_value", 3) or 3)
    importance = int(item.get("importance", 3) or 3)
    difficulty = int(item.get("difficulty", 3) or 3)
    return (group, mastery, -review_value, -importance, difficulty)


def assign_days_v2(plan, schedule, student_id, start_date_str, end_date_str):
    """
    割り当てロジック：
    予習：problem_id順 × テキスト間インターリーブ分散（授業日当日を含む）
    復習：前半60%・後半40%に分散して全問振り分け
    定着・再定着：残り時間に均等分散、代表問題優先、抑制中はスキップ
    """
    from database import get_suppressed_problems
    from collections import defaultdict

    remaining = {d: m for d, m in schedule.items() if m > 0}
    dates_sorted = sorted(remaining.keys())

    if not dates_sorted:
        for item in plan:
            item["assigned_date"] = None
        return [], plan

    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT DISTINCT p.subject FROM problems p "
        "JOIN assignments a ON p.problem_id = a.problem_id "
        "WHERE a.student_id=?", (student_id,))
    subjects = [r["subject"] for r in c.fetchall()]
    conn.close()

    subject_class_dates = {
        s: get_class_dates_in_range(
            student_id, s, start_date_str, end_date_str)
        for s in subjects
    }

    suppressed_ids = set(get_suppressed_problems(student_id))

    assigned = []
    unassigned = []
    n = len(dates_sorted)

    def try_assign(item, search_dates):
        """残り時間が最も多い日に割り当て"""
        minutes = get_adjusted_minutes(item)
        valid = [d for d in search_dates if remaining.get(d, 0) >= minutes]
        if not valid:
            return False
        d = max(valid, key=lambda x: remaining[x])
        remaining[d] -= minutes
        item["assigned_date"] = d
        assigned.append(item)
        return True

    def try_assign_balanced(item, search_dates, date_counts):
        """問題数が少ない日を優先して均等に割り当て"""
        minutes = get_adjusted_minutes(item)
        valid = [d for d in search_dates if remaining.get(d, 0) >= minutes]
        if not valid:
            return False
        # 問題数が少なく残り時間が多い日を優先
        d = min(valid, key=lambda x: (date_counts[x], -remaining[x]))
        remaining[d] -= minutes
        item["assigned_date"] = d
        date_counts[d] += 1
        assigned.append(item)
        return True

    # 日付ごとの問題数カウント（均等分散用）
    date_counts = defaultdict(int)

    # ─── 予習：problem_id順 × テキスト間インターリーブ ───
    yosyu_items = sorted(
        [p for p in plan if p["category"] == "予習"],
        key=lambda x: x.get("problem_id", 0))

    yosyu_by_textbook = defaultdict(list)
    for item in yosyu_items:
        tb_id = item.get("textbook_id") or item.get("textbook", "unknown")
        yosyu_by_textbook[tb_id].append(item)

    interleaved_yosyu = []
    textbook_queues = list(yosyu_by_textbook.values())
    indices = [0] * len(textbook_queues)
    while True:
        added = False
        for i, queue in enumerate(textbook_queues):
            if indices[i] < len(queue):
                interleaved_yosyu.append(queue[indices[i]])
                indices[i] += 1
                added = True
        if not added:
            break

    for item in interleaved_yosyu:
        subject = item["subject"]
        class_dates = subject_class_dates.get(subject, [])
        future = sorted([d for d in class_dates if d > start_date_str])
        if future:
            next_class = future[0]
            # 授業日当日も含める
            search = [d for d in dates_sorted if d <= next_class]
        else:
            search = list(dates_sorted)
        if not try_assign_balanced(item, search, date_counts):
            item["assigned_date"] = None
            unassigned.append(item)

    # ─── 復習：次回授業日の前日までに配置、前半60%・後半40% ──
    fukushu_items = sorted(
        [p for p in plan if p["category"] == "復習"],
        key=priority_score)

    front_end = max(1, int(n * 0.6))
    front_dates = dates_sorted[:front_end]
    back_dates = dates_sorted[front_end:] if len(dates_sorted) > front_end else dates_sorted

    total = len(fukushu_items)
    front_count = max(1, int(total * 0.6)) if total > 0 else 0

    for i, item in enumerate(fukushu_items):
        subject = item["subject"]
        class_dates = subject_class_dates.get(subject, [])
        future = sorted([d for d in class_dates if d > start_date_str])

        # 次回授業日の前日を計算
        if future:
            from datetime import date as _date, timedelta as _timedelta
            next_class = future[0]
            next_class_obj = _date.fromisoformat(next_class)
            prev_day = (next_class_obj - _timedelta(days=1)).isoformat()
            deadline_dates = [d for d in dates_sorted if d <= prev_day]
        else:
            deadline_dates = dates_sorted

        # 期限内で前半・後半に分散
        if i < front_count:
            search = [d for d in front_dates if d in deadline_dates] or deadline_dates
        else:
            search = [d for d in back_dates if d in deadline_dates] or deadline_dates

        if not try_assign_balanced(item, search, date_counts):
            # フォールバック：期限内全日付
            if not try_assign_balanced(item, deadline_dates, date_counts):
                # 最終フォールバック：全日付
                if not try_assign_balanced(item, dates_sorted, date_counts):
                    item["assigned_date"] = None
                    unassigned.append(item)

    # ─── 定着・再定着：均等分散、代表問題優先 ──────────
    teichaku_items = [p for p in plan
                      if p["category"] in ("定着", "再定着")]

    rep_items = sorted(
        [p for p in teichaku_items
         if int(p.get("review_value", 0) or 0) >= 4
         and p.get("problem_id") not in suppressed_ids],
        key=priority_score)

    normal_items = sorted(
        [p for p in teichaku_items
         if int(p.get("review_value", 0) or 0) < 4
         and p.get("problem_id") not in suppressed_ids],
        key=priority_score)

    for item in rep_items:
        if not try_assign_balanced(item, dates_sorted, date_counts):
            item["assigned_date"] = None
            unassigned.append(item)

    for item in normal_items:
        if not try_assign_balanced(item, dates_sorted, date_counts):
            item["assigned_date"] = None
            unassigned.append(item)

    return assigned, unassigned




def build_plan_data(student_id, start_date_str, target_date_str,
                    subject_filter=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT student_id, name, subjects, plan_mode FROM students "
        "WHERE student_id=?", (student_id,))
    student = c.fetchone()
    conn.close()
    if not student:
        return None

    all_subjects = [s.strip() for s in student["subjects"].split(",")]
    plan_mode = student["plan_mode"] if student["plan_mode"] else "all"
    all_plan = get_plan_v2(student_id, start_date_str, target_date_str)
    global_schedule = get_schedule(student_id, start_date_str, target_date_str)

    if subject_filter:
        subjects = [subject_filter]
        plan = [p for p in all_plan if p["subject"] == subject_filter]
    else:
        subjects = all_subjects
        plan = all_plan

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
            subject_schedules[subject] = global_schedule

    if use_subject_schedule:
        # 教科ごとに独立して割り当て
        all_assigned = []
        all_unassigned = []
        all_dates = set()
        for subject in subjects:
            subj_plan = [p for p in plan if p["subject"] == subject]
            subj_sched = subject_schedules[subject]
            a, u = assign_days_v2(
                subj_plan, dict(subj_sched),
                student_id, start_date_str, target_date_str)
            all_assigned.extend(a)
            all_unassigned.extend(u)
            all_dates.update(
                [d for d, m in subj_sched.items() if m > 0])
        dates_with_time = sorted(all_dates)
        assigned = all_assigned
        unassigned = all_unassigned
    else:
        # 全教科で共通スケジュールを使う
        assigned, unassigned = assign_days_v2(
            plan, global_schedule, student_id, start_date_str, target_date_str)
        dates_with_time = sorted(
            [d for d, m in global_schedule.items() if m > 0])

    rows = []
    for d in dates_with_time:
        d_obj = date.fromisoformat(d)
        dow = DOW_JA[d_obj.weekday()]
        date_label = (str(d_obj.month) + "/" + str(d_obj.day)
                      + "（" + dow + "）")
        day_items = [i for i in assigned if i["assigned_date"] == d]
        row = {"date": date_label, "date_str": d, "subjects": {}}
        for subject in subjects:
            si = sorted(
                [i for i in day_items if i["subject"] == subject],
                key=lambda x: DISPLAY_ORDER.get(x["category"], 9))
            row["subjects"][subject] = si
        rows.append(row)

    unassigned_by_subject = {}
    for subject in subjects:
        unassigned_by_subject[subject] = [
            i for i in unassigned if i["subject"] == subject]

    return {
        "student_name": student["name"],
        "student_id": student_id,
        "subjects": subjects,
        "plan_mode": plan_mode,
        "rows": rows,
        "unassigned": unassigned_by_subject,
        "schedule": global_schedule,
    }


def _make_problem_text(item):
    return ("【" + item["category"] + "】"
            + item["textbook"] + " " + item["problem_number"])


def _write_excel_sheet(ws, data, border):
    subjects = data["subjects"]
    rows = data["rows"]
    unassigned = data["unassigned"]

    header_cols = ["実施日"]
    for subject in subjects:
        header_cols.append(subject + "（問題）")
        header_cols.append(subject + "（指示）")
    header_cols.append("未割当")

    for col, h in enumerate(header_cols, start=1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="4472C4")
        cell.alignment = Alignment(horizontal="center")
        cell.border = border

    for row_idx, row in enumerate(rows, start=2):
        dc = ws.cell(row=row_idx, column=1, value=row["date"])
        dc.font = Font(bold=True)
        dc.fill = PatternFill("solid", fgColor="E8EEF8")
        dc.alignment = Alignment(horizontal="center", vertical="top")
        dc.border = border

        col_idx = 2
        for subject in subjects:
            si = sorted(
                row["subjects"].get(subject, []),
                key=lambda x: DISPLAY_ORDER.get(x["category"], 9))
            prob_lines = [_make_problem_text(i) for i in si]
            instr_lines = [i.get("instruction", "") or "" for i in si]
            prob_text = chr(10).join(prob_lines)
            instr_text = chr(10).join(instr_lines)
            color = "FFFFFF"
            if si:
                color = CATEGORY_COLORS.get(si[0]["category"], "FFFFFF")

            pc = ws.cell(row=row_idx, column=col_idx, value=prob_text)
            if si:
                pc.fill = PatternFill("solid", fgColor=color)
            pc.alignment = Alignment(
                horizontal="left", vertical="top", wrap_text=True)
            pc.border = border
            col_idx += 1

            ic = ws.cell(row=row_idx, column=col_idx, value=instr_text)
            if si:
                ic.fill = PatternFill("solid", fgColor=color)
            ic.alignment = Alignment(
                horizontal="left", vertical="top", wrap_text=True)
            ic.border = border
            col_idx += 1

        uc = ws.cell(row=row_idx, column=col_idx, value="")
        uc.border = border

    all_unassigned = []
    for subject in subjects:
        all_unassigned.extend(unassigned.get(subject, []))

    if all_unassigned:
        ur = len(rows) + 2
        lc = ws.cell(row=ur, column=1, value="未割当")
        lc.font = Font(bold=True)
        lc.fill = PatternFill("solid", fgColor="F0F0F0")
        lc.alignment = Alignment(horizontal="center", vertical="top")
        lc.border = border
        col_idx = 2
        for subject in subjects:
            si = unassigned.get(subject, [])
            prob_text = chr(10).join([_make_problem_text(i) for i in si])
            instr_text = chr(10).join(
                [i.get("instruction", "") or "" for i in si])
            pc = ws.cell(row=ur, column=col_idx, value=prob_text)
            pc.fill = PatternFill("solid", fgColor="F0F0F0")
            pc.alignment = Alignment(
                horizontal="left", vertical="top", wrap_text=True)
            pc.border = border
            col_idx += 1
            ic = ws.cell(row=ur, column=col_idx, value=instr_text)
            ic.fill = PatternFill("solid", fgColor="F0F0F0")
            ic.alignment = Alignment(
                horizontal="left", vertical="top", wrap_text=True)
            ic.border = border
            col_idx += 1

    ws.column_dimensions["A"].width = 14
    cl = 2
    for subject in subjects:
        ws.column_dimensions[
            openpyxl.utils.get_column_letter(cl)].width = 30
        cl += 1
        ws.column_dimensions[
            openpyxl.utils.get_column_letter(cl)].width = 35
        cl += 1
    for ri in range(2, len(rows) + 3):
        ws.row_dimensions[ri].height = 80


def export_excel(target_date_str, output_path, student_id=None,
                 start_date=None, subject_filter=None):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    conn = get_connection()
    c = conn.cursor()
    if student_id:
        c.execute(
            "SELECT student_id, name, subjects, plan_mode FROM students "
            "WHERE student_id=?", (student_id,))
    else:
        c.execute(
            "SELECT student_id, name, subjects, plan_mode FROM students "
            "ORDER BY student_id")
    students = c.fetchall()
    conn.close()

    thin = Side(style="thin")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    start_str = start_date if start_date else date.today().isoformat()

    for student in students:
        sid = student["student_id"]
        name = student["name"]
        plan_mode = student["plan_mode"] if student["plan_mode"] else "all"

        if subject_filter:
            subjects_to_process = [subject_filter]
        elif plan_mode == "per_subject":
            subjects_to_process = [
                s.strip() for s in student["subjects"].split(",")]
        else:
            subjects_to_process = None

        if subjects_to_process:
            for subject in subjects_to_process:
                data = build_plan_data(
                    sid, start_str, target_date_str, subject)
                if not data:
                    continue
                ws = wb.create_sheet(title=name + "_" + subject)
                _write_excel_sheet(ws, data, border)
        else:
            data = build_plan_data(sid, start_str, target_date_str)
            if not data:
                continue
            ws = wb.create_sheet(title=name)
            _write_excel_sheet(ws, data, border)

    wb.save(output_path)
    return output_path
