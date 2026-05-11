import os

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")

# ─── 1. excel_export.pyのassign_days_v2を修正 ─────────
excel_path = os.path.join(base, "excel_export.py")
with open(excel_path, "r", encoding="utf-8") as f:
    excel = f.read()

old_assign = """def assign_days_v2(plan, schedule, student_id, start_date_str, end_date_str):
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

    assigned = []
    unassigned = []
    date_textbook_count = defaultdict(lambda: defaultdict(int))

    def try_assign(item, search_dates):
        minutes = get_adjusted_minutes(item)
        textbook = item["textbook"]
        valid = [d for d in search_dates if remaining.get(d, 0) >= minutes]
        if not valid:
            return False
        sorted_d = sorted(valid,
                          key=lambda d: (date_textbook_count[d][textbook],
                                         -remaining[d]))
        d = sorted_d[0]
        remaining[d] -= minutes
        item["assigned_date"] = d
        date_textbook_count[d][textbook] += 1
        assigned.append(item)
        return True

    plan_sorted = sorted(plan, key=priority_score)
    review_list = [p for p in plan_sorted if p["category"] in ("復習", "定着", "再定着")]
    yosyu_list = [p for p in plan_sorted if p["category"] == "予習"]

    for item in [p for p in review_list if p["category"] == "復習"]:
        class_dates = subject_class_dates.get(item["subject"], [])
        search_from = dates_sorted[0]
        past = [d for d in class_dates if d <= start_date_str]
        if past:
            search_from = past[-1]
        search = [d for d in dates_sorted if d >= search_from]
        if not try_assign(item, search):
            item["assigned_date"] = None
            unassigned.append(item)

    for item in [p for p in review_list
                 if p["category"] in ("定着", "再定着")]:
        if not try_assign(item, dates_sorted):
            item["assigned_date"] = None
            unassigned.append(item)

    for item in yosyu_list:
        class_dates = subject_class_dates.get(item["subject"], [])
        future = sorted([d for d in class_dates if d > start_date_str])
        if future:
            next_class = future[0]
            search = list(reversed(
                [d for d in dates_sorted if d <= next_class]))
        else:
            search = list(reversed(dates_sorted))
        if not try_assign(item, search):
            item["assigned_date"] = None
            unassigned.append(item)

    return assigned, unassigned"""

new_assign = """def assign_days_v2(plan, schedule, student_id, start_date_str, end_date_str):
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

    assigned = []
    unassigned = []

    def try_assign(item, search_dates):
        minutes = get_adjusted_minutes(item)
        valid = [d for d in search_dates if remaining.get(d, 0) >= minutes]
        if not valid:
            return False
        # 残り時間が均等になるよう、残り時間が最も多い日に割り当てる
        d = max(valid, key=lambda x: remaining[x])
        remaining[d] -= minutes
        item["assigned_date"] = d
        assigned.append(item)
        return True

    # 復習・定着・再定着：priority_scoreでソート
    plan_sorted = sorted(plan, key=priority_score)
    review_list = [p for p in plan_sorted
                   if p["category"] in ("復習", "定着", "再定着")]

    # 予習：problem_id順にソート（問題集の順番通り）
    yosyu_list = sorted(
        [p for p in plan if p["category"] == "予習"],
        key=lambda x: x.get("problem_id", 0))

    for item in [p for p in review_list if p["category"] == "復習"]:
        class_dates = subject_class_dates.get(item["subject"], [])
        search_from = dates_sorted[0]
        past = [d for d in class_dates if d <= start_date_str]
        if past:
            search_from = past[-1]
        search = [d for d in dates_sorted if d >= search_from]
        if not try_assign(item, search):
            item["assigned_date"] = None
            unassigned.append(item)

    for item in [p for p in review_list
                 if p["category"] in ("定着", "再定着")]:
        if not try_assign(item, dates_sorted):
            item["assigned_date"] = None
            unassigned.append(item)

    for item in yosyu_list:
        class_dates = subject_class_dates.get(item["subject"], [])
        future = sorted([d for d in class_dates if d > start_date_str])
        if future:
            next_class = future[0]
            # 予習は授業直前から逆順に、均等分散で配置
            search = [d for d in dates_sorted if d <= next_class]
        else:
            search = list(dates_sorted)
        if not try_assign(item, search):
            item["assigned_date"] = None
            unassigned.append(item)

    return assigned, unassigned"""

if old_assign in excel:
    excel = excel.replace(old_assign, new_assign)
    with open(excel_path, "w", encoding="utf-8") as f:
        f.write(excel)
    print("✅ assign_days_v2を修正しました")
else:
    print("❌ assign_days_v2が見つかりません")

# ─── 2. database.pyにget_plan_v2のproblem_idを追加 ──────
db_path = os.path.join(base, "database.py")
with open(db_path, "r", encoding="utf-8") as f:
    db = f.read()

old_select = """    c.execute(\"\"\"
        SELECT a.*, p.subject, p.textbook, p.problem_number,
               p.importance, p.difficulty, p.review_value,
               p.estimated_minutes, p.instruction,
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
    \"\"\", (student_id, end_date_str))"""

new_select = """    c.execute(\"\"\"
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
    \"\"\", (student_id, end_date_str))"""

if old_select in db:
    db = db.replace(old_select, new_select)
    with open(db_path, "w", encoding="utf-8") as f:
        f.write(db)
    print("✅ database.pyにproblem_idを追加しました")
else:
    print("❌ database.pyの対象箇所が見つかりません")

# ─── 3. 出題予定管理の並び順を新しい順に変更 ────────────
app_path = os.path.join(base, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    app = f.read()

old_order = """            WHERE a.student_id = ?
            ORDER BY a.scheduled_date, p.subject
        \"\"\", (student_id,))"""

new_order = """            WHERE a.student_id = ?
            ORDER BY a.scheduled_date DESC, p.subject
        \"\"\", (student_id,))"""

if old_order in app:
    app = app.replace(old_order, new_order)
    print("✅ 出題予定の並び順を修正しました")
else:
    print("❌ 出題予定の並び順が見つかりません")

# ─── 4. 自動昇格機能をdatabase.pyに追加 ─────────────────
with open(db_path, "r", encoding="utf-8") as f:
    db = f.read()

auto_promote_func = """
def auto_promote_past_assignments(student_id):
    \"\"\"
    出題日が過ぎた問題を自動的に正答扱いして昇格させる。
    特段誤りの報告がない場合、出題日翌日以降に自動処理。
    \"\"\"
    conn = get_connection()
    c = conn.cursor()
    today = date.today().isoformat()

    c.execute(\"\"\"
        SELECT a.problem_id, a.scheduled_date, a.category,
               a.assignment_id,
               p.review_value,
               (SELECT mastery FROM history h
                WHERE h.student_id = a.student_id
                AND h.problem_id = a.problem_id
                ORDER BY h.date DESC LIMIT 1) as mastery
        FROM assignments a
        JOIN problems p ON a.problem_id = p.problem_id
        WHERE a.student_id = ?
          AND a.scheduled_date < ?
          AND a.scheduled_date != '2099-12-31'
          AND a.category IN ('予習', '復習', '定着', '再定着')
    \"\"\", (student_id, today))
    rows = c.fetchall()

    promoted = 0
    for row in rows:
        problem_id = row["problem_id"]
        scheduled_date = row["scheduled_date"]
        current_mastery = row["mastery"] if row["mastery"] else 1

        # 新しい習熟度を計算
        new_mastery = min(current_mastery + 1, 3)

        # historyに正答記録を追加
        c.execute(\"\"\"
            INSERT INTO history
            (student_id, problem_id, date, correct, mastery, category)
            VALUES (?, ?, ?, ?, ?, ?)
        \"\"\", (student_id, problem_id, scheduled_date,
                1, new_mastery, "自動昇格"))

        # 次回出題日を計算
        review_value = row["review_value"]
        next_date = get_next_date(review_value, new_mastery, scheduled_date)
        category = {1: "復習", 2: "定着"}.get(new_mastery, "再定着")

        # 出題予定を更新
        c.execute("DELETE FROM assignments WHERE assignment_id=?",
                  (row["assignment_id"],))
        c.execute(\"\"\"
            INSERT INTO assignments
            (student_id, problem_id, scheduled_date, category)
            VALUES (?, ?, ?, ?)
        \"\"\", (student_id, problem_id, next_date.isoformat(), category))
        promoted += 1

    conn.commit()
    conn.close()
    return promoted

"""

if "auto_promote_past_assignments" not in db:
    db = db + auto_promote_func
    with open(db_path, "w", encoding="utf-8") as f:
        f.write(db)
    print("✅ auto_promote_past_assignmentsを追加しました")

# ─── 5. previewページで自動昇格を実行するフックを追加 ────
with open(app_path, "r", encoding="utf-8") as f:
    app = f.read()

old_preview_start = """    if request.method == "POST":
        student_id = request.form["student_id"]
        target_date = request.form["date"]
        start_date = request.form.get("start_date", "")
        subject_filter = request.form.get("subject_filter", "")
        if not start_date:
            start_date = date.today().isoformat()"""

new_preview_start = """    if request.method == "POST":
        student_id = request.form["student_id"]
        target_date = request.form["date"]
        start_date = request.form.get("start_date", "")
        subject_filter = request.form.get("subject_filter", "")
        if not start_date:
            start_date = date.today().isoformat()

        # 出題日が過ぎた問題を自動昇格
        from database import auto_promote_past_assignments
        auto_promote_past_assignments(student_id)"""

if old_preview_start in app:
    app = app.replace(old_preview_start, new_preview_start)
    print("✅ previewに自動昇格フックを追加しました")
else:
    print("❌ previewの対象箇所が見つかりません")

# ─── 6. 更新後にページトップへ飛ばない修正 ──────────────
# assignments_listの更新後
old_redirect_assign = """    return redirect(f"/assignments/list?student_id={student_id}")


@app.route("/assignments/delete/<int:assignment_id>", methods=["POST"])
def assignment_delete(assignment_id):
    student_id = request.form.get("student_id", "")
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM assignments WHERE assignment_id=?", (assignment_id,))
    conn.commit()
    conn.close()
    return redirect(f"/assignments/list?student_id={student_id}")"""

new_redirect_assign = """    return redirect(f"/assignments/list?student_id={student_id}#row-{assignment_id}")


@app.route("/assignments/delete/<int:assignment_id>", methods=["POST"])
def assignment_delete(assignment_id):
    student_id = request.form.get("student_id", "")
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM assignments WHERE assignment_id=?", (assignment_id,))
    conn.commit()
    conn.close()
    return redirect(f"/assignments/list?student_id={student_id}")"""

if old_redirect_assign in app:
    app = app.replace(old_redirect_assign, new_redirect_assign)
    print("✅ assignments_listのリダイレクトを修正しました")

# problems_listの削除後もその場にとどまる（すでにJSで対応済み）
# record_listの修正
old_record_redirect = "    return redirect(\"/record/list\")"
new_record_redirect = "    return redirect(request.referrer or \"/record/list\")"

app = app.replace(old_record_redirect, new_record_redirect)

# class_scheduleのリダイレクト
old_class_redirect = "        return redirect(\n            f\"/class_schedule?student_id={student_id}\")"
new_class_redirect = "        return redirect(\n            f\"/class_schedule?student_id={student_id}#subject-{subject}\")"

if old_class_redirect in app:
    app = app.replace(old_class_redirect, new_class_redirect)
    print("✅ class_scheduleのリダイレクトを修正しました")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(app)
print("✅ app.py を更新しました")

print("✅ 全て完了")