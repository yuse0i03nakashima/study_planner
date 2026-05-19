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

    def try_assign(item, search_dates, prefer_earliest=False):
        """残り時間がある日に割り当て。prefer_earliest=Trueなら最も早い日優先"""
        minutes = get_adjusted_minutes(item)
        valid = [d for d in search_dates if remaining.get(d, 0) >= minutes]
        if not valid:
            return False
        if prefer_earliest:
            d = min(valid)
        else:
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

    # 予習：No.順を維持しながら後半寄りに分散
    # 戦略：予習問題をN個とし、i番目の問題は全体の後半60%に収まるよう
    #        目標日インデックスを設定。その日付以降で空きがあれば割り当て、
    #        なければ前に戻って探す（順番は絶対に崩さない）
    n_dates = len(dates_sorted)
    n_yosyu = len(interleaved_yosyu)

    yosyu_date_counts = {}
    for yi, item in enumerate(interleaved_yosyu):
        subject = item["subject"]
        class_dates = subject_class_dates.get(subject, [])
        future = sorted([d for d in class_dates if d > start_date_str])
        if future:
            next_class = future[0]
            search = sorted([d for d in dates_sorted if d <= next_class])
        else:
            search = list(dates_sorted)

        n_search = len(search)
        minutes = item.get("estimated_minutes", 15)

        # i番目の問題の目標位置：後半60%の範囲内でi/N比率で分散
        # 例：5問なら 0.40, 0.50, 0.60, 0.75, 0.90 のインデックス
        if n_yosyu > 1:
            ratio = 0.40 + (yi / (n_yosyu - 1)) * 0.55
        else:
            ratio = 0.70
        target_idx = int(n_search * ratio)
        target_idx = max(0, min(target_idx, n_search - 1))

        # 目標日以降で空きがある日を探す（後半優先）
        valid_after = [d for d in search[target_idx:]
                       if remaining.get(d, 0) >= minutes]
        valid_before = [d for d in search[:target_idx]
                        if remaining.get(d, 0) >= minutes]

        if valid_after:
            # 目標以降で最も問題数が少ない日（同数なら早い日）
            d = min(valid_after,
                    key=lambda x: (yosyu_date_counts.get(x, 0), x))
        elif valid_before:
            # 前に戻って最も問題数が少ない日（同数なら遅い日＝後半寄り）
            d = min(valid_before,
                    key=lambda x: (yosyu_date_counts.get(x, 0), -search.index(x)))
        else:
            item["assigned_date"] = None
            unassigned.append(item)
            continue

        remaining[d] -= minutes
        item["assigned_date"] = d
        yosyu_date_counts[d] = yosyu_date_counts.get(d, 0) + 1
        assigned.append(item)

        # ─── 復習：前半優先＋均等分散 ───────────────────────
    # 前60%の日を優先し、満杯なら後半にスピルオーバー
    fukusyu_items = [p for p in plan if p["category"] == "復習"]

    # 前半60%・後半40%に分割
    n_dates_f = len(dates_sorted)
    split_f = int(n_dates_f * 0.60)
    fuku_first_half  = dates_sorted[:split_f]   # 前半（復習優先）
    fuku_second_half = dates_sorted[split_f:]   # 後半（スピルオーバー）

    fuku_date_counts = {}
    for item in fukusyu_items:
        minutes = item.get("estimated_minutes", 15)

        # 前半優先で有効な日
        first_valid  = [d for d in fuku_first_half
                        if remaining.get(d, 0) >= minutes]
        second_valid = [d for d in fuku_second_half
                        if remaining.get(d, 0) >= minutes]

        if first_valid:
            # 前半：問題数が少ない日優先（同数なら早い日）
            d = min(first_valid,
                    key=lambda x: (fuku_date_counts.get(x, 0), x))
        elif second_valid:
            # 後半にスピルオーバー
            d = min(second_valid,
                    key=lambda x: (fuku_date_counts.get(x, 0), x))
        else:
            item["assigned_date"] = None
            unassigned.append(item)
            continue

        remaining[d] -= minutes
        item["assigned_date"] = d
        fuku_date_counts[d] = fuku_date_counts.get(d, 0) + 1
        assigned.append(item)

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


def _write_excel_sheet(ws, subjects, rows, unassigned,
                       student_name, start_date, end_date):
    """全教科を1シートに出力するダークテーマExcel"""
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from datetime import date as date_cls

    # ── カラーパレット ──
    BG_MAIN     = "0C0D11"
    BG_SURFACE  = "13151E"
    BG_SURFACE2 = "1B1E2B"
    BG_SURFACE3 = "222536"
    BG_DAY_A    = "13151E"   # 日付ブロックA（濃）
    BG_DAY_B    = "1B1E2B"   # 日付ブロックB（やや薄）
    C_TEXT      = "DDE1EC"
    C_MUTED     = "9AA3B8"
    C_DIM       = "555D7A"
    C_BLUE      = "5B8FF9"
    C_GREEN     = "3ECF8E"
    C_AMBER     = "F5A623"
    C_ROSE      = "F06292"
    C_RED       = "EF4444"
    C_BORDER    = "252838"
    C_BORDER_L  = "2F3347"

    CAT_COLORS = {
        "予習": C_BLUE, "復習": C_GREEN,
        "定着": C_AMBER, "再定着": C_ROSE,
    }
    MASTERY_COLORS = {1: C_ROSE, 2: C_AMBER, 3: C_GREEN}
    DOW_JA = ["月", "火", "水", "木", "金", "土", "日"]

    def fill(c): return PatternFill("solid", fgColor=c)
    def font(c, bold=False, size=10, mono=False):
        name = "Consolas" if mono else "Noto Serif JP"
        return Font(color=c, bold=bold, size=size, name=name)
    def aln(h="left", v="center", wrap=False):
        return Alignment(horizontal=h, vertical=v, wrap_text=wrap)
    def bdr(c=C_BORDER):
        s = Side(style="thin", color=c)
        return Border(left=s, right=s, top=s, bottom=s)

    ws.sheet_view.showGridLines = False

    # ── 列定義 ──
    # Date / Day / Subject / Category / Textbook / Problem / Mastery / Min / Instruction
    COLS = [
        ("Date",        10),
        ("Day",          4),
        ("Subject",     10),
        ("Category",     9),
        ("Textbook",    20),
        ("Problem",     34),
        ("Mastery",      8),
        ("Min",          5),
        ("Instruction", 44),
    ]
    N_COLS = len(COLS)

    # ── 全セルにデフォルト背景色を設定 ──
    # I列より右（J〜Z列）にもダークテーマを適用
    for r in range(1, 501):
        for c in range(1, 40):  # A〜AN列まで
            ws.cell(row=r, column=c).fill = fill(BG_MAIN)

    # ── 列幅 ──
    for i, (_, w) in enumerate(COLS, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ── タイトル行 ──
    ws.merge_cells(f"A1:{get_column_letter(N_COLS)}1")
    c1 = ws["A1"]
    c1.value = f"[SP]  {student_name}   {start_date} → {end_date}"
    c1.fill = fill("0F1119")   # タイトル専用（最も濃い）
    c1.font = Font(color=C_BLUE, bold=True, size=12, name="Consolas")
    c1.alignment = aln("left", "center")
    ws.row_dimensions[1].height = 30

    # ── ヘッダ行 ──
    BG_HEADER_ROW = "222536"   # ヘッダ専用色（BG_SURFACE3相当）
    for i, (h, _) in enumerate(COLS, 1):
        cell = ws.cell(row=2, column=i)
        cell.value = h.upper()
        cell.fill = fill(BG_HEADER_ROW)
        cell.font = Font(color=C_MUTED, bold=False, size=8, name="Consolas")
        cell.alignment = aln("center", "center")
        cell.border = bdr(C_BORDER_L)
    ws.row_dimensions[2].height = 20

    ws.freeze_panes = "A3"

    # ── データ行 ──
    cur = 3
    day_toggle = False  # 日付ブロックの交互色制御

    for day_row in rows:
        date_str_raw = day_row.get("date_str", "")
        date_label   = day_row.get("date", "")
        subjects_dict = day_row.get("subjects", {})

        # この日の全問題を収集（教科順）
        day_items = []
        for subj in subjects:
            for item in subjects_dict.get(subj, []):
                day_items.append((subj, item))

        if not day_items:
            continue

        # 日付ブロックの背景色を交互に
        day_bg = BG_DAY_A if day_toggle else BG_DAY_B
        day_toggle = not day_toggle

        try:
            d_obj = date_cls.fromisoformat(date_str_raw)
            dow = DOW_JA[d_obj.weekday()]
            date_disp = f"{d_obj.month}/{d_obj.day}"
            is_weekend = d_obj.weekday() >= 5
        except Exception:
            dow = ""
            date_disp = date_label
            is_weekend = False

        # 曜日色
        dow_color = C_ROSE if is_weekend else C_MUTED

        for row_i, (subj, item) in enumerate(day_items):
            cat = item.get("category", "")
            cat_color = CAT_COLORS.get(cat, C_DIM)
            mastery_int = item.get("mastery_int", 1)
            mastery_color = MASTERY_COLORS.get(mastery_int, C_TEXT)

            vals = [
                date_disp if row_i == 0 else "",
                dow       if row_i == 0 else "",
                subj,
                cat,
                item.get("textbook", ""),
                item.get("problem_number", ""),
                item.get("mastery", "★"),
                item.get("estimated_minutes", ""),
                item.get("instruction", ""),
            ]

            # 同一日の最終行かどうか（下ボーダーを強調）
            is_last_in_day = (row_i == len(day_items) - 1)
            bot_side = Side(style="medium", color=C_BORDER_L)                        if is_last_in_day else Side(style="thin", color=C_BORDER)
            top_side = Side(style="thin", color=C_BORDER)
            side_side = Side(style="thin", color=C_BORDER)

            for col_i, val in enumerate(vals, 1):
                cell = ws.cell(row=cur, column=col_i)
                cell.value = val
                cell.fill = fill(day_bg)
                cell.border = Border(
                    left=side_side, right=side_side,
                    top=top_side, bottom=bot_side
                )

                # 列別スタイル
                if col_i == 1:   # Date
                    cell.font = font(C_MUTED, size=9, mono=True)
                    cell.alignment = aln("center", "center")
                elif col_i == 2: # Day
                    cell.font = Font(color=dow_color, size=9, name="Consolas")
                    cell.alignment = aln("center", "center")
                elif col_i == 3: # Subject
                    cell.font = font(C_MUTED, size=9, mono=True)
                    cell.alignment = aln("center", "center")
                elif col_i == 4: # Category
                    cell.font = Font(color=cat_color, bold=True,
                                     size=9, name="Consolas")
                    cell.alignment = aln("center", "center")
                elif col_i == 5: # Textbook
                    cell.font = font(C_MUTED, size=9)
                    cell.alignment = aln("left", "center")
                elif col_i == 6: # Problem
                    cell.font = font(C_TEXT, size=10)
                    cell.alignment = aln("left", "center", wrap=True)
                elif col_i == 7: # Mastery
                    cell.font = Font(color=mastery_color, size=10,
                                     name="Noto Serif JP")
                    cell.alignment = aln("center", "center")
                elif col_i == 8: # Min
                    cell.font = font(C_DIM, size=9, mono=True)
                    cell.alignment = aln("center", "center")
                elif col_i == 9: # Instruction
                    cell.font = font(C_MUTED, size=9)
                    cell.alignment = aln("left", "center", wrap=True)

            # 行の高さを内容に応じて動的設定
            problem_text = str(item.get("problem_number", ""))
            instruction_text = str(item.get("instruction", ""))
            # 問題番号：列幅34で1行≒20文字
            prob_lines = max(1, -(-len(problem_text) // 20))
            # 学習指示：列幅44で1行≒25文字
            instr_lines = max(1, -(-len(instruction_text) // 25))
            row_h = max(prob_lines, instr_lines) * 15 + 4
            row_h = max(20, min(row_h, 200))  # 20〜200ptの範囲
            ws.row_dimensions[cur].height = row_h
            cur += 1

    # ── 未割当ブロック ──
    all_unassigned = []
    for subj in subjects:
        for item in unassigned.get(subj, []):
            all_unassigned.append((subj, item))

    if all_unassigned:
        # 区切り
        ws.merge_cells(f"A{cur}:{get_column_letter(N_COLS)}{cur}")
        sep = ws.cell(row=cur, column=1)
        sep.value = "── UNASSIGNED ──"
        sep.fill = fill("1A0A0A")
        sep.font = Font(color=C_RED, size=8, name="Consolas")
        sep.alignment = aln("left", "center")
        ws.row_dimensions[cur].height = 14
        cur += 1

        for subj, item in all_unassigned:
            cat = item.get("category", "")
            vals = ["—", "—", subj, cat,
                    item.get("textbook", ""),
                    item.get("problem_number", ""),
                    "—",
                    item.get("estimated_minutes", ""),
                    item.get("instruction", "")]
            for col_i, val in enumerate(vals, 1):
                cell = ws.cell(row=cur, column=col_i)
                cell.value = val
                cell.fill = fill("1A0A0A")
                cell.font = font(C_DIM, size=9)
                cell.border = bdr("3A1010")
                cell.alignment = aln("center" if col_i in (1,2,7,8) else "left",
                                     "center")
            ws.row_dimensions[cur].height = 18
            cur += 1

    # オートフィルター
    ws.auto_filter.ref = f"A2:{get_column_letter(N_COLS)}{cur - 1}"


def export_excel(student_id, start_date_str, end_date_str, subject_filter=None):
    """計画表をExcelファイルに出力して保存パスを返す"""
    import openpyxl
    import os
    from datetime import datetime

    plan_data = build_plan_data(
        student_id, start_date_str, end_date_str, subject_filter)
    if not plan_data:
        return None

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    student_name = plan_data["student_name"]
    subjects     = plan_data["subjects"]
    rows         = plan_data["rows"]
    unassigned   = plan_data.get("unassigned", {})

    # 全教科を1シートに出力
    ws = wb.create_sheet(title="Plan")
    _write_excel_sheet(ws, subjects, rows, unassigned,
                       student_name, start_date_str, end_date_str)

    # 保存
    archive_dir = os.path.join(os.path.dirname(__file__), "plan_archives")
    os.makedirs(archive_dir, exist_ok=True)
    base_name = f"{student_name}_{start_date_str}_{end_date_str}"
    filename  = f"{base_name}.xlsx"
    filepath  = os.path.join(archive_dir, filename)
    # 同名ファイルが開かれている場合はタイムスタンプを付加
    if os.path.exists(filepath):
        try:
            import tempfile
            with open(filepath, "a"):
                pass
        except PermissionError:
            from datetime import datetime as _dt
            filename = f"{base_name}_{_dt.now().strftime('%H%M%S')}.xlsx"
            filepath = os.path.join(archive_dir, filename)
    wb.save(filepath)

    # historyテーブルに記録
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO plan_history (student_id, filename, created_at)
            VALUES (?, ?, ?)
        """, (student_id, filename,
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    except Exception:
        pass

    return filepath

