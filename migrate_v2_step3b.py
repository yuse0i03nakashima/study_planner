import os

base = r"C:\Users\ynaka\study_planner"
excel_path = os.path.join(base, "excel_export.py")

with open(excel_path, "r", encoding="utf-8") as f:
    content = f.read()

# assign_days_v2を完全に書き直す
old_func_start = "def assign_days_v2(plan, schedule, student_id, start_date_str, end_date_str):"
old_func_end = "    return assigned, unassigned"

start_idx = content.find(old_func_start)
end_idx = content.find(old_func_end, start_idx) + len(old_func_end)

new_func = '''def assign_days_v2(plan, schedule, student_id, start_date_str, end_date_str):
    """
    新しい割り当てロジック：
    予習：problem_id順 × テキスト間インターリーブ分散
    復習：前半60%・後半40%に分散して全問振り分け
    定着・再定着：残り時間に代表問題を優先、抑制中はスキップ
    """
    from database import get_suppressed_problems
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

    # 抑制中の問題IDを取得
    suppressed_ids = set(get_suppressed_problems(student_id))

    assigned = []
    unassigned = []
    n = len(dates_sorted)

    def try_assign_to_date(item, d):
        minutes = get_adjusted_minutes(item)
        if remaining.get(d, 0) >= minutes:
            remaining[d] -= minutes
            item["assigned_date"] = d
            assigned.append(item)
            return True
        return False

    def try_assign(item, search_dates):
        minutes = get_adjusted_minutes(item)
        valid = [d for d in search_dates if remaining.get(d, 0) >= minutes]
        if not valid:
            return False
        d = max(valid, key=lambda x: remaining[x])
        remaining[d] -= minutes
        item["assigned_date"] = d
        assigned.append(item)
        return True

    # ─── 予習：problem_id順 × テキスト間インターリーブ ───
    yosyu_items = sorted(
        [p for p in plan if p["category"] == "予習"],
        key=lambda x: x.get("problem_id", 0))

    # テキストIDごとにグループ化
    from collections import defaultdict
    yosyu_by_textbook = defaultdict(list)
    for item in yosyu_items:
        tb_id = item.get("textbook_id") or item.get("textbook", "unknown")
        yosyu_by_textbook[tb_id].append(item)

    # インターリーブ：各テキストから1問ずつ交互に取り出す
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

    # 予習は出題期間の全体に均等分散（次回授業日直前に集中させない）
    for item in interleaved_yosyu:
        class_dates = subject_class_dates.get(item["subject"], [])
        future = sorted([d for d in class_dates if d > start_date_str])
        if future:
            next_class = future[0]
            search = [d for d in dates_sorted if d <= next_class]
        else:
            search = list(dates_sorted)
        if not try_assign(item, search):
            item["assigned_date"] = None
            unassigned.append(item)

    # ─── 復習：前半60%・後半40%に分散 ──────────────────
    fukushu_items = sorted(
        [p for p in plan if p["category"] == "復習"],
        key=priority_score)

    front_end = max(1, int(n * 0.6))
    front_dates = dates_sorted[:front_end]
    back_dates = dates_sorted[front_end:]

    total = len(fukushu_items)
    front_count = max(1, int(total * 0.6)) if total > 0 else 0

    for i, item in enumerate(fukushu_items):
        if i < front_count:
            search = front_dates if front_dates else dates_sorted
        else:
            search = back_dates if back_dates else dates_sorted
        if not try_assign(item, search):
            # フォールバック：全日付で再試行
            if not try_assign(item, dates_sorted):
                item["assigned_date"] = None
                unassigned.append(item)

    # ─── 定着・再定着：代表問題優先、抑制中はスキップ ──
    teichaku_items = [p for p in plan
                      if p["category"] in ("定着", "再定着")]

    # 代表問題（復習価値4以上）と通常問題に分離
    rep_items = [p for p in teichaku_items
                 if int(p.get("review_value", 0) or 0) >= 4
                 and p.get("problem_id") not in suppressed_ids]
    normal_items = [p for p in teichaku_items
                    if int(p.get("review_value", 0) or 0) < 4
                    and p.get("problem_id") not in suppressed_ids]
    skipped_items = [p for p in teichaku_items
                     if p.get("problem_id") in suppressed_ids]

    # 代表問題を優先してソート・配置
    rep_items_sorted = sorted(rep_items, key=priority_score)
    for item in rep_items_sorted:
        if not try_assign(item, dates_sorted):
            item["assigned_date"] = None
            unassigned.append(item)

    # 通常問題を残り時間に配置
    normal_sorted = sorted(normal_items, key=priority_score)
    for item in normal_sorted:
        if not try_assign(item, dates_sorted):
            item["assigned_date"] = None
            unassigned.append(item)

    # 抑制中の問題は未割当として記録
    for item in skipped_items:
        item["assigned_date"] = None
        # 未割当には含めず、抑制中として静かにスキップ

    return assigned, unassigned'''

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_func + "\n" + content[end_idx:]
    with open(excel_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ assign_days_v2を更新しました")
else:
    print("❌ assign_days_v2が見つかりません")

# ─── get_plan_v2にtextbook_idを含める ───────────────────
db_path = os.path.join(base, "database.py")
with open(db_path, "r", encoding="utf-8") as f:
    db_content = f.read()

old_plan_query = '''    c.execute("""
        SELECT a.*, p.subject, p.textbook, p.problem_number,
               p.importance, p.difficulty, p.review_value,
               p.estimated_minutes, p.instruction, p.problem_id,
               (SELECT mastery FROM history h
                WHERE h.student_id = a.student_id AND h.problem_id = a.problem_id
                ORDER BY h.date DESC LIMIT 1) as mastery,
               (SELECT date FROM history h
                WHERE h.student_id = a.student_id AND h.problem_id = a.problem_id
                ORDER BY h.date DESC LIMIT 1) as last_date
        FROM assignments a
        JOIN problems p ON a.problem_id = p.problem_id
        WHERE a.student_id = ?
          AND a.scheduled_date <= ?
          AND a.scheduled_date != '2099-12-31'
        ORDER BY p.review_value DESC, p.importance DESC
    """, (student_id, end_date_str))'''

new_plan_query = '''    c.execute("""
        SELECT a.*, p.subject, p.textbook, p.problem_number,
               p.importance, p.difficulty, p.review_value,
               p.estimated_minutes, p.instruction, p.problem_id,
               p.textbook_id, p.order_in_textbook,
               (SELECT mastery FROM history h
                WHERE h.student_id = a.student_id AND h.problem_id = a.problem_id
                ORDER BY h.date DESC LIMIT 1) as mastery,
               (SELECT date FROM history h
                WHERE h.student_id = a.student_id AND h.problem_id = a.problem_id
                ORDER BY h.date DESC LIMIT 1) as last_date
        FROM assignments a
        JOIN problems p ON a.problem_id = p.problem_id
        WHERE a.student_id = ?
          AND a.scheduled_date <= ?
          AND a.scheduled_date != '2099-12-31'
        ORDER BY p.review_value DESC, p.importance DESC
    """, (student_id, end_date_str))'''

if old_plan_query in db_content:
    db_content = db_content.replace(old_plan_query, new_plan_query)
    with open(db_path, "w", encoding="utf-8") as f:
        f.write(db_content)
    print("✅ get_plan_v2にtextbook_id・order_in_textbookを追加しました")
else:
    print("❌ get_plan_v2のクエリが見つかりません")

# ─── get_plan_v2のplanリスト生成にtextbook_idを追加 ──────
with open(db_path, "r", encoding="utf-8") as f:
    db_content = f.read()

old_plan_item = '''    for r in rows:
        mastery = r["mastery"] if r["mastery"] else 1
        plan.append({
            "category": r["category"],
            "subject": r["subject"],
            "textbook": r["textbook"],
            "problem_number": r["problem_number"],
            "importance": r["importance"],
            "difficulty": r["difficulty"],
            "review_value": r["review_value"],
            "estimated_minutes": r["estimated_minutes"],
            "mastery": "★" * mastery,
            "mastery_int": mastery,
            "last_date": r["last_date"] if r["last_date"] else "（初見）",
            "instruction": r["instruction"] if r["instruction"] else "",
            "problem_id": r["problem_id"],
        })'''

new_plan_item = '''    for r in rows:
        mastery = r["mastery"] if r["mastery"] else 1
        plan.append({
            "category": r["category"],
            "subject": r["subject"],
            "textbook": r["textbook"],
            "problem_number": r["problem_number"],
            "importance": r["importance"],
            "difficulty": r["difficulty"],
            "review_value": r["review_value"],
            "estimated_minutes": r["estimated_minutes"],
            "mastery": "★" * mastery,
            "mastery_int": mastery,
            "last_date": r["last_date"] if r["last_date"] else "（初見）",
            "instruction": r["instruction"] if r["instruction"] else "",
            "problem_id": r["problem_id"],
            "textbook_id": r["textbook_id"],
            "order_in_textbook": r["order_in_textbook"] or r["problem_id"],
        })'''

if old_plan_item in db_content:
    db_content = db_content.replace(old_plan_item, new_plan_item)
    with open(db_path, "w", encoding="utf-8") as f:
        f.write(db_content)
    print("✅ get_plan_v2のplanアイテムにtextbook_id等を追加しました")
else:
    print("❌ get_plan_v2のplanアイテム生成が見つかりません")

print("✅ Step3b完了")
print("アプリを再起動して計画表プレビューで動作確認してください。")