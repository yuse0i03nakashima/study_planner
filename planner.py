from database import (get_connection, get_plan_v2, get_schedule,
                      get_schedule_subject, get_class_dates_in_range)
from datetime import date
from collections import defaultdict

DOW_JA = ["月", "火", "水", "木", "金", "土", "日"]

MASTERY_MULTIPLIER = {1: 1.3, 2: 1.0, 3: 0.5}
CATEGORY_GROUP  = {"Recall": 0, "Drill": 0, "Reinforce": 0, "New": 1}
DISPLAY_ORDER   = {"Recall": 0, "Drill": 1, "Reinforce": 2, "New": 3}
# 1日の割当時間を最大この割合まで超過して問題を割り当てる（0.10 = 10%）
OVERFLOW_FACTOR = 0.10


def get_adjusted_minutes(item):
    mastery_level = int(item.get("mastery_int", 1) or 1)
    mastery_level = max(1, min(3, mastery_level))
    multiplier = MASTERY_MULTIPLIER.get(mastery_level, 1.0)
    return max(5, round(item["estimated_minutes"] * multiplier / 5) * 5)


def priority_score(item):
    group      = CATEGORY_GROUP.get(item["category"], 1)
    mastery    = int(item.get("mastery_int", 1) or 1)
    review_val = int(item.get("review_value", 3) or 3)
    importance = int(item.get("importance", 3) or 3)
    difficulty = int(item.get("difficulty", 3) or 3)
    return (group, mastery, -review_val, -importance, difficulty)


def assign_days_v2(plan, schedule, student_id, start_date_str, end_date_str):
    """
    割り当てロジック：
    予習：problem_id順 × テキスト間インターリーブ分散（授業日当日を含む）
    復習：前半60%・後半40%に分散して全問振り分け
    定着・再定着：残り時間に均等分散、代表問題優先、抑制中はスキップ
    """
    from database import get_suppressed_problems
    import math as _math

    remaining = {d: m for d, m in schedule.items() if m > 0}
    original_time = dict(remaining)  # 超過判定用：割り当て前の初期値を保持
    dates_sorted = sorted(remaining.keys())

    def can_fit(d, minutes):
        """残り時間 + OVERFLOW_FACTOR分の超過余裕で問題が収まるか判定"""
        r = remaining.get(d, 0)
        return r >= 0 and r + original_time.get(d, 0) * OVERFLOW_FACTOR >= minutes

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
        s: get_class_dates_in_range(student_id, s, start_date_str, end_date_str)
        for s in subjects
    }

    suppressed_ids = set(get_suppressed_problems(student_id))

    assigned   = []
    unassigned = []

    def try_assign_balanced(item, search_dates, date_counts):
        minutes = get_adjusted_minutes(item)
        valid = [d for d in search_dates if can_fit(d, minutes)]
        if not valid:
            return False
        d = min(valid, key=lambda x: (date_counts[x], -remaining[x]))
        remaining[d] -= minutes
        item["assigned_date"] = d
        date_counts[d] += 1
        assigned.append(item)
        return True

    date_counts = defaultdict(int)

    # ── 予習：problem_id順 × テキスト間インターリーブ ──────────────────
    yosyu_items = sorted(
        [p for p in plan if p["category"] == "New"],
        key=lambda x: (
            x.get("textbook_id") or 0,
            x.get("order_in_textbook") or x.get("problem_id", 0)
        ))
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

    # HP問題の事前展開
    expanded_yosyu = []
    for _it in interleaved_yosyu:
        _tot = _it.get("total_minutes")
        _est = int(_it.get("estimated_minutes") or 15)
        if not _tot or int(_tot) <= _est:
            _d = dict(_it)
            _d["session_index"]   = 1
            _d["session_total"]   = 1
            _d["progress_before"] = 0.0
            _d["progress_after"]  = 1.0
            expanded_yosyu.append(_d)
        else:
            _tot    = int(_tot)
            _n_sess = _math.ceil(_tot / _est)
            _prog   = 0.0
            for _si in range(_n_sess):
                _sess_m     = _est
                _prog_after = round(min(1.0, _prog + _sess_m / _tot), 4)
                _sd = dict(_it)
                _sd["estimated_minutes"] = _sess_m
                _sd["session_index"]     = _si + 1
                _sd["session_total"]     = _n_sess
                _sd["progress_before"]   = round(_prog, 4)
                _sd["progress_after"]    = _prog_after
                expanded_yosyu.append(_sd)
                _prog = _prog_after
    interleaved_yosyu = expanded_yosyu

    n_yosyu = len(interleaved_yosyu)
    yosyu_date_counts = {}

    for yi, item in enumerate(interleaved_yosyu):
        subject = item["subject"]
        class_dates = subject_class_dates.get(subject, [])
        future = sorted([d for d in class_dates if d > start_date_str])
        search = sorted([d for d in dates_sorted if d <= future[0]]) if future else list(dates_sorted)
        n_search = len(search)
        minutes  = item.get("estimated_minutes", 15)

        ratio = 0.40 + (yi / (n_yosyu - 1)) * 0.55 if n_yosyu > 1 else 0.70
        target_idx = max(0, min(int(n_search * ratio), n_search - 1))

        valid_after  = [d for d in search[target_idx:] if can_fit(d, minutes)]
        valid_before = [d for d in search[:target_idx]  if can_fit(d, minutes)]

        if valid_after:
            d = min(valid_after,  key=lambda x: (yosyu_date_counts.get(x, 0), x))
        elif valid_before:
            d = min(valid_before, key=lambda x: (yosyu_date_counts.get(x, 0), -search.index(x)))
        else:
            item["assigned_date"] = None
            unassigned.append(item)
            continue

        remaining[d] -= minutes
        item["assigned_date"] = d
        yosyu_date_counts[d] = yosyu_date_counts.get(d, 0) + 1
        assigned.append(item)

    # ── 復習：前半優先＋均等分散 ───────────────────────────────────────
    fukusyu_items = [p for p in plan if p["category"] == "Recall"]
    split_f = int(len(dates_sorted) * 0.60)
    fuku_first_half  = dates_sorted[:split_f]
    fuku_second_half = dates_sorted[split_f:]
    fuku_date_counts = {}

    for item in fukusyu_items:
        minutes = item.get("estimated_minutes", 15)
        first_valid  = [d for d in fuku_first_half  if can_fit(d, minutes)]
        second_valid = [d for d in fuku_second_half if can_fit(d, minutes)]

        if first_valid:
            d = min(first_valid,  key=lambda x: (fuku_date_counts.get(x, 0), x))
        elif second_valid:
            d = min(second_valid, key=lambda x: (fuku_date_counts.get(x, 0), x))
        else:
            item["assigned_date"] = None
            unassigned.append(item)
            continue

        remaining[d] -= minutes
        item["assigned_date"] = d
        fuku_date_counts[d] = fuku_date_counts.get(d, 0) + 1
        assigned.append(item)

    # ── 定着・再定着：均等分散、代表問題優先 ─────────────────────────
    teichaku_items = [p for p in plan if p["category"] in ("Drill", "Reinforce")]

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
                    subject_filter=None, section_ids=None):
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
    all_plan  = get_plan_v2(student_id, start_date_str, target_date_str)
    global_schedule = get_schedule(student_id, start_date_str, target_date_str)

    if subject_filter:
        subjects = [subject_filter]
        plan = [p for p in all_plan if p["subject"] == subject_filter]
    else:
        subjects = all_subjects
        plan = all_plan

    if section_ids:
        conn2 = get_connection()
        c2 = conn2.cursor()
        placeholders = ",".join("?" * len(section_ids))
        c2.execute(f"SELECT problem_id FROM problems WHERE section_id IN ({placeholders})",
                   section_ids)
        section_pids = {r["problem_id"] for r in c2.fetchall()}
        conn2.close()
        plan = [p for p in plan if p.get("problem_id") in section_pids]

    subject_schedules = {}
    use_subject_schedule = False
    for subject in subjects:
        subj_sched = get_schedule_subject(
            student_id, subject, start_date_str, target_date_str)
        if subj_sched is not None and any(m > 0 for m in subj_sched.values()):
            subject_schedules[subject] = subj_sched
            use_subject_schedule = True
        else:
            subject_schedules[subject] = global_schedule

    if use_subject_schedule:
        all_assigned   = []
        all_unassigned = []
        all_dates      = set()
        for subject in subjects:
            subj_plan  = [p for p in plan if p["subject"] == subject]
            subj_sched = subject_schedules[subject]
            a, u = assign_days_v2(
                subj_plan, dict(subj_sched),
                student_id, start_date_str, target_date_str)
            all_assigned.extend(a)
            all_unassigned.extend(u)
            all_dates.update([d for d, m in subj_sched.items() if m > 0])
        dates_with_time = sorted(all_dates)
        assigned   = all_assigned
        unassigned = all_unassigned
    else:
        assigned, unassigned = assign_days_v2(
            plan, global_schedule, student_id, start_date_str, target_date_str)
        dates_with_time = sorted([d for d, m in global_schedule.items() if m > 0])

    rows = []
    for d in dates_with_time:
        d_obj = date.fromisoformat(d)
        dow = DOW_JA[d_obj.weekday()]
        date_label = str(d_obj.month) + "/" + str(d_obj.day) + "（" + dow + "）"
        day_items  = [i for i in assigned if i["assigned_date"] == d]
        row = {"date": date_label, "date_str": d, "subjects": {}}
        for subject in subjects:
            si = sorted(
                [i for i in day_items if i["subject"] == subject],
                key=lambda x: DISPLAY_ORDER.get(x["category"], 9))
            row["subjects"][subject] = si
        rows.append(row)

    unassigned_by_subject = {
        subject: [i for i in unassigned if i["subject"] == subject]
        for subject in subjects
    }

    return {
        "student_name": student["name"],
        "student_id":   student_id,
        "subjects":     subjects,
        "plan_mode":    plan_mode,
        "rows":         rows,
        "unassigned":   unassigned_by_subject,
        "schedule":     global_schedule,
    }
