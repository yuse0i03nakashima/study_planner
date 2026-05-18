import os, re
from datetime import date, timedelta

base = r"C:\Users\ynaka\study_planner"
app_path = os.path.join(base, "app.py")

with open(app_path, "r", encoding="utf-8") as f:
    app = f.read()

# ─── 1. 次回授業日の自動計算ユーティリティをdatabase.pyに追加 ──
db_path = os.path.join(base, "database.py")
with open(db_path, "r", encoding="utf-8") as f:
    db = f.read()

auto_next_func = '''

def get_auto_next_class_date(student_id, subject):
    """
    class_schedule_overrideがあればそれを返す。
    なければclass_schedule_baseの曜日から
    「今日以降の最初の授業日」を自動計算して返す。
    """
    conn = get_connection()
    c = conn.cursor()

    # overrideを確認
    c.execute("""
        SELECT next_class_date FROM class_schedule_override
        WHERE student_id=? AND subject=?
    """, (student_id, subject))
    row = c.fetchone()
    if row and row["next_class_date"]:
        conn.close()
        return row["next_class_date"]

    # baseの曜日から計算
    c.execute("""
        SELECT dow FROM class_schedule_base
        WHERE student_id=? AND subject=?
    """, (student_id, subject))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return None

    dow_map = {"mon":0,"tue":1,"wed":2,"thu":3,"fri":4,"sat":5,"sun":6}
    class_dows = set(dow_map[r["dow"]] for r in rows if r["dow"] in dow_map)

    today = date.today()
    for delta in range(1, 14):
        d = today + timedelta(days=delta)
        if d.weekday() in class_dows:
            return d.isoformat()

    return None
'''

if "get_auto_next_class_date" not in db:
    db = db + auto_next_func
    with open(db_path, "w", encoding="utf-8") as f:
        f.write(db)
    print("✅ get_auto_next_class_dateをdatabase.pyに追加しました")

# ─── 2. studentsルートを更新（一覧ページ） ───────────────
new_students_list = '''\
def students():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()
    conn.close()
    return render_template("students.html", students=students)
'''

pattern = re.compile(r'def students\(\):.*?(?=\n@app\.route|\nif __name__)', re.DOTALL)
if pattern.search(app):
    app = pattern.sub(new_students_list, app)
    print("✅ studentsルートを更新しました")

# ─── 3. student_detailルートを追加 ───────────────────────
new_detail_route = '''
@app.route("/students/<student_id>", methods=["GET"])
def student_detail(student_id):
    from database import get_auto_next_class_date
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM students WHERE student_id=?", (student_id,))
    student = c.fetchone()
    if not student:
        conn.close()
        return "Student not found", 404

    subjects = [s.strip() for s in student["subjects"].split(",")]

    # テキスト一覧
    c.execute("""
        SELECT t.textbook_id, t.name, t.subject,
               s.name as series_name,
               COUNT(DISTINCT p.problem_id) as problem_count
        FROM textbooks t
        LEFT JOIN series s ON t.series_id = s.series_id
        LEFT JOIN problems p ON t.textbook_id = p.textbook_id
        JOIN student_textbooks st ON t.textbook_id = st.textbook_id
        WHERE st.student_id=?
        GROUP BY t.textbook_id ORDER BY t.subject, t.name
    """, (student_id,))
    textbooks = c.fetchall()

    # 全体スケジュール
    c.execute("SELECT dow, available_minutes FROM schedule_base WHERE student_id=?",
              (student_id,))
    base_schedule = {r["dow"]: r["available_minutes"] for r in c.fetchall()}

    c.execute("SELECT date, available_minutes FROM schedule_override WHERE student_id=? ORDER BY date",
              (student_id,))
    overrides = c.fetchall()

    # 教科別スケジュール
    subject_base = {}
    c.execute("SELECT subject, dow, available_minutes FROM schedule_base_subject WHERE student_id=?",
              (student_id,))
    for r in c.fetchall():
        if r["subject"] not in subject_base:
            subject_base[r["subject"]] = {}
        subject_base[r["subject"]][r["dow"]] = r["available_minutes"]

    subject_overrides = {}
    c.execute("""SELECT subject, date, available_minutes FROM schedule_override_subject
                 WHERE student_id=? ORDER BY subject, date""", (student_id,))
    for r in c.fetchall():
        if r["subject"] not in subject_overrides:
            subject_overrides[r["subject"]] = []
        subject_overrides[r["subject"]].append(r)

    # 授業曜日
    schedule_map = {}
    c.execute("SELECT subject, dow FROM class_schedule_base WHERE student_id=?",
              (student_id,))
    for r in c.fetchall():
        if r["subject"] not in schedule_map:
            schedule_map[r["subject"]] = {}
        schedule_map[r["subject"]][r["dow"]] = True

    # 次回授業日（override）
    next_class_map = {}
    c.execute("SELECT subject, next_class_date FROM class_schedule_override WHERE student_id=?",
              (student_id,))
    for r in c.fetchall():
        next_class_map[r["subject"]] = r["next_class_date"] or ""

    conn.close()

    # 自動計算された次回授業日
    auto_next = {}
    for subj in subjects:
        if not next_class_map.get(subj):
            auto_next[subj] = get_auto_next_class_date(student_id, subj) or "—"

    return render_template("student_detail.html",
                           student=student,
                           subjects=subjects,
                           textbooks=textbooks,
                           base_schedule=base_schedule,
                           overrides=overrides,
                           subject_base=subject_base,
                           subject_overrides=subject_overrides,
                           schedule_map=schedule_map,
                           next_class_map=next_class_map,
                           auto_next=auto_next)


@app.route("/students/<student_id>/update", methods=["POST"])
def student_update(student_id):
    name       = request.form.get("name", "").strip()
    subjects   = request.form.get("subjects", "").strip()
    plan_mode  = request.form.get("plan_mode", "all")
    conn = get_connection()
    c = conn.cursor()
    c.execute("""UPDATE students SET name=?, subjects=?, plan_mode=?
                 WHERE student_id=?""",
              (name, subjects, plan_mode, student_id))
    conn.commit()
    conn.close()
    return redirect(f"/students/{student_id}#profile")

'''

if "/students/<student_id>" not in app:
    idx = app.rfind("if __name__")
    app = app[:idx] + new_detail_route + app[idx:]
    print("✅ student_detailルートを追加しました")
else:
    print("ℹ️  student_detailルートはすでに存在します")

# ─── 4. add_problemでscheduled_dateを自動設定 ───────────
old_add_problem_insert = """\
        conn.commit()
        problem_id = c.lastrowid

        # 生徒×出題予定の登録
        student_ids   = request.form.getlist("student_ids")
        scheduled_date = request.form.get("scheduled_date", "").strip() or "2099-12-31"
        category      = request.form.get("category", "予習")

        for sid in student_ids:"""

new_add_problem_insert = """\
        conn.commit()
        problem_id = c.lastrowid

        # 生徒×出題予定の登録
        from database import get_auto_next_class_date
        student_ids    = request.form.getlist("student_ids")
        scheduled_date = request.form.get("scheduled_date", "").strip()
        category       = request.form.get("category", "予習")

        for sid in student_ids:
            # scheduled_dateが未指定なら自動計算
            if not scheduled_date:
                auto_date = get_auto_next_class_date(sid, subject)
                effective_date = auto_date if auto_date else "2099-12-31"
            else:
                effective_date = scheduled_date"""

if old_add_problem_insert in app:
    app = app.replace(old_add_problem_insert, new_add_problem_insert)
    # student_textbooksとassignmentsの登録でscheduled_dateをeffective_dateに変更
    app = app.replace(
        '""", (sid, problem_id, scheduled_date, category))',
        '""", (sid, problem_id, effective_date, category))'
    )
    print("✅ add_problemにscheduled_date自動設定を追加しました")
else:
    print("❌ add_problemのINSERT前処理が見つかりません（手動確認が必要）")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(app)

print("✅ Step B 完了")