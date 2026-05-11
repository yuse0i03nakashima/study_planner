from flask import Flask, render_template, request, redirect, send_file, jsonify
from database import (init_db, get_connection, calc_new_mastery,
                      update_assignments_after_record, get_plan, get_schedule,
                      save_plan_history, get_plan_histories)
from excel_export import export_excel
from datetime import date, timedelta
import os

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


# ─── 問題マスタ ────────────────────────────────────────

@app.route("/problems", methods=["GET", "POST"])
def problems():
    conn = get_connection()
    c = conn.cursor()
    if request.method == "POST":
        subject = request.form["subject"]
        textbook = request.form["textbook"]
        problem_number = request.form["problem_number"]
        importance = int(request.form["importance"])
        difficulty = int(request.form["difficulty"])
        review_value = int(request.form["review_value"])
        estimated_minutes = int(request.form["estimated_minutes"])
        instruction = request.form.get("instruction", "")
        c.execute("""
            INSERT INTO problems
            (subject, textbook, problem_number, importance, difficulty,
             review_value, estimated_minutes, instruction, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (subject, textbook, problem_number, importance, difficulty,
              review_value, estimated_minutes, instruction, "標準"))
        conn.commit()
        problem_id = c.lastrowid
        student_ids = request.form.getlist("student_ids")
        scheduled_date = request.form.get("scheduled_date", "").strip()
        category = request.form.get("category", "予習")
        if scheduled_date and student_ids:
            for sid in student_ids:
                c.execute("""
                    INSERT INTO assignments
                    (student_id, problem_id, scheduled_date, category)
                    VALUES (?, ?, ?, ?)
                """, (sid, problem_id, scheduled_date, category))
        conn.commit()
        conn.close()
        return redirect("/problems")

    c.execute("SELECT * FROM problems ORDER BY problem_id DESC LIMIT 50")
    problems = c.fetchall()
    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()
    conn.close()
    return render_template("problems.html", problems=problems, students=students)


@app.route("/problems/edit/<int:problem_id>", methods=["GET", "POST"])
def problem_edit(problem_id):
    conn = get_connection()
    c = conn.cursor()
    if request.method == "POST":
        subject = request.form["subject"]
        textbook = request.form["textbook"]
        problem_number = request.form["problem_number"]
        importance = int(request.form["importance"])
        difficulty = int(request.form["difficulty"])
        review_value = int(request.form["review_value"])
        estimated_minutes = int(request.form["estimated_minutes"])
        instruction = request.form.get("instruction", "")
        c.execute("""
            UPDATE problems SET
                subject=?, textbook=?, problem_number=?, importance=?,
                difficulty=?, review_value=?, estimated_minutes=?, instruction=?
            WHERE problem_id=?
        """, (subject, textbook, problem_number, importance, difficulty,
              review_value, estimated_minutes, instruction, problem_id))
        conn.commit()
        conn.close()
        return redirect("/problems")

    c.execute("SELECT * FROM problems WHERE problem_id=?", (problem_id,))
    problem = c.fetchone()
    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()
    conn.close()
    return render_template("problem_edit.html", problem=problem, students=students)


@app.route("/problems/delete/<int:problem_id>", methods=["POST"])
def problem_delete(problem_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM assignments WHERE problem_id=?", (problem_id,))
    c.execute("DELETE FROM history WHERE problem_id=?", (problem_id,))
    c.execute("DELETE FROM problems WHERE problem_id=?", (problem_id,))
    conn.commit()
    conn.close()
    return redirect("/problems")


# ─── 授業記録 ──────────────────────────────────────────

@app.route("/record", methods=["GET", "POST"])
def record():
    conn = get_connection()
    c = conn.cursor()
    if request.method == "POST":
        student_id = request.form["student_id"]
        record_date = request.form["date"]
        problem_ids = request.form.getlist("problem_ids")
        for pid in problem_ids:
            correct = int(request.form.get(f"correct_{pid}", "0"))
            new_mastery = calc_new_mastery(student_id, int(pid), correct, record_date)
            c.execute("""
                INSERT INTO history
                (student_id, problem_id, date, correct, mastery, category)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (student_id, int(pid), record_date, correct, new_mastery, "記録"))
            conn.commit()
            update_assignments_after_record(student_id, int(pid), record_date, new_mastery)
        conn.close()
        return redirect("/record")

    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()
    conn.close()
    return render_template("record.html", students=students)


@app.route("/get_assignments")
def get_assignments():
    student_id = request.args.get("student_id")
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT a.assignment_id, a.problem_id, a.category, a.scheduled_date,
               p.subject, p.textbook, p.problem_number, p.importance,
               p.estimated_minutes
        FROM assignments a
        JOIN problems p ON a.problem_id = p.problem_id
        WHERE a.student_id = ?
        ORDER BY a.scheduled_date, p.subject
    """, (student_id,))
    rows = c.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/record/list")
def record_list():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()
    student_id = request.args.get("student_id",
                  students[0]["student_id"] if students else None)
    records = []
    if student_id:
        c.execute("""
            SELECT h.history_id, h.date, h.correct, h.mastery, h.category,
                   p.subject, p.textbook, p.problem_number
            FROM history h
            JOIN problems p ON h.problem_id = p.problem_id
            WHERE h.student_id = ?
            ORDER BY h.date DESC, h.history_id DESC
            LIMIT 100
        """, (student_id,))
        records = c.fetchall()
    conn.close()
    return render_template("record_list.html", students=students,
                           records=records, selected_student=student_id)


@app.route("/record/edit/<int:history_id>", methods=["GET", "POST"])
def record_edit(history_id):
    conn = get_connection()
    c = conn.cursor()
    if request.method == "POST":
        correct = int(request.form["correct"])
        record_date = request.form["date"]
        c.execute("""
            UPDATE history SET correct=?, date=? WHERE history_id=?
        """, (correct, record_date, history_id))
        conn.commit()
        conn.close()
        return redirect(request.referrer or "/record/list")

    c.execute("""
        SELECT h.*, p.subject, p.textbook, p.problem_number
        FROM history h
        JOIN problems p ON h.problem_id = p.problem_id
        WHERE h.history_id=?
    """, (history_id,))
    record = c.fetchone()
    conn.close()
    return render_template("record_edit.html", record=record)


@app.route("/record/delete/<int:history_id>", methods=["POST"])
def record_delete(history_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM history WHERE history_id=?", (history_id,))
    conn.commit()
    conn.close()
    return redirect(request.referrer or "/record/list")


# ─── 生徒管理 ──────────────────────────────────────────

@app.route("/students", methods=["GET", "POST"])
def students():
    conn = get_connection()
    c = conn.cursor()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            student_id = request.form["student_id"]
            name = request.form["name"]
            subjects = request.form["subjects"]
            c.execute("""
                INSERT OR IGNORE INTO students (student_id, name, subjects)
                VALUES (?, ?, ?)
            """, (student_id, name, subjects))
        elif action == "edit":
            student_id = request.form["student_id"]
            name = request.form["name"]
            subjects = request.form["subjects"]
            plan_mode = request.form.get("plan_mode", "all")
            c.execute("""
                UPDATE students SET name=?, subjects=?, plan_mode=?
                WHERE student_id=?
            """, (name, subjects, plan_mode, student_id))
        elif action == "delete":
            student_id = request.form["student_id"]
            c.execute("DELETE FROM assignments WHERE student_id=?", (student_id,))
            c.execute("DELETE FROM history WHERE student_id=?", (student_id,))
            c.execute("DELETE FROM schedule_base WHERE student_id=?", (student_id,))
            c.execute("DELETE FROM schedule_override WHERE student_id=?", (student_id,))
            c.execute("DELETE FROM plan_history WHERE student_id=?", (student_id,))
            c.execute("DELETE FROM students WHERE student_id=?", (student_id,))
        conn.commit()
        conn.close()
        return redirect("/students")

    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()
    conn.close()
    return render_template("students.html", students=students)


# ─── 計画表出力・プレビュー ────────────────────────────

@app.route("/export", methods=["GET", "POST"])
def export():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()
    conn.close()

    if request.method == "POST":
        student_id = request.form["student_id"]
        target_date = request.form["date"]
        start_date = request.form.get("start_date", "")
        if not start_date:
            start_date = date.today().isoformat()

        conn2 = get_connection()
        c2 = conn2.cursor()
        c2.execute("SELECT name FROM students WHERE student_id = ?", (student_id,))
        row = c2.fetchone()
        conn2.close()
        student_name = row["name"] if row else student_id

        os.makedirs("plan_archives", exist_ok=True)
        output_path = os.path.join(
            "plan_archives", f"計画表_{student_name}_{target_date}.xlsx")
        subject_filter = request.form.get("subject_filter", "")
        export_excel(target_date, output_path,
                     student_id=student_id, start_date=start_date,
                     subject_filter=subject_filter if subject_filter else None)
        save_plan_history(student_id, start_date, target_date, output_path)
        return send_file(output_path, as_attachment=True)

    return render_template("export.html", students=students)


@app.route("/preview", methods=["GET", "POST"])
def preview():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()
    conn.close()

    preview_data = None
    selected = {}

    if request.method == "POST":
        student_id = request.form["student_id"]
        target_date = request.form["date"]
        start_date = request.form.get("start_date", "")
        subject_filter = request.form.get("subject_filter", "")
        if not start_date:
            start_date = date.today().isoformat()

        # 出題日が過ぎた問題を自動昇格
        from database import auto_promote_past_assignments
        auto_promote_past_assignments(student_id)

        selected = {
            "student_id": student_id,
            "date": target_date,
            "start_date": start_date,
            "subject_filter": subject_filter,
        }

        from excel_export import build_plan_data
        preview_data = build_plan_data(
            student_id, start_date, target_date,
            subject_filter if subject_filter else None)

    # 各生徒の教科リストを渡す
    conn2 = get_connection()
    c2 = conn2.cursor()
    c2.execute("SELECT student_id, subjects, plan_mode FROM students")
    student_subjects = {
        r["student_id"]: {
            "subjects": [s.strip() for s in r["subjects"].split(",")],
            "plan_mode": r["plan_mode"] or "all"
        }
        for r in c2.fetchall()
    }
    conn2.close()

    return render_template("preview.html", students=students,
                           preview_data=preview_data, selected=selected,
                           student_subjects=student_subjects)


# ─── 勉強時間・履歴 ────────────────────────────────────

@app.route("/schedule", methods=["GET", "POST"])
def schedule():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()

    if request.method == "POST":
        action = request.form.get("action")
        student_id = request.form["student_id"]
        if action == "save_base":
            for dow in range(7):
                minutes = int(request.form.get(f"dow_{dow}", 0))
                c.execute("""
                    INSERT INTO schedule_base (student_id, dow, available_minutes)
                    VALUES (?, ?, ?)
                    ON CONFLICT(student_id, dow) DO UPDATE SET available_minutes = ?
                """, (student_id, dow, minutes, minutes))
            conn.commit()
        elif action == "save_override":
            date_str = request.form["override_date"]
            minutes = int(request.form.get("override_minutes", 0))
            c.execute("""
                INSERT INTO schedule_override (student_id, date, available_minutes)
                VALUES (?, ?, ?)
                ON CONFLICT(student_id, date) DO UPDATE SET available_minutes = ?
            """, (student_id, date_str, minutes, minutes))
            conn.commit()
        conn.close()
        return redirect("/schedule")

    selected_student = request.args.get("student_id",
                        students[0]["student_id"] if students else None)
    base_schedule = {}
    if selected_student:
        c.execute("""
            SELECT dow, available_minutes FROM schedule_base WHERE student_id=?
        """, (selected_student,))
        base_schedule = {row["dow"]: row["available_minutes"] for row in c.fetchall()}
    conn.close()
    return render_template("schedule.html", students=students,
                           selected_student=selected_student,
                           base_schedule=base_schedule)


@app.route("/history")
def history():
    student_id = request.args.get("student_id")
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()
    conn.close()
    histories = get_plan_histories(student_id)
    return render_template("history.html", students=students,
                           histories=histories, selected_student=student_id)


@app.route("/history/download/<int:history_id>")
def history_download(history_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM plan_history WHERE history_id=?", (history_id,))
    row = c.fetchone()
    conn.close()
    if row and os.path.exists(row["excel_path"]):
        return send_file(row["excel_path"], as_attachment=True)
    return "ファイルが見つかりません", 404



@app.route("/export_pdf", methods=["POST"])
def export_pdf_route():
    from pdf_export import export_pdf
    student_id = request.form["student_id"]
    target_date = request.form["date"]
    start_date = request.form.get("start_date", "")
    if not start_date:
        start_date = date.today().isoformat()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM students WHERE student_id=?", (student_id,))
    row = c.fetchone()
    conn.close()
    student_name = row["name"] if row else student_id
    os.makedirs("plan_archives", exist_ok=True)
    output_path = os.path.join(
        "plan_archives", f"計画表_{student_name}_{target_date}.pdf")
    subject_filter = request.form.get("subject_filter", "")
    export_pdf(target_date, output_path,
               student_id=student_id, start_date=start_date,
               subject_filter=subject_filter if subject_filter else None)
    save_plan_history(student_id, start_date, target_date, output_path)
    return send_file(output_path, as_attachment=True)


@app.route("/problems/list")
def problems_list():
    conn = get_connection()
    c = conn.cursor()
    student_id = request.args.get("student_id", "")
    subject = request.args.get("subject", "")
    keyword = request.args.get("keyword", "")

    query = "SELECT * FROM problems WHERE 1=1"
    params = []

    if student_id:
        query = """SELECT DISTINCT p.* FROM problems p
                   JOIN assignments a ON p.problem_id = a.problem_id
                   WHERE a.student_id = ?"""
        params.append(student_id)
        if subject:
            query += " AND p.subject=?"
            params.append(subject)
        if keyword:
            query += " AND (p.textbook LIKE ? OR p.problem_number LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
    else:
        if subject:
            query += " AND subject=?"
            params.append(subject)
        if keyword:
            query += " AND (textbook LIKE ? OR problem_number LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])

    query += " ORDER BY problem_id DESC"
    c.execute(query, params)
    problems = c.fetchall()

    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()

    c.execute("SELECT DISTINCT subject FROM problems ORDER BY subject")
    subjects = [row["subject"] for row in c.fetchall()]
    conn.close()

    return render_template("problems_list.html",
                           problems=problems,
                           students=students,
                           subjects=subjects,
                           selected_student=student_id,
                           selected_subject=subject,
                           keyword=keyword)


@app.route("/class_schedule", methods=["GET", "POST"])
def class_schedule():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()

    if request.method == "POST":
        action = request.form.get("action")
        student_id = request.form["student_id"]
        subject = request.form["subject"]

        if action == "save_base":
            # 既存を削除して再登録
            c.execute("DELETE FROM class_schedule_base "
                      "WHERE student_id=? AND subject=?",
                      (student_id, subject))
            dows = request.form.getlist("dows")
            for dow in dows:
                c.execute("""
                    INSERT OR IGNORE INTO class_schedule_base
                    (student_id, subject, dow) VALUES (?, ?, ?)
                """, (student_id, subject, int(dow)))
            conn.commit()

        elif action == "save_override":
            next_date = request.form["next_class_date"]
            c.execute("""
                INSERT INTO class_schedule_override
                (student_id, subject, next_class_date)
                VALUES (?, ?, ?)
                ON CONFLICT(student_id, subject)
                DO UPDATE SET next_class_date=?
            """, (student_id, subject, next_date, next_date))
            conn.commit()

        elif action == "delete_override":
            c.execute("DELETE FROM class_schedule_override "
                      "WHERE student_id=? AND subject=?",
                      (student_id, subject))
            conn.commit()

        conn.close()
        return redirect(f"/class_schedule?student_id={student_id}")

    selected_student = request.args.get(
        "student_id", students[0]["student_id"] if students else None)

    # 現在の設定を取得
    base_schedule = {}
    override_schedule = {}
    student_subjects = []

    if selected_student:
        c.execute("SELECT subjects FROM students WHERE student_id=?",
                  (selected_student,))
        row = c.fetchone()
        if row:
            student_subjects = [s.strip()
                                 for s in row["subjects"].split(",")]

        c.execute("""
            SELECT subject, dow FROM class_schedule_base
            WHERE student_id=? ORDER BY subject, dow
        """, (selected_student,))
        for r in c.fetchall():
            base_schedule.setdefault(r["subject"], []).append(r["dow"])

        c.execute("""
            SELECT subject, next_class_date FROM class_schedule_override
            WHERE student_id=?
        """, (selected_student,))
        override_schedule = {r["subject"]: r["next_class_date"]
                             for r in c.fetchall()}

    conn.close()
    return render_template("class_schedule.html",
                           students=students,
                           selected_student=selected_student,
                           student_subjects=student_subjects,
                           base_schedule=base_schedule,
                           override_schedule=override_schedule)


@app.route("/problems/assign/<int:problem_id>", methods=["POST"])
def problem_assign(problem_id):
    student_id = request.form["student_id"]
    scheduled_date = request.form.get("scheduled_date", "").strip()
    category = request.form.get("category", "予習")
    conn = get_connection()
    c = conn.cursor()
    if scheduled_date:
        c.execute("""
            INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
            VALUES (?, ?, ?, ?)
        """, (student_id, problem_id, scheduled_date, category))
    else:
        # 日付未定の場合は遠い未来日付で仮登録（計画表には出ないが一覧には表示）
        c.execute("""
            INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
            VALUES (?, ?, ?, ?)
        """, (student_id, problem_id, "2099-12-31", category))
    conn.commit()
    conn.close()
    return redirect(f"/problems/edit/{problem_id}")


@app.route("/mastery/edit/<int:history_id>", methods=["POST"])
def mastery_edit(history_id):
    new_mastery = int(request.form["mastery"])
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT student_id, problem_id, date FROM history "
              "WHERE history_id=?", (history_id,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE history SET mastery=? WHERE history_id=?",
                  (new_mastery, history_id))
        conn.commit()
    conn.close()
    return redirect(request.referrer or "/record/list")


@app.route("/assignment/category/<int:student_id_dummy>", methods=["POST"])
def assignment_category_edit():
    pass


@app.route("/assignments/list")
def assignments_list():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()
    student_id = request.args.get(
        "student_id", students[0]["student_id"] if students else None)
    assignments = []
    if student_id:
        c.execute("""
            SELECT a.assignment_id, a.category, a.scheduled_date,
                   p.problem_id, p.subject, p.textbook, p.problem_number,
                   p.importance, p.review_value,
                   (SELECT mastery FROM history h
                    WHERE h.student_id = a.student_id
                    AND h.problem_id = a.problem_id
                    ORDER BY h.date DESC LIMIT 1) as mastery
            FROM assignments a
            JOIN problems p ON a.problem_id = p.problem_id
            WHERE a.student_id = ?
            ORDER BY a.scheduled_date, p.subject
        """, (student_id,))
        assignments = c.fetchall()
    conn.close()
    return render_template("assignments_list.html",
                           students=students,
                           assignments=assignments,
                           selected_student=student_id)


@app.route("/assignments/update", methods=["POST"])
def assignment_update():
    assignment_id = int(request.form["assignment_id"])
    category = request.form.get("category", "")
    scheduled_date = request.form.get("scheduled_date", "")
    conn = get_connection()
    c = conn.cursor()
    if category and scheduled_date:
        c.execute("UPDATE assignments SET category=?, scheduled_date=? "
                  "WHERE assignment_id=?",
                  (category, scheduled_date, assignment_id))
    elif category:
        c.execute("UPDATE assignments SET category=? WHERE assignment_id=?",
                  (category, assignment_id))
    elif scheduled_date:
        c.execute("UPDATE assignments SET scheduled_date=? "
                  "WHERE assignment_id=?",
                  (scheduled_date, assignment_id))
    conn.commit()
    conn.close()
    student_id = request.form.get("student_id", "")
    return redirect(f"/assignments/list?student_id={student_id}#row-{assignment_id}")


@app.route("/assignments/delete/<int:assignment_id>", methods=["POST"])
def assignment_delete(assignment_id):
    student_id = request.form.get("student_id", "")
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM assignments WHERE assignment_id=?", (assignment_id,))
    conn.commit()
    conn.close()
    return redirect(f"/assignments/list?student_id={student_id}")


@app.route("/history/delete/<int:history_id>", methods=["POST"])
def history_delete(history_id):
    reset_assignments = request.form.get("reset_assignments") == "1"
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM plan_history WHERE history_id=?", (history_id,))
    row = c.fetchone()
    if row and reset_assignments:
        student_id = row["student_id"]
        start_date = row["start_date"]
        end_date = row["end_date"]

        # 当該期間の授業記録（historyテーブル）のみ削除
        # ※problemsテーブルは削除しない
        c.execute("""
            DELETE FROM history
            WHERE student_id=?
            AND date BETWEEN ? AND ?
        """, (student_id, start_date, end_date))

        # 当該期間の出題予定（assignmentsテーブル）を削除
        # → 授業記録が消えたので、出題予定も初期状態に戻す
        c.execute("""
            DELETE FROM assignments
            WHERE student_id=?
            AND scheduled_date BETWEEN ? AND ?
        """, (student_id, start_date, end_date))

        # 問題マスタに登録された問題を「予習未定」として出題予定に戻す
        # （assignments に存在しない問題のみ）
        c.execute("""
            INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
            SELECT ?, p.problem_id, ?, '復習'
            FROM problems p
            WHERE p.problem_id IN (
                SELECT DISTINCT problem_id FROM history
                WHERE student_id=?
            )
            AND p.problem_id NOT IN (
                SELECT problem_id FROM assignments WHERE student_id=?
            )
        """, (student_id, start_date, student_id, student_id))

    # Excelファイルを削除（ファイルのみ・DBレコードは残す）
    if row:
        try:
            if os.path.exists(row["excel_path"]):
                os.remove(row["excel_path"])
        except PermissionError:
            pass  # ファイルが開かれている場合は削除をスキップ

    c.execute("DELETE FROM plan_history WHERE history_id=?", (history_id,))
    conn.commit()
    conn.close()
    return redirect("/history")


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

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
