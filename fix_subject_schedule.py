import os
import sqlite3

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")
DB_PATH = os.path.join(base, "study_planner.db")

# ─── 1. DBにschedule_base_subjectテーブルを追加 ──────────
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS schedule_base_subject (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        subject TEXT NOT NULL,
        dow INTEGER NOT NULL,
        available_minutes INTEGER NOT NULL DEFAULT 0,
        UNIQUE(student_id, subject, dow),
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )
""")
c.execute("""
    CREATE TABLE IF NOT EXISTS schedule_override_subject (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        subject TEXT NOT NULL,
        date TEXT NOT NULL,
        available_minutes INTEGER NOT NULL DEFAULT 0,
        UNIQUE(student_id, subject, date),
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    )
""")
conn.commit()
conn.close()
print("✅ DBテーブルを追加しました")

# ─── 2. database.pyにget_schedule_subject関数を追加 ──────
db_path = os.path.join(base, "database.py")
with open(db_path, "r", encoding="utf-8") as f:
    db_content = f.read()

new_func = '''
def get_schedule_subject(student_id, subject, start_date_str, end_date_str):
    """教科ごとの勉強時間スケジュールを取得する"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT dow, available_minutes FROM schedule_base_subject
        WHERE student_id=? AND subject=?
    """, (student_id, subject))
    base = {row["dow"]: row["available_minutes"] for row in c.fetchall()}
    c.execute("""
        SELECT date, available_minutes FROM schedule_override_subject
        WHERE student_id=? AND subject=? AND date BETWEEN ? AND ?
    """, (student_id, subject, start_date_str, end_date_str))
    overrides = {row["date"]: row["available_minutes"] for row in c.fetchall()}
    conn.close()

    # 教科別設定がない場合はNoneを返す（全体設定を使う）
    if not base and not overrides:
        return None

    schedule = {}
    current = date.fromisoformat(start_date_str)
    end = date.fromisoformat(end_date_str)
    while current <= end:
        date_str = current.isoformat()
        schedule[date_str] = overrides.get(
            date_str, base.get(current.weekday(), 0))
        current += timedelta(days=1)
    return schedule

'''

if "get_schedule_subject" not in db_content:
    db_content = db_content + new_func
    with open(db_path, "w", encoding="utf-8") as f:
        f.write(db_content)
    print("✅ database.py を更新しました")
else:
    print("ℹ️ get_schedule_subjectはすでに存在します")

# ─── 3. excel_export.pyのbuild_plan_dataを更新 ───────────
excel_path = os.path.join(base, "excel_export.py")
with open(excel_path, "r", encoding="utf-8") as f:
    excel_content = f.read()

old_import = """from database import (get_connection, get_plan_v2, get_schedule,
                      get_class_dates_in_range)"""
new_import = """from database import (get_connection, get_plan_v2, get_schedule,
                      get_schedule_subject, get_class_dates_in_range)"""
excel_content = excel_content.replace(old_import, new_import)

old_build = """def build_plan_data(student_id, start_date_str, target_date_str,
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
    schedule = get_schedule(student_id, start_date_str, target_date_str)
    all_plan = get_plan_v2(student_id, start_date_str, target_date_str)

    if subject_filter:
        subjects = [subject_filter]
        plan = [p for p in all_plan if p["subject"] == subject_filter]
    else:
        subjects = all_subjects
        plan = all_plan

    assigned, unassigned = assign_days_v2(
        plan, schedule, student_id, start_date_str, target_date_str)
    dates_with_time = sorted([d for d, m in schedule.items() if m > 0])

    rows = []
    for d in dates_with_time:
        d_obj = date.fromisoformat(d)
        dow = DOW_JA[d_obj.weekday()]
        date_label = str(d_obj.month) + "/" + str(d_obj.day) + "（" + dow + "）"
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
        "schedule": schedule,
    }"""

new_build = """def build_plan_data(student_id, start_date_str, target_date_str,
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
    }"""

if old_build in excel_content:
    excel_content = excel_content.replace(old_build, new_build)
    with open(excel_path, "w", encoding="utf-8") as f:
        f.write(excel_content)
    print("✅ excel_export.py を更新しました")
else:
    print("❌ build_plan_dataの対象箇所が見つかりません")

# ─── 4. app.pyにschedule_subjectルートを追加 ────────────
app_path = os.path.join(base, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

subject_schedule_route = '''
@app.route("/schedule_subject", methods=["GET", "POST"])
def schedule_subject():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()

    if request.method == "POST":
        action = request.form.get("action")
        student_id = request.form["student_id"]
        subject = request.form["subject"]

        if action == "save_base":
            for dow in range(7):
                minutes = int(request.form.get(f"dow_{dow}", 0))
                c.execute("""
                    INSERT INTO schedule_base_subject
                    (student_id, subject, dow, available_minutes)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(student_id, subject, dow)
                    DO UPDATE SET available_minutes=?
                """, (student_id, subject, dow, minutes, minutes))
            conn.commit()

        elif action == "save_override":
            date_str = request.form["override_date"]
            minutes = int(request.form.get("override_minutes", 0))
            c.execute("""
                INSERT INTO schedule_override_subject
                (student_id, subject, date, available_minutes)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(student_id, subject, date)
                DO UPDATE SET available_minutes=?
            """, (student_id, subject, date_str, minutes, minutes))
            conn.commit()

        conn.close()
        return redirect(
            f"/schedule_subject?student_id={student_id}&subject={subject}")

    selected_student = request.args.get(
        "student_id", students[0]["student_id"] if students else None)
    selected_subject = request.args.get("subject", "")

    student_subjects = []
    base_schedule = {}

    if selected_student:
        c.execute("SELECT subjects FROM students WHERE student_id=?",
                  (selected_student,))
        row = c.fetchone()
        if row:
            student_subjects = [s.strip()
                                 for s in row["subjects"].split(",")]
        if not selected_subject and student_subjects:
            selected_subject = student_subjects[0]

        if selected_subject:
            c.execute("""
                SELECT dow, available_minutes FROM schedule_base_subject
                WHERE student_id=? AND subject=?
                ORDER BY dow
            """, (selected_student, selected_subject))
            base_schedule = {r["dow"]: r["available_minutes"]
                             for r in c.fetchall()}

    conn.close()
    return render_template("schedule_subject.html",
                           students=students,
                           selected_student=selected_student,
                           selected_subject=selected_subject,
                           student_subjects=student_subjects,
                           base_schedule=base_schedule)

'''

if "/schedule_subject" not in app_content:
    idx = app_content.rfind("if __name__")
    app_content = app_content[:idx] + subject_schedule_route + app_content[idx:]
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app_content)
    print("✅ app.py を更新しました")

# ─── 5. schedule_subject.htmlを作成 ─────────────────────
schedule_subject_html = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>教科別勉強時間登録</title>
  <style>
    body { font-family: sans-serif; max-width: 700px; margin: 40px auto; background: #f5f7fa; }
    h1 { color: #2c3e50; }
    .form-box { background: white; padding: 24px; border-radius: 8px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    h2 { color: #2c3e50; margin-top: 0; font-size: 16px; }
    label { display: block; margin-top: 12px; font-weight: bold; }
    select, input[type="date"], input[type="number"] { width: 100%; padding: 8px; margin-top: 4px; border: 1px solid #ccc; border-radius: 4px; font-size: 15px; box-sizing: border-box; }
    .dow-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; margin-top: 12px; }
    .dow-item { text-align: center; }
    .dow-item span { display: block; font-weight: bold; margin-bottom: 4px; font-size: 13px; }
    .dow-item input { padding: 4px; font-size: 13px; text-align: center; }
    .override-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 12px; }
    button { margin-top: 16px; padding: 10px 28px; background: #4472C4; color: white; border: none; border-radius: 6px; font-size: 15px; cursor: pointer; }
    button:hover { background: #2c5fa8; }
    .hint { font-size: 12px; color: #888; margin-top: 4px; }
    a { color: #4472C4; }
    .note { background: #fff3cd; padding: 12px; border-radius: 6px; font-size: 13px; margin-bottom: 16px; }
  </style>
</head>
<body>
  <h1>⑩ 教科別勉強時間登録</h1>

  <div class="note">
    教科ごとに勉強時間を設定すると、各教科が独立して時間を割り当てます。<br>
    設定しない教科は全体の勉強時間設定（⑥）が使われます。
  </div>

  <div class="form-box">
    <h2>生徒と教科を選択</h2>
    <form method="GET">
      <label>生徒</label>
      <select name="student_id" onchange="this.form.submit()">
        {% for s in students %}
        <option value="{{ s.student_id }}"
          {% if s.student_id == selected_student %}selected{% endif %}>
          {{ s.name }}
        </option>
        {% endfor %}
      </select>
      {% if student_subjects %}
      <label>教科</label>
      <select name="subject" onchange="this.form.submit()">
        {% for sub in student_subjects %}
        <option value="{{ sub }}"
          {% if sub == selected_subject %}selected{% endif %}>
          {{ sub }}
        </option>
        {% endfor %}
      </select>
      {% endif %}
    </form>
  </div>

  {% if selected_subject %}
  <div class="form-box">
    <h2>{{ selected_subject }}の曜日別勉強時間（分）</h2>
    <p class="hint">0の場合はその曜日に{{ selected_subject }}の学習を割り当てません。</p>
    <form method="POST">
      <input type="hidden" name="action" value="save_base">
      <input type="hidden" name="student_id" value="{{ selected_student }}">
      <input type="hidden" name="subject" value="{{ selected_subject }}">
      <div class="dow-grid">
        {% set dow_names = ["月", "火", "水", "木", "金", "土", "日"] %}
        {% for i in range(7) %}
        <div class="dow-item">
          <span>{{ dow_names[i] }}</span>
          <input type="number" name="dow_{{ i }}" min="0" step="5"
            value="{{ base_schedule.get(i, 0) }}" placeholder="0">
        </div>
        {% endfor %}
      </div>
      <p class="hint">単位：分</p>
      <button type="submit">保存</button>
    </form>
  </div>

  <div class="form-box">
    <h2>特定の日だけ変更</h2>
    <form method="POST">
      <input type="hidden" name="action" value="save_override">
      <input type="hidden" name="student_id" value="{{ selected_student }}">
      <input type="hidden" name="subject" value="{{ selected_subject }}">
      <div class="override-row">
        <div>
          <label>日付</label>
          <input type="date" name="override_date" required>
        </div>
        <div>
          <label>勉強時間（分）</label>
          <input type="number" name="override_minutes" min="0" step="5"
            placeholder="例：60" required>
        </div>
      </div>
      <button type="submit">上書き保存</button>
    </form>
  </div>
  {% endif %}

  <p><a href="/">← トップに戻る</a></p>
</body>
</html>"""

with open(os.path.join(templates, "schedule_subject.html"), "w",
          encoding="utf-8") as f:
    f.write(schedule_subject_html)
print("✅ schedule_subject.html を作成しました")

# ─── 6. index.htmlを更新 ────────────────────────────────
index_html = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>学習計画管理システム</title>
  <style>
    body { font-family: sans-serif; max-width: 600px; margin: 60px auto; background: #f5f7fa; }
    h1 { color: #2c3e50; }
    .menu a {
      display: block; margin: 16px 0; padding: 18px 24px;
      background: #4472C4; color: white; text-decoration: none;
      border-radius: 8px; font-size: 18px;
    }
    .menu a:hover { background: #2c5fa8; }
    .menu a.sub {
      background: #7f8c8d; font-size: 15px;
      padding: 12px 24px; margin: -8px 0 16px 0;
    }
    .menu a.sub:hover { background: #636e72; }
  </style>
</head>
<body>
  <h1>📚 学習計画管理システム</h1>
  <div class="menu">
    <a href="/problems">① 問題マスタ登録</a>
    <a href="/problems/list" class="sub">　└ 問題一覧・編集・削除</a>
    <a href="/record">② 授業記録入力</a>
    <a href="/record/list">③ 授業記録修正・習熟度修正</a>
    <a href="/assignments/list">④ 出題予定管理</a>
    <a href="/preview">⑤ 計画表プレビュー・出力</a>
    <a href="/schedule">⑥ 勉強時間登録（全体）</a>
    <a href="/schedule_subject">⑦ 勉強時間登録（教科別）</a>
    <a href="/students">⑧ 生徒管理</a>
    <a href="/history">⑨ 過去の計画表</a>
    <a href="/class_schedule">⑩ 授業スケジュール管理</a>
  </div>
</body>
</html>"""

with open(os.path.join(templates, "index.html"), "w", encoding="utf-8") as f:
    f.write(index_html)
print("✅ index.html を更新しました")
print("✅ 全て完了")