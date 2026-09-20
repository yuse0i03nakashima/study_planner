from database import (get_connection, get_plan_v2, get_schedule,
                      get_schedule_subject, get_class_dates_in_range)
from datetime import date, timedelta
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


def water_fill(caps, weights, need):
    """
    日別キャパ(caps)と重み(weights)から、合計need分の日別割当量を求める（水充填）。
    割当は「重み×キャパ」に比例し、各日のキャパを超えない。
    キャパに達した日の超過分は残りの日へ再配分されるため、
    需要が少ない週は重みの高い日（後半）に寄り、需要が多い週は
    前半の大キャパ日へ自然に溢れていく。
    """
    n = len(caps)
    alloc = [0.0] * n
    if n == 0 or need <= 0:
        return alloc
    total_cap = float(sum(caps))
    if total_cap <= 0:
        return alloc
    if need >= total_cap:
        return [float(c) for c in caps]
    active = [i for i in range(n) if caps[i] > 0]
    fixed_sum = 0.0
    while active:
        wsum = sum(weights[i] * caps[i] for i in active)
        if wsum <= 0:
            break
        lam = (need - fixed_sum) / wsum
        clipped = [i for i in active if lam * weights[i] * caps[i] >= caps[i]]
        if not clipped:
            for i in active:
                alloc[i] = lam * weights[i] * caps[i]
            break
        for i in clipped:
            alloc[i] = float(caps[i])
            fixed_sum += caps[i]
        clipped_set = set(clipped)
        active = [i for i in active if i not in clipped_set]
    return alloc


# 空き日と判定する下限問題数（この数未満の日を coverage_pass が埋める）
MIN_DAY_ITEMS = 1


def _cov_charged(item):
    return item.get("_charged_minutes") or item.get("estimated_minutes", 15) or 15


def _cov_fit(ctx, d, minutes):
    """context（教科別または全体スケジュール）のキャパで d に minutes が収まるか"""
    r = ctx["remaining"].get(d)
    if r is None:
        return False
    return r >= 0 and r + ctx["original_time"].get(d, 0) * OVERFLOW_FACTOR >= minutes


def _cov_can_move(ctx, item, target):
    """割当時に付与した _cov 制約の範囲内で target へ移動できるか"""
    cov = item.get("_cov") or ("any", None)
    kind = cov[0]
    if kind == "until":
        return target <= cov[1]
    if kind == "seq":
        _, limit, group, idx = cov
        if target > limit:
            return False
        # 同じ締切グループ内で番号順（キュー順）の単調性を保てる範囲のみ
        for other in ctx["assigned"]:
            oc = other.get("_cov")
            if not oc or oc[0] != "seq" or oc[2] != group or other is item:
                continue
            od = other.get("assigned_date")
            if not od:
                continue
            if oc[3] < idx and od > target:
                return False
            if oc[3] > idx and od < target:
                return False
        return True
    return True  # "any"


def coverage_pass(contexts, all_dates):
    """
    キャパがあるのに割当が MIN_DAY_ITEMS 問未満の日（空き日）へ、
    制約（番号順・授業前日・締切・キャパ）を守れる問題を1問移す。

    1. 直接移動：2問以上ある日から1問移す（新たな空き日を作らない）
    2. カスケード左詰め：直接移動できない場合、空き日より後ろの問題を
       番号順を保ったまま1日ずつ左に詰め、どこかの複数問題日を1問減らす

    contexts: assign_days_v2 が返す context のリスト
              （全体スケジュール時は1件、教科別スケジュール時は教科ごと）
    all_dates: キャパのある日のソート済みリスト
    """
    loads = {d: [] for d in all_dates}
    for ctx in contexts:
        for it in ctx["assigned"]:
            d = it.get("assigned_date")
            if d in loads:
                loads[d].append((ctx, it))

    pref_order = {"any": 0, "until": 1, "seq": 2}

    def move(ctx, it, src, target, minutes):
        ctx["remaining"][src] = ctx["remaining"].get(src, 0) + minutes
        ctx["remaining"][target] = ctx["remaining"].get(target, 0) - minutes
        it["assigned_date"] = target
        loads[src] = [p for p in loads[src] if p[1] is not it]
        loads[target].append((ctx, it))

    def try_direct(target):
        cands = []
        for src, lst in loads.items():
            if src == target or len(lst) <= MIN_DAY_ITEMS:
                continue
            for ctx, it in lst:
                cov = it.get("_cov") or ("any", None)
                cands.append((pref_order.get(cov[0], 0), -len(lst), src, ctx, it))
        cands.sort(key=lambda x: (x[0], x[1], x[2]))
        for _, _, src, ctx, it in cands:
            minutes = _cov_charged(it)
            if _cov_fit(ctx, target, minutes) and _cov_can_move(ctx, it, target):
                move(ctx, it, src, target, minutes)
                return True
        return False

    def try_cascade(target):
        # 空き日より後ろに複数問題日がなければ、左詰めしても空き日は減らない
        if not any(len(loads[d]) > MIN_DAY_ITEMS for d in all_dates if d > target):
            return False
        total_items = sum(len(v) for v in loads.values())
        current = target
        for _ in range(total_items + 1):
            best = None
            for src in all_dates:
                if src <= current or not loads[src]:
                    continue
                for ctx, it in loads[src]:
                    minutes = _cov_charged(it)
                    if _cov_fit(ctx, current, minutes) and _cov_can_move(ctx, it, current):
                        best = (src, ctx, it, minutes)
                        break
                if best:
                    break
            if not best:
                return False
            src, ctx, it, minutes = best
            move(ctx, it, src, current, minutes)
            if loads[src]:
                return True   # 移動元にまだ問題が残っている＝空き日が1つ減った
            current = src     # 移動元が空いたので、続けて右隣から詰める
        return False

    guard = len(all_dates) * 4 + 10
    while guard > 0:
        guard -= 1
        empty = [d for d in all_dates if len(loads[d]) < MIN_DAY_ITEMS]
        progressed = False
        for d in empty:
            if try_direct(d) or try_cascade(d):
                progressed = True
                break  # 空き日リストを取り直す
        if not progressed:
            break


def assign_days_v2(plan, schedule, student_id, start_date_str, end_date_str):
    """
    割り当てロジック（2026-09 再設計）：
    復習：scheduled_dateが対象教科の授業日ならその前日まで、
          そうでなければscheduled_dateまでに、件数バランスをとって前半寄りに配置（仕様保証）
    予習：締切(scheduled_date)ごとにまとめ、番号順（テキスト間インターリーブ）を保ったまま
          「後半寄り重み×曜日別キャパ」の水充填クォータで日別配分。
          後半キャパに収まらない分は番号の小さい側から前半の残キャパへ流れ、
          全体を通した番号順と曜日別キャパ比例が保たれる
    定着・再定着：残り時間に均等分散、代表問題優先、抑制中はスキップ
                  （割当が1問もない日を優先して埋める）
    戻り値：(assigned, unassigned, context)
    context は coverage_pass（空き日解消）用の状態
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
        return [], plan, {"assigned": [], "remaining": {}, "original_time": {}}

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
        # 全カテゴリ通して1問もない日を最優先に埋める（空き日の解消）
        d = min(valid, key=lambda x: (1 if day_item_counts[x] > 0 else 0,
                                      date_counts[x], -remaining[x]))
        remaining[d] -= minutes
        item["assigned_date"] = d
        item["_cov"] = ("any", None)
        item["_charged_minutes"] = minutes
        date_counts[d] += 1
        day_item_counts[d] += 1
        assigned.append(item)
        return True

    date_counts = defaultdict(int)
    day_item_counts = defaultdict(int)  # 全カテゴリ合算の日別問題数

    def day_before(date_str):
        return (date.fromisoformat(date_str) - timedelta(days=1)).isoformat()

    # ── 復習：授業前日まで（授業日出題の場合）／締切までに前半寄り配置 ──
    fukusyu_items = [p for p in plan if p["category"] == "Recall"]
    fuku_date_counts = {}

    for item in fukusyu_items:
        minutes = item.get("estimated_minutes", 15) or 15
        sd = item.get("scheduled_date") or end_date_str
        if sd > end_date_str or sd < dates_sorted[0]:
            # 期間より先／期限超過（過去日）の課題は週全体を窓にする
            sd = end_date_str
        class_dates = subject_class_dates.get(item["subject"], [])
        # 出題予定日が対象教科の授業日なら「授業前日まで」に済ませる（仕様保証）
        limit = day_before(sd) if sd in class_dates else sd
        candidate_windows = (
            [d for d in dates_sorted if d <= limit],
            [d for d in dates_sorted if d <= sd],
            dates_sorted,
        )
        placed = False
        for cand in candidate_windows:
            valid = [d for d in cand if can_fit(d, minutes)]
            if valid:
                d = min(valid, key=lambda x: (fuku_date_counts.get(x, 0), x))
                remaining[d] -= minutes
                item["assigned_date"] = d
                item["_cov"] = ("until", limit)   # 移動は limit までに制限
                item["_charged_minutes"] = minutes
                fuku_date_counts[d] = fuku_date_counts.get(d, 0) + 1
                day_item_counts[d] += 1
                assigned.append(item)
                placed = True
                break
        if not placed:
            item["assigned_date"] = None
            unassigned.append(item)

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

    # ── 予習：締切グループごとに番号順を保って水充填配分 ────────────────
    EPS = 1e-6
    yosyu_groups = defaultdict(list)
    for item in interleaved_yosyu:
        sd = item.get("scheduled_date") or end_date_str
        if sd > end_date_str or sd < dates_sorted[0]:
            # 期間より先／期限超過（過去日）の課題は週全体を窓にする
            sd = end_date_str
        yosyu_groups[sd].append(item)

    yosyu_leftovers = []
    for limit in sorted(yosyu_groups.keys()):
        queue = yosyu_groups[limit]
        window = [d for d in dates_sorted if d <= limit] or list(dates_sorted)
        n = len(window)
        caps = [max(0, remaining[d]) for d in window]
        need = sum(item.get("estimated_minutes", 15) or 15 for item in queue)

        # 後半寄りの重み（先頭0.35→末尾1.0）。需要が窓の後半キャパを超える週は
        # 水充填により前半の大キャパ日へ番号の小さい側から自然に溢れる
        weights = [0.35 + 0.65 * (i / (n - 1)) if n > 1 else 1.0 for i in range(n)]
        alloc = water_fill(caps, weights, need)

        cum_targets = []
        acc = 0.0
        for a in alloc:
            acc += a
            cum_targets.append(acc)

        # 累積ターゲットに沿って、日ポインタを単調に進めながら番号順のまま割当
        di = 0
        assigned_cum = 0.0
        for qi, item in enumerate(queue):
            minutes = item.get("estimated_minutes", 15) or 15
            while di < n - 1 and (assigned_cum + minutes / 2.0 > cum_targets[di] + EPS
                                  or not can_fit(window[di], minutes)):
                di += 1
            d = window[di]
            if can_fit(d, minutes):
                remaining[d] -= minutes
                item["assigned_date"] = d
                # 移動は締切内かつグループ内の前後の問題の間のみ（番号順を保持）
                item["_cov"] = ("seq", limit, limit, qi)
                item["_charged_minutes"] = minutes
                day_item_counts[d] += 1
                assigned.append(item)
                assigned_cum += minutes
            else:
                yosyu_leftovers.append((item, limit))

    # クォータの端数等で収まらなかった予習は、締切内→締切超過の順で
    # 残キャパの大きい日に割り当てる（未割当にするより完了を優先）
    for item, limit in yosyu_leftovers:
        minutes = item.get("estimated_minutes", 15) or 15
        in_window  = [d for d in dates_sorted if d <= limit and can_fit(d, minutes)]
        out_window = [d for d in dates_sorted if d > limit and can_fit(d, minutes)]
        pool = in_window or out_window
        if pool:
            d = max(pool, key=lambda x: remaining[x])
            remaining[d] -= minutes
            item["assigned_date"] = d
            item["_cov"] = ("until", limit)  # 順序保証は既に外れているため締切のみ制約
            item["_charged_minutes"] = minutes
            day_item_counts[d] += 1
            assigned.append(item)
        else:
            item["assigned_date"] = None
            unassigned.append(item)

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

    context = {"assigned": assigned, "remaining": remaining,
               "original_time": original_time}
    return assigned, unassigned, context


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
        contexts       = []
        for subject in subjects:
            subj_plan  = [p for p in plan if p["subject"] == subject]
            subj_sched = subject_schedules[subject]
            a, u, ctx = assign_days_v2(
                subj_plan, dict(subj_sched),
                student_id, start_date_str, target_date_str)
            all_assigned.extend(a)
            all_unassigned.extend(u)
            contexts.append(ctx)
            all_dates.update([d for d, m in subj_sched.items() if m > 0])
        dates_with_time = sorted(all_dates)
        assigned   = all_assigned
        unassigned = all_unassigned
    else:
        assigned, unassigned, ctx = assign_days_v2(
            plan, global_schedule, student_id, start_date_str, target_date_str)
        contexts = [ctx]
        dates_with_time = sorted([d for d, m in global_schedule.items() if m > 0])

    # 空き日（キャパはあるのに割当0問の日）を、制約の範囲で解消する
    coverage_pass(contexts, dates_with_time)

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

    # キャパがあるのに1問も割り当てられなかった日（課題不足の週で発生。
    # 前倒しは行わず、問題登録の見直し判断のために明示して返す）
    empty_days = [r["date_str"] for r in rows
                  if not any(r["subjects"].values())]

    return {
        "student_name": student["name"],
        "student_id":   student_id,
        "subjects":     subjects,
        "plan_mode":    plan_mode,
        "rows":         rows,
        "unassigned":   unassigned_by_subject,
        "schedule":     global_schedule,
        "empty_days":   empty_days,
    }


def plan_days_snapshot(data):
    """
    build_plan_data の結果から出力時点の日別配置スナップショットを作る。
    plan_history.plan_data に保存し、get_plan_days(source="snapshot") が参照する。
    計画は毎回再計算されるため、生徒に渡した計画表とDBの再計算結果のずれを
    このスナップショットで吸収する。
    """
    if not data:
        return None
    days = []
    for row in data["rows"]:
        for subj, items in row["subjects"].items():
            for it in items:
                days.append({
                    "date":              row["date_str"],
                    "subject":           subj,
                    "problem_id":        it.get("problem_id"),
                    "problem_number":    it.get("problem_number"),
                    "textbook":          it.get("textbook"),
                    "textbook_id":       it.get("textbook_id"),
                    "category":          it.get("category"),
                    "estimated_minutes": it.get("estimated_minutes"),
                    "session_index":     it.get("session_index", 1),
                    "session_total":     it.get("session_total", 1),
                })
    unassigned = []
    for subj, items in data["unassigned"].items():
        for it in items:
            unassigned.append({
                "subject":        subj,
                "problem_id":     it.get("problem_id"),
                "problem_number": it.get("problem_number"),
                "textbook":       it.get("textbook"),
                "category":       it.get("category"),
            })
    return {"format": "days_v1", "days": days, "unassigned": unassigned,
            "empty_days": data.get("empty_days", [])}
