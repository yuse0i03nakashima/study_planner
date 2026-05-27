from flask import Flask, render_template, request, redirect, send_file, jsonify, flash, url_for, get_flashed_messages
from database import (init_db, get_connection, calc_new_mastery,
                      update_assignments_after_record, get_plan, get_schedule,
                      save_plan_history, get_plan_histories)
from excel_export import export_excel
from datetime import date, timedelta
import os

app = Flask(__name__)

# カテゴリ/記録種別の英語化フィルター
CAT_EN = {
    "予習": "New", "復習": "Recall", "定着": "Drill",
    "再定着": "Reinforce", "記録": "Record", "手動修正": "Manual",
    "自動登録": "Auto"
}
SCORE_EN = {
    5: "Perfect", 4: "Good", 3: "Review", 2: "Retry", 1: "Failed"
}

@app.template_filter("cat_en")
def cat_en_filter(v):
    return CAT_EN.get(v, v)

@app.template_filter("score_en")
def score_en_filter(v):
    try:
        return SCORE_EN.get(int(v), str(v))
    except Exception:
        return str(v) if v else "—"

app.secret_key = "study-planner-secret-2024"


@app.route("/")
def index():
    return render_template("index.html")


# ─── 問題マスタ ────────────────────────────────────────

@app.route("/problems", methods=["GET", "POST"])
def problems():
    conn = get_connection()
    c = conn.cursor()

    if request.method == "POST":
        # textbook_idからsubject/textbook名を取得
        textbook_id = request.form.get("textbook_id")
        if textbook_id:
            c.execute("SELECT subject, name FROM textbooks WHERE textbook_id=?",
                      (textbook_id,))
            tb_row = c.fetchone()
            subject  = tb_row["subject"] if tb_row else request.form.get("subject", "")
            textbook = tb_row["name"]    if tb_row else ""
        else:
            subject  = request.form.get("subject", "")
            textbook = request.form.get("textbook", "")

        # order_in_textbook: 入力があればそれを使い, なければ同テキスト最大+1
        total_minutes_raw = request.form.get("total_minutes", "").strip()
        total_minutes = int(total_minutes_raw) if total_minutes_raw else None

        order_input = request.form.get("order_in_textbook", "").strip()
        if order_input:
            order_in_textbook = int(order_input)
        else:
            c.execute("""
                SELECT MAX(order_in_textbook) as m FROM problems WHERE textbook_id=?
            """, (textbook_id,))
            r = c.fetchone()
            order_in_textbook = (r["m"] if r and r["m"] else 0) + 1

        # section_id: 選択があればそれを使い, なければ前の問題と同じSectionを使用
        section_id_raw = request.form.get("section_id", "").strip()
        if section_id_raw:
            section_id_val = int(section_id_raw)
        else:
            # 同テキスト内の直前の問題のsection_idを取得
            c.execute("""
                SELECT section_id FROM problems
                WHERE textbook_id=? AND section_id IS NOT NULL
                ORDER BY order_in_textbook DESC, problem_id DESC LIMIT 1
            """, (textbook_id,))
            prev = c.fetchone()
            section_id_val = prev["section_id"] if prev else None

        c.execute("""
            INSERT INTO problems
            (subject, textbook, textbook_id, problem_number,
             importance, difficulty, review_value,
             estimated_minutes, instruction, type, order_in_textbook,
             total_minutes, section_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            subject, textbook, textbook_id,
            request.form["problem_number"],
            request.form["importance"],
            request.form["difficulty"],
            request.form["review_value"],
            request.form["estimated_minutes"],
            request.form.get("instruction", ""),
            "標準",
            order_in_textbook,
            total_minutes,
            section_id_val
        ))
        conn.commit()
        problem_id = c.lastrowid

        # 生徒×出題予定の登録
        from database import get_auto_next_class_date
        student_ids    = request.form.getlist("student_ids")
        scheduled_date = request.form.get("scheduled_date", "").strip()
        category       = request.form.get("category", "New")

        # Students未選択の場合はテキストに紐づく生徒を自動対象にする
        if not student_ids:
            c.execute(
                "SELECT student_id FROM student_textbooks WHERE textbook_id=?",
                (textbook_id,))
            student_ids = [r["student_id"] for r in c.fetchall()]

        undecided = request.form.get("undecided") == "1"
        for sid in student_ids:
            if undecided:
                # 授業日未定
                effective_date = "2099-12-31"
            elif not scheduled_date:
                # 未指定なら授業曜日から自動計算
                auto_date = get_auto_next_class_date(sid, subject)
                effective_date = auto_date if auto_date else "2099-12-31"
            else:
                effective_date = scheduled_date
            # student_textbooksに紐づけ
            c.execute("""
                INSERT OR IGNORE INTO student_textbooks (student_id, textbook_id)
                VALUES (?, ?)
            """, (sid, textbook_id))
            # assignmentsに登録
            c.execute("""
                INSERT INTO assignments
                (student_id, problem_id, scheduled_date, category)
                VALUES (?, ?, ?, ?)
            """, (sid, problem_id, effective_date, category))

        conn.commit()
        conn.close()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "ok": True,
                "problem_id": problem_id,
                "order_in_textbook": order_in_textbook,
                "subject": subject,
                "textbook": textbook,
                "problem_number": request.form["problem_number"],
                "importance": int(request.form["importance"]),
                "difficulty": int(request.form["difficulty"]),
                "review_value": int(request.form["review_value"]),
                "estimated_minutes": int(request.form["estimated_minutes"]),
                "total_minutes": total_minutes,
                "instruction": request.form.get("instruction", ""),
            })
        return redirect("/problems")

    # GET
    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()

    c.execute("""
        SELECT p.problem_id, p.subject, p.textbook, p.problem_number,
               p.importance, p.difficulty, p.review_value,
               p.estimated_minutes, p.instruction, p.order_in_textbook
        FROM problems p
        ORDER BY p.problem_id DESC LIMIT 50
    """)
    probs = c.fetchall()

    # テキスト一覧(教科でフィルタできるようにdata-subjectを付与)
    c.execute("""
        SELECT t.textbook_id, t.name, t.subject,
               s.name as series_name
        FROM textbooks t
        LEFT JOIN series s ON t.series_id = s.series_id
        ORDER BY t.subject, s.name, t.name
    """)
    textbooks_list = c.fetchall()

    # 教科一覧(studentsのsubjectsから生成)
    c.execute("SELECT DISTINCT subjects FROM students ORDER BY subjects")
    all_subjects = []
    for row in c.fetchall():
        for subj in row["subjects"].split(","):
            s = subj.strip()
            if s and s not in all_subjects:
                all_subjects.append(s)
    all_subjects = sorted(all_subjects)

    conn.close()
    return render_template("problems.html",
                           students=students,
                           problems=probs,
                           textbooks=textbooks_list,
                           all_subjects=all_subjects)

@app.route("/problems/edit/<int:problem_id>", methods=["GET", "POST"])
def problem_edit(problem_id):
    conn = get_connection()
    c = conn.cursor()
    if request.method == "POST":
        textbook_id = request.form.get("textbook_id")
        # textbook_idからsubjectとtextbook名を取得
        conn2 = get_connection()
        c2 = conn2.cursor()
        if textbook_id:
            c2.execute("SELECT subject, name FROM textbooks WHERE textbook_id=?",
                       (textbook_id,))
            tb_row = c2.fetchone()
            subject = tb_row["subject"] if tb_row else request.form.get("subject", "")
            textbook = tb_row["name"] if tb_row else ""
        else:
            subject = request.form.get("subject", "")
            textbook = request.form.get("textbook", "")
        conn2.close()
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
        from database import (calc_new_mastery_v2, update_assignments_after_record,
                               score_to_correct)
        student_id = request.form["student_id"]
        problem_id = request.form["problem_id"]
        record_date = request.form["record_date"]
        score = int(request.form.get("score", 5))
        correct = score_to_correct(score)
        new_mastery = calc_new_mastery_v2(student_id, problem_id, score, record_date)
        c.execute("""
            INSERT INTO history
            (student_id, problem_id, date, correct, mastery, category, score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (student_id, problem_id, record_date, correct, new_mastery, "記録", score))
        conn.commit()
        conn.close()
        update_assignments_after_record(student_id, problem_id, record_date, new_mastery)
        score_label = {5: "Perfect", 4: "Good", 3: "Review",
                       2: "Retry", 1: "Failed"}
        flash(
            f"記録しました(評価:{score}／{score_label[score]}"
            f"　習熟度:{'★' * new_mastery})",
            "success"
        )
        return redirect("/record")

    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()

    # 今期の問題(assignments)を優先表示
    c.execute("""
        SELECT DISTINCT p.problem_id, p.subject, p.textbook, p.problem_number,
               a.student_id as assigned_student,
               a.scheduled_date, a.category
        FROM problems p
        LEFT JOIN assignments a ON p.problem_id = a.problem_id
          AND a.scheduled_date != '2099-12-31'
        ORDER BY
          CASE WHEN a.scheduled_date IS NOT NULL THEN 0 ELSE 1 END,
          a.scheduled_date,
          p.subject, p.textbook, p.problem_id
    """)
    problems = c.fetchall()
    conn.close()
    today = date.today().isoformat()
    return render_template("record.html", students=students,
                           problems=problems, today=today)


@app.route("/get_assignments")
def get_assignments():
    student_id = request.args.get("student_id")
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT a.assignment_id, a.problem_id, a.category, a.scheduled_date,
               p.subject, p.textbook, p.problem_number, p.importance, p.difficulty,
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
               h.score,
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
    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()
    conn.close()
    return render_template("students.html", students=students)

@app.route("/export", methods=["GET", "POST"])
def export():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()
    conn.close()

    if request.method == "POST":
        student_id = request.form["student_id"]
        _td = request.form.get("end_date") or request.form.get("date") or ""
        target_date = _td if _td else (date.today() + timedelta(days=7)).isoformat()
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
        subject_filter = request.form.get("subject_filter", "")
        save_plan_history(student_id, start_date, target_date, output_path,
                          pdf_path="", subject=subject_filter)
        return send_file(output_path, as_attachment=True)

    return render_template("export.html", students=students)


@app.route("/preview", methods=["GET", "POST"])
def preview():
    from database import get_auto_next_class_date
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()

    # 各生徒の教科/plan_mode
    c.execute("SELECT student_id, subjects, plan_mode FROM students")
    student_subjects = {
        r["student_id"]: {
            "subjects": [s.strip() for s in r["subjects"].split(",")],
            "plan_mode": r["plan_mode"] or "all"
        }
        for r in c.fetchall()
    }
    conn.close()

    preview_data = None
    selected = {}

    if request.method == "POST":
        student_id    = request.form.get("student_id", "")
        subject_filter = request.form.get("subject_filter", "").strip()
        start_date    = request.form.get("start_date", "").strip()
        end_date      = request.form.get("end_date", "").strip()

        if not start_date:
            start_date = date.today().isoformat()

        # end_dateが空欄の場合は次回授業日を自動計算
        if not end_date:
            target_subject = subject_filter if subject_filter else None
            if target_subject:
                next_cls = get_auto_next_class_date(student_id, target_subject)
            else:
                # 全教科の中で最も近い次回授業日
                info = student_subjects.get(student_id, {})
                subjs = info.get("subjects", [])
                dates = []
                for subj in subjs:
                    d = get_auto_next_class_date(student_id, subj)
                    if d:
                        dates.append(d)
                next_cls = min(dates) if dates else None
            end_date = next_cls if next_cls else (
                date.fromisoformat(start_date) + timedelta(days=7)).isoformat()

        selected = {
            "student_id":     student_id,
            "mode":           "per_subject" if subject_filter else "all",
            "subject_filter": subject_filter,
            "start_date":     start_date,
            "end_date":       end_date,
        }

        from planner import build_plan_data
        action = request.form.get("action", "preview")

        section_filters = request.form.getlist("section_filter")
        section_ids = [int(s) for s in section_filters if s.strip()]
        if action == "excel":
            from excel_export import export_excel
            path = export_excel(student_id, start_date, end_date,
                                subject_filter if subject_filter else None,
                                section_ids=section_ids if section_ids else None)
            if path:
                save_plan_history(student_id, start_date, end_date,
                                  excel_path=path, pdf_path="",
                                  subject=subject_filter)
                import subprocess
                subprocess.Popen(["start", "", path], shell=True)
            return redirect("/preview")

        if action == "pdf":
            from pdf_export import export_pdf
            path = export_pdf(student_id, start_date, end_date,
                              subject_filter if subject_filter else None,
                              section_ids=section_ids if section_ids else None)
            if path:
                save_plan_history(student_id, start_date, end_date,
                                  excel_path="", pdf_path=path,
                                  subject=subject_filter)
                import subprocess
                subprocess.Popen(["start", "", path], shell=True)
            return redirect("/preview")

        section_filters = request.form.getlist("section_filter")
        section_ids = [int(s) for s in section_filters if s.strip()]
        preview_data = build_plan_data(
            student_id, start_date, end_date,
            subject_filter if subject_filter else None,
            section_ids=section_ids if section_ids else None)

    # テンプレート変数を整理
    selected_student     = selected.get("student_id",
                           students[0]["student_id"] if students else "")
    selected_mode        = selected.get("mode", "all")
    selected_subject     = selected.get("subject_filter", "")
    start_date           = selected.get("start_date", date.today().isoformat())
    end_date             = selected.get("end_date", "")
    selected_student_name = ""
    subjects = []
    for s in students:
        if s["student_id"] == selected_student:
            selected_student_name = s["name"]
            info = student_subjects.get(selected_student, {})
            subjects = info.get("subjects", [])
            break

    # Section一覧を取得してプレビューに渡す
    _sec_filters = request.form.getlist("section_filter") if request.method == "POST" else []
    _conn_sec = get_connection()
    _c_sec = _conn_sec.cursor()
    if selected_subject and selected_student:
        _c_sec.execute("""
            SELECT DISTINCT ts.section_id, ts.name, ts.order_index,
                   t.name as textbook_name
            FROM textbook_sections ts
            JOIN textbooks t ON ts.textbook_id = t.textbook_id
            JOIN problems p ON p.section_id = ts.section_id
            JOIN assignments a ON a.problem_id = p.problem_id
            WHERE t.subject=? AND a.student_id=?
            ORDER BY t.name, ts.order_index
        """, (selected_subject, selected_student))
    else:
        _c_sec.execute("SELECT section_id, name, order_index, '' as textbook_name FROM textbook_sections LIMIT 0")
    _selected_sections = [dict(r) for r in _c_sec.fetchall()]
    _conn_sec.close()

    return render_template("preview.html",
                           students=students,
                           preview_data=preview_data,
                           selected=selected,
                           student_subjects=student_subjects,
                           selected_student=selected_student,
                           selected_student_name=selected_student_name,
                           selected_mode=selected_mode,
                           selected_subject=selected_subject,
                           start_date=start_date,
                           end_date=end_date,
                           subjects=subjects,
                           selected_sections=_selected_sections,
                           selected_section_ids=_sec_filters,
                           unassigned=preview_data.get("unassigned", {}) if preview_data else {})


@app.route("/schedule", methods=["GET", "POST"])
def schedule():
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()
    if not students:
        conn.close()
        return render_template("schedule.html", students=[],
                               selected_student="", base_schedule={}, overrides=[])

    selected_student = request.args.get("student_id") or                        students[0]["student_id"]

    # ベーススケジュール: available_minutesカラム
    c.execute("""SELECT dow, available_minutes FROM schedule_base
                 WHERE student_id=?""", (selected_student,))
    base_schedule = {row["dow"]: row["available_minutes"] for row in c.fetchall()}

    # オーバーライド
    c.execute("""SELECT date, available_minutes FROM schedule_override
                 WHERE student_id=? ORDER BY date""", (selected_student,))
    overrides = c.fetchall()

    conn.close()
    return render_template("schedule.html",
                           students=students,
                           selected_student=selected_student,
                           base_schedule=base_schedule,
                           overrides=overrides)

@app.route("/history")
def history():
    student_id = request.args.get("student_id", "")
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()
    conn.close()
    all_histories   = get_plan_histories(student_id)
    confirmed       = [h for h in all_histories if h["confirmed"] == 1]
    unconfirmed     = [h for h in all_histories if h["confirmed"] == 0]
    return render_template("history.html",
                           students=students,
                           confirmed=confirmed,
                           unconfirmed=unconfirmed,
                           selected_student=student_id)

@app.route("/history/preview/<int:history_id>")
def history_preview(history_id):
    """確定済み計画表のプレビュー(JSON返却)"""
    import json as _json
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT ph.*, s.name as student_name
                 FROM plan_history ph
                 JOIN students s ON ph.student_id=s.student_id
                 WHERE ph.history_id=?""", (history_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "not found"}), 404
    plan_data = []
    if row["plan_data"]:
        try:
            plan_data = _json.loads(row["plan_data"])
        except Exception:
            plan_data = []
    return jsonify({
        "history_id":   history_id,
        "student_name": row["student_name"],
        "start_date":   row["start_date"],
        "end_date":     row["end_date"],
        "subject":      row["subject"],
        "generated_date": row["generated_date"],
        "plan":         plan_data
    })


@app.route("/history/download/<int:history_id>")
def history_download(history_id):
    file_type = request.args.get("type", "excel")
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM plan_history WHERE history_id=?", (history_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return "Record not found", 404
    path = row["pdf_path"] if file_type == "pdf" else row["excel_path"]
    if path and os.path.exists(path):
        return send_file(path, as_attachment=True)
    # もう一方を試みる
    fallback = row["excel_path"] if file_type == "pdf" else row["pdf_path"]
    if fallback and os.path.exists(fallback):
        return send_file(fallback, as_attachment=True)
    return "File not found", 404



@app.route("/export_pdf", methods=["POST"])
def export_pdf_route():
    from pdf_export import export_pdf
    student_id = request.form["student_id"]
    target_date = request.form.get("end_date") or request.form.get("date") or ""
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
    subject_filter_pdf = request.form.get("subject_filter", "")
    save_plan_history(student_id, start_date, target_date,
                      excel_path="", pdf_path=output_path,
                      subject=subject_filter_pdf)
    return send_file(output_path, as_attachment=True)


@app.route("/problems/list")
def problems_list():
    conn = get_connection()
    c = conn.cursor()

    subject     = request.args.get("subject", "")
    textbook_id = request.args.get("textbook_id", "")

    # 問題クエリ
    query = """
        SELECT p.problem_id, p.subject, p.textbook, p.textbook_id,
               p.problem_number, p.importance, p.difficulty, p.review_value,
               p.estimated_minutes, p.total_minutes, p.instruction, p.order_in_textbook
        FROM problems p
        WHERE 1=1
    """
    params = []
    if subject:
        query += " AND p.subject=?"
        params.append(subject)
    if textbook_id:
        query += " AND p.textbook_id=?"
        params.append(textbook_id)
    query += " ORDER BY p.order_in_textbook, p.problem_id"
    c.execute(query, params)
    problems = c.fetchall()

    # フィルター用データ
    c.execute("SELECT DISTINCT subject FROM problems ORDER BY subject")
    all_subjects = [r["subject"] for r in c.fetchall()]

    # 教科フィルターがある場合はそのテキストのみ, なければ全テキスト
    if subject:
        c.execute("""
            SELECT t.textbook_id, t.name, t.subject
            FROM textbooks t
            WHERE t.subject=?
            ORDER BY t.name
        """, (subject,))
    else:
        c.execute("""
            SELECT t.textbook_id, t.name, t.subject
            FROM textbooks t
            ORDER BY t.subject, t.name
        """)
    all_textbooks = c.fetchall()

    # 生徒一覧(出題予定追加モーダル用)
    c.execute("SELECT * FROM students ORDER BY student_id")
    students_list = c.fetchall()

    conn.close()
    return render_template("problems_list.html",
                           problems=problems,
                           all_subjects=all_subjects,
                           all_textbooks=all_textbooks,
                           selected_subject=subject,
                           selected_textbook=textbook_id,
                           students=students_list)

@app.route("/class_schedule", methods=["GET", "POST"])
def class_schedule():
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()

    # schedule_map: {student_id: {subject: {dow: bool}}}
    # class_schedule_baseは (student_id, subject, dow) の行ごと登録
    schedule_map = {}
    c.execute("SELECT student_id, subject, dow FROM class_schedule_base")
    for row in c.fetchall():
        sid  = row["student_id"]
        subj = row["subject"]
        dow  = row["dow"]
        if sid  not in schedule_map: schedule_map[sid]  = {}
        if subj not in schedule_map[sid]: schedule_map[sid][subj] = {}
        schedule_map[sid][subj][dow] = True

    # next_class_map: {student_id: {subject: date_str}}
    next_class_map = {}
    c.execute("SELECT student_id, subject, next_class_date FROM class_schedule_override")
    for row in c.fetchall():
        sid  = row["student_id"]
        subj = row["subject"]
        if sid not in next_class_map: next_class_map[sid] = {}
        next_class_map[sid][subj] = row["next_class_date"] or ""

    conn.close()
    return render_template("class_schedule.html",
                           students=students,
                           schedule_map=schedule_map,
                           next_class_map=next_class_map)

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
        # 日付未定の場合は遠い未来日付で仮登録(計画表には出ないが一覧には表示)
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
                   p.importance, p.difficulty, p.review_value,
                   p.estimated_minutes, p.total_minutes,
                   (SELECT mastery FROM history h
                    WHERE h.student_id = a.student_id
                    AND h.problem_id = a.problem_id
                    ORDER BY h.date DESC, h.history_id DESC LIMIT 1) as mastery
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

        # 当該期間の授業記録(historyテーブル)のみ削除
        # ※problemsテーブルは削除しない
        c.execute("""
            DELETE FROM history
            WHERE student_id=?
            AND date BETWEEN ? AND ?
        """, (student_id, start_date, end_date))

        # 当該期間の出題予定(assignmentsテーブル)を削除
        # → 授業記録が消えたので, 出題予定も初期状態に戻す
        c.execute("""
            DELETE FROM assignments
            WHERE student_id=?
            AND scheduled_date BETWEEN ? AND ?
        """, (student_id, start_date, end_date))

        # 問題マスタに登録された問題を"予習未定"として出題予定に戻す
        # (assignments に存在しない問題のみ)
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

    # Excelファイルを削除(ファイルのみ/DBレコードは残す)
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
    if not students:
        conn.close()
        return render_template("schedule_subject.html", students=[],
                               selected_student="", subjects=[],
                               subject_base={}, subject_overrides={})

    selected_student = request.args.get("student_id") or                        students[0]["student_id"]

    # 教科一覧
    c.execute("SELECT subjects FROM students WHERE student_id=?",
              (selected_student,))
    row = c.fetchone()
    subjects = [s.strip() for s in row["subjects"].split(",")] if row else []

    # ベーススケジュール
    subject_base = {}
    c.execute("""SELECT subject, dow, available_minutes FROM schedule_base_subject
                 WHERE student_id=?""", (selected_student,))
    for r in c.fetchall():
        if selected_student not in subject_base:
            subject_base[selected_student] = {}
        if r["subject"] not in subject_base[selected_student]:
            subject_base[selected_student][r["subject"]] = {}
        subject_base[selected_student][r["subject"]][r["dow"]] = r["available_minutes"]

    # オーバーライド
    subject_overrides = {}
    c.execute("""SELECT subject, date, available_minutes FROM schedule_override_subject
                 WHERE student_id=? ORDER BY subject, date""", (selected_student,))
    for r in c.fetchall():
        if selected_student not in subject_overrides:
            subject_overrides[selected_student] = {}
        if r["subject"] not in subject_overrides[selected_student]:
            subject_overrides[selected_student][r["subject"]] = []
        subject_overrides[selected_student][r["subject"]].append(r)

    conn.close()
    return render_template("schedule_subject.html",
                           students=students,
                           selected_student=selected_student,
                           subjects=subjects,
                           subject_base=subject_base,
                           subject_overrides=subject_overrides)

@app.route("/textbooks")
def textbooks():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT t.textbook_id, t.name, t.subject,
               s.name as series_name,
               COUNT(DISTINCT p.problem_id) as problem_count,
               GROUP_CONCAT(DISTINCT st.name) as students
        FROM textbooks t
        LEFT JOIN series s ON t.series_id = s.series_id
        LEFT JOIN problems p ON t.textbook_id = p.textbook_id
        LEFT JOIN student_textbooks stb ON t.textbook_id = stb.textbook_id
        LEFT JOIN students st ON stb.student_id = st.student_id
        GROUP BY t.textbook_id
        ORDER BY t.subject, s.name, t.name
    """)
    tb_list = c.fetchall()
    c.execute("""
        SELECT s.series_id, s.name,
               COUNT(t.textbook_id) as textbook_count
        FROM series s
        LEFT JOIN textbooks t ON s.series_id = t.series_id
        GROUP BY s.series_id ORDER BY s.name
    """)
    series_list = c.fetchall()
    c.execute("SELECT DISTINCT subjects FROM students ORDER BY subjects")
    all_subjects_raw = c.fetchall()
    all_subjects = []
    for row in all_subjects_raw:
        for subj in row["subjects"].split(","):
            s = subj.strip()
            if s and s not in all_subjects:
                all_subjects.append(s)
    # 全生徒
    c.execute("SELECT student_id, name FROM students ORDER BY student_id")
    all_students = c.fetchall()

    # 各テキストの紐づき生徒IDリストを付与
    tb_list_with_students = []
    for t in tb_list:
        c.execute("SELECT student_id FROM student_textbooks WHERE textbook_id=?",
                  (t["textbook_id"],))
        sids = [r["student_id"] for r in c.fetchall()]
        tb_list_with_students.append({**dict(t), "student_ids_list": sids})

    conn.close()
    return render_template("textbooks.html",
                           textbooks=tb_list_with_students,
                           series_list=series_list,
                           all_subjects=sorted(all_subjects),
                           all_students=all_students)


@app.route("/textbooks/series/add", methods=["POST"])
def textbook_series_add():
    name = request.form["name"].strip()
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO series (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()
    return redirect("/textbooks")


@app.route("/textbooks/series/delete/<int:series_id>", methods=["POST"])
def textbook_series_delete(series_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE textbooks SET series_id=NULL WHERE series_id=?", (series_id,))
    c.execute("DELETE FROM series WHERE series_id=?", (series_id,))
    conn.commit()
    conn.close()
    return redirect("/textbooks")


@app.route("/textbooks/add", methods=["POST"])
def textbook_add():
    series_id = request.form.get("series_id") or None
    name = request.form["name"].strip()
    subject = request.form["subject"]
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO textbooks (series_id, name, subject) VALUES (?, ?, ?)
    """, (series_id, name, subject))
    conn.commit()
    conn.close()
    return redirect("/textbooks")


@app.route("/textbooks/delete/<int:textbook_id>", methods=["POST"])
def textbook_delete(textbook_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as cnt FROM problems WHERE textbook_id=?",
              (textbook_id,))
    if c.fetchone()["cnt"] > 0:
        conn.close()
        return "Cannot delete: this textbook has registered problems.", 400
    c.execute("DELETE FROM student_textbooks WHERE textbook_id=?", (textbook_id,))
    c.execute("DELETE FROM textbooks WHERE textbook_id=?", (textbook_id,))
    conn.commit()
    conn.close()
    return redirect("/textbooks")


@app.route("/textbooks/<int:textbook_id>/sections", methods=["GET", "POST"])
def textbook_sections(textbook_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT t.*, s.name as series_name FROM textbooks t LEFT JOIN series s ON t.series_id = s.series_id WHERE t.textbook_id=?", (textbook_id,))
    textbook = c.fetchone()
    if not textbook:
        conn.close()
        return "Textbook not found", 404

    if request.method == "POST":
        name = request.form["name"].strip()
        order_index = int(request.form.get("order_index", 0))
        c.execute("""
            INSERT INTO textbook_sections (textbook_id, name, order_index)
            VALUES (?, ?, ?)
        """, (textbook_id, name, order_index))
        conn.commit()
        return redirect(f"/textbooks/{textbook_id}/sections")

    c.execute("""
        SELECT s.*, COUNT(p.problem_id) as problem_count
        FROM textbook_sections s
        LEFT JOIN problems p ON s.section_id = p.section_id
        WHERE s.textbook_id=?
        GROUP BY s.section_id
        ORDER BY s.order_index, s.section_id
    """, (textbook_id,))
    sections = c.fetchall()

    # テキスト内の問題一覧
    c.execute("""
        SELECT problem_id, problem_number, subject,
               importance, difficulty, review_value, order_in_textbook
        FROM problems WHERE textbook_id=?
        ORDER BY order_in_textbook, problem_id
    """, (textbook_id,))
    problems = c.fetchall()
    conn.close()
    return render_template("sections.html",
                           textbook=textbook,
                           sections=sections,
                           problems=problems)

@app.route("/textbooks/sections/delete/<int:section_id>", methods=["POST"])
def section_delete(section_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT textbook_id FROM textbook_sections WHERE section_id=?",
              (section_id,))
    row = c.fetchone()
    textbook_id = row["textbook_id"] if row else 0
    c.execute("UPDATE problems SET section_id=NULL WHERE section_id=?", (section_id,))
    c.execute("DELETE FROM textbook_sections WHERE section_id=?", (section_id,))
    conn.commit()
    conn.close()
    return redirect(f"/textbooks/{textbook_id}/sections")


@app.route("/assignments/bulk_update", methods=["POST"])
def assignments_bulk_update():
    import json as _json
    data = request.get_json()
    updates = data.get("updates", [])
    conn = get_connection()
    c = conn.cursor()
    for upd in updates:
        assignment_id = upd.get("assignment_id")
        category = upd.get("category", "")
        scheduled_date = upd.get("scheduled_date", "").strip()
        if not scheduled_date:
            scheduled_date = "2099-12-31"
        if category and assignment_id:
            c.execute("""
                UPDATE assignments
                SET category=?, scheduled_date=?
                WHERE assignment_id=?
            """, (category, scheduled_date, assignment_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "updated": len(updates)})


@app.route("/mastery/bulk_update", methods=["POST"])
def mastery_bulk_update():
    import json as _json
    data = request.get_json()
    updates = data.get("updates", [])
    conn = get_connection()
    c = conn.cursor()
    for upd in updates:
        history_id = upd.get("history_id")
        mastery = upd.get("mastery")
        if history_id and mastery:
            c.execute("UPDATE history SET mastery=? WHERE history_id=?",
                      (mastery, history_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "updated": len(updates)})


@app.route("/problems/update_field", methods=["POST"])
def problem_update_field():
    """問題固有フィールドをインライン編集で更新する"""
    data = request.get_json()
    problem_id = data.get("problem_id")
    field      = data.get("field")
    value      = data.get("value")

    allowed = {"importance", "difficulty", "review_value", "estimated_minutes",
               "order_in_textbook", "total_minutes", "instruction", "problem_number"}
    if field not in allowed:
        return jsonify({"ok": False, "message": "Invalid field"}), 400

    # フィールドごとのバリデーションと型変換
    try:
        if field in ("importance", "difficulty", "review_value"):
            value = int(value)
            if not (1 <= value <= 5):
                raise ValueError
        elif field == "estimated_minutes":
            value = int(value)
            if not (5 <= value <= 300):
                raise ValueError
        elif field == "order_in_textbook":
            value = int(value)
            if not (1 <= value <= 9999):
                raise ValueError
        elif field == "total_minutes":
            # 空欄/null/"—"はNULLに
            if value is None or value == "" or value == "—":
                value = None
            else:
                value = int(value)
                if value < 5:
                    raise ValueError
        # instruction/problem_numberはそのまま文字列
    except (ValueError, TypeError):
        return jsonify({"ok": False, "message": "Invalid value"}), 400

    conn = get_connection()
    c = conn.cursor()
    c.execute(f"UPDATE problems SET {field}=? WHERE problem_id=?",
              (value, problem_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/mastery/single_update", methods=["POST"])
def mastery_single_update():
    """Assignmentsページから習熟度を単体更新する"""
    data = request.get_json()
    student_id = data.get("student_id")
    problem_id = data.get("problem_id")
    mastery = data.get("mastery")
    if not student_id or problem_id is None or mastery is None:
        return jsonify({"ok": False, "message": "missing params"}), 400
    problem_id = int(problem_id)
    mastery = int(mastery)
    today = __import__("datetime").date.today().isoformat()
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO history (student_id, problem_id, date, correct, mastery, category)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (student_id, problem_id, today, 1, mastery, "手動修正"))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/problems/update_instruction", methods=["POST"])
def problem_update_instruction():
    data = request.get_json()
    problem_id = data.get("problem_id")
    instruction = data.get("instruction", "")
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE problems SET instruction=? WHERE problem_id=?",
              (instruction, problem_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})


@app.route("/problems/update_number", methods=["POST"])
def problem_update_number():
    data = request.get_json()
    problem_id = data.get("problem_id")
    value = data.get("value", "").strip()
    if not value:
        return jsonify({"status": "error", "message": "Empty value"}), 400
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE problems SET problem_number=? WHERE problem_id=?",
              (value, problem_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})









@app.route("/schedule/base", methods=["POST"])
def schedule_base_save():
    student_id = request.form.get("student_id")
    conn = get_connection()
    c = conn.cursor()
    for dow in ["mon","tue","wed","thu","fri","sat","sun"]:
        minutes = int(request.form.get(dow, 0))
        c.execute("""
            INSERT OR REPLACE INTO schedule_base
            (student_id, dow, available_minutes) VALUES (?, ?, ?)
        """, (student_id, dow, minutes))
    conn.commit()
    conn.close()
    return redirect(f"/students/{student_id}#schedule")


@app.route("/schedule/override", methods=["POST"])
def schedule_override_add():
    student_id    = request.form.get("student_id")
    override_date = request.form.get("override_date")
    minutes       = int(request.form.get("override_minutes", 0))
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO schedule_override
        (student_id, date, available_minutes) VALUES (?, ?, ?)
    """, (student_id, override_date, minutes))
    conn.commit()
    conn.close()
    return redirect(f"/students/{student_id}#schedule")


@app.route("/schedule/override/delete", methods=["POST"])
def schedule_override_delete():
    student_id    = request.form.get("student_id")
    override_date = request.form.get("override_date")
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM schedule_override WHERE student_id=? AND date=?",
              (student_id, override_date))
    conn.commit()
    conn.close()
    return redirect(f"/students/{student_id}#schedule")


@app.route("/schedule_subject/base", methods=["POST"])
def schedule_subject_base_save():
    student_id = request.form.get("student_id")
    subject    = request.form.get("subject")
    conn = get_connection()
    c = conn.cursor()
    for dow in ["mon","tue","wed","thu","fri","sat","sun"]:
        minutes = int(request.form.get(dow, 0))
        c.execute("""
            INSERT OR REPLACE INTO schedule_base_subject
            (student_id, subject, dow, available_minutes) VALUES (?, ?, ?, ?)
        """, (student_id, subject, dow, minutes))
    conn.commit()
    conn.close()
    return redirect(f"/students/{student_id}#schedule")


@app.route("/schedule_subject/override", methods=["POST"])
def schedule_subject_override_add():
    student_id    = request.form.get("student_id")
    subject       = request.form.get("subject")
    override_date = request.form.get("override_date")
    minutes       = int(request.form.get("override_minutes", 0))
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO schedule_override_subject
        (student_id, subject, date, available_minutes) VALUES (?, ?, ?, ?)
    """, (student_id, subject, override_date, minutes))
    conn.commit()
    conn.close()
    return redirect(f"/students/{student_id}#schedule")


@app.route("/schedule_subject/override/delete", methods=["POST"])
def schedule_subject_override_delete():
    student_id    = request.form.get("student_id")
    subject       = request.form.get("subject")
    override_date = request.form.get("override_date")
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        DELETE FROM schedule_override_subject
        WHERE student_id=? AND subject=? AND date=?
    """, (student_id, subject, override_date))
    conn.commit()
    conn.close()
    return redirect(f"/students/{student_id}#schedule")


@app.route("/class_schedule/set", methods=["POST"])
def class_schedule_set():
    student_id = request.form.get("student_id")
    subject    = request.form.get("subject")
    dows       = request.form.getlist("dows")
    conn = get_connection()
    c = conn.cursor()
    # 既存の曜日設定を削除してから再登録
    c.execute("DELETE FROM class_schedule_base WHERE student_id=? AND subject=?",
              (student_id, subject))
    for dow in dows:
        c.execute("""
            INSERT INTO class_schedule_base (student_id, subject, dow)
            VALUES (?, ?, ?)
        """, (student_id, subject, dow))
    conn.commit()
    conn.close()
    return redirect(f"/students/{student_id}#classdays")


@app.route("/class_schedule/next", methods=["POST"])
def class_schedule_next():
    student_id      = request.form.get("student_id")
    subject         = request.form.get("subject")
    next_class_date = request.form.get("next_class_date", "").strip()
    conn = get_connection()
    c = conn.cursor()
    if next_class_date:
        c.execute("""
            INSERT OR REPLACE INTO class_schedule_override
            (student_id, subject, next_class_date) VALUES (?, ?, ?)
        """, (student_id, subject, next_class_date))
    else:
        c.execute("""
            DELETE FROM class_schedule_override
            WHERE student_id=? AND subject=?
        """, (student_id, subject))
    conn.commit()
    conn.close()
    return redirect(f"/students/{student_id}#classdays")


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

    # 次回授業日(override)
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


@app.route("/students/add", methods=["POST"])
def students_add():
    student_id = request.form.get("student_id", "").strip()
    name       = request.form.get("name", "").strip()
    subjects   = request.form.get("subjects", "").strip()
    plan_mode  = request.form.get("plan_mode", "all")
    if not student_id or not name:
        return redirect("/students")
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO students
        (student_id, name, subjects, plan_mode)
        VALUES (?, ?, ?, ?)
    """, (student_id, name, subjects, plan_mode))
    conn.commit()
    conn.close()
    return redirect("/students")


@app.route("/textbooks/<int:textbook_id>/students", methods=["POST"])
def textbook_students_update(textbook_id):
    """テキストと生徒の紐づけを更新する"""
    student_ids = request.form.getlist("student_ids")
    conn = get_connection()
    c = conn.cursor()
    # 既存の紐づけを削除してから再登録
    c.execute("DELETE FROM student_textbooks WHERE textbook_id=?", (textbook_id,))
    for sid in student_ids:
        c.execute("""
            INSERT OR IGNORE INTO student_textbooks (student_id, textbook_id)
            VALUES (?, ?)
        """, (sid, textbook_id))
    conn.commit()
    conn.close()
    return redirect("/textbooks")


@app.route("/assignments/add", methods=["POST"])
def assignment_add():
    """出題予定を手動で追加する(複数生徒対応)"""
    problem_id     = request.form.get("problem_id")
    student_ids    = request.form.getlist("student_ids")
    scheduled_date = request.form.get("scheduled_date", "").strip()
    category       = request.form.get("category", "New")
    redirect_to    = request.form.get("redirect_to", "/assignments/list")

    if not scheduled_date:
        scheduled_date = "2099-12-31"

    conn = get_connection()
    c = conn.cursor()
    for sid in student_ids:
        c.execute("""
            INSERT OR REPLACE INTO assignments
            (student_id, problem_id, scheduled_date, category)
            VALUES (?, ?, ?, ?)
        """, (sid, problem_id, scheduled_date, category))
    conn.commit()
    conn.close()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"ok": True, "count": len(student_ids)})
    return redirect(redirect_to)


@app.route("/api/problems/search")
def api_problems_search():
    """問題番号/テキスト名で問題を検索するAPI"""
    q = request.args.get("q", "").strip()
    student_id = request.args.get("student_id", "")
    if not q:
        return jsonify([])
    conn = get_connection()
    c = conn.cursor()
    like = f"%{q}%"
    if student_id:
        c.execute("""
            SELECT DISTINCT p.problem_id, p.subject, p.textbook,
                   p.problem_number, p.importance, p.difficulty, p.review_value
            FROM problems p
            JOIN student_textbooks st ON p.textbook_id = st.textbook_id
            WHERE st.student_id = ?
              AND (p.problem_number LIKE ? OR p.textbook LIKE ?
                   OR CAST(p.problem_id AS TEXT) LIKE ?)
            ORDER BY p.subject, p.textbook, p.problem_id
            LIMIT 20
        """, (student_id, like, like, like))
    else:
        c.execute("""
            SELECT problem_id, subject, textbook, problem_number,
                   importance, difficulty, review_value
            FROM problems
            WHERE problem_number LIKE ? OR textbook LIKE ?
               OR CAST(problem_id AS TEXT) LIKE ?
            ORDER BY subject, textbook, problem_id
            LIMIT 20
        """, (like, like, like))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/problems/update_textbook", methods=["POST"])
def api_problems_update_textbook():
    """問題のテキストを変更するAPI"""
    data = request.get_json()
    problem_id  = data.get("problem_id")
    textbook_id = data.get("textbook_id")
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name, subject FROM textbooks WHERE textbook_id=?",
              (textbook_id,))
    tb = c.fetchone()
    if not tb:
        conn.close()
        return jsonify({"status": "error", "message": "Textbook not found"}), 404
    c.execute("""
        UPDATE problems SET textbook_id=?, textbook=?, subject=?
        WHERE problem_id=?
    """, (textbook_id, tb["name"], tb["subject"], problem_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok",
                    "textbook": tb["name"], "subject": tb["subject"]})


@app.route("/api/textbooks/list")
def api_textbooks_list():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT t.textbook_id, t.name, t.subject,
               s.name as series_name
        FROM textbooks t
        LEFT JOIN series s ON t.series_id = s.series_id
        ORDER BY t.subject, s.name, t.name
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/next_order")
def api_next_order():
    """同一テキスト内の次のorder_in_textbookを返す"""
    textbook_id = request.args.get("textbook_id")
    if not textbook_id:
        return jsonify({"next_order": 1})
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT MAX(order_in_textbook) as max_order
        FROM problems WHERE textbook_id=?
    """, (textbook_id,))
    row = c.fetchone()
    conn.close()
    max_order = row["max_order"] if row and row["max_order"] else 0
    return jsonify({"next_order": max_order + 1})


@app.route("/favicon.ico")
def favicon():
    from flask import send_from_directory
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico" if os.path.exists(
            os.path.join(app.root_path, "static", "favicon.ico"))
        else "favicon.svg",
        mimetype="image/x-icon"
    )


@app.route("/api/sections/<int:section_id>/problems")
def api_section_problems(section_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT problem_id, problem_number, textbook_id,
               importance, difficulty, review_value, order_in_textbook
        FROM problems
        WHERE section_id=?
        ORDER BY order_in_textbook, problem_id
    """, (section_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/sections_by_subject")
def api_sections_by_subject():
    """指定教科のセクション一覧を返す(Preview絞り込み用)
    student_idが指定された場合はstudent_textbooksで紐づくテキストのセクションのみ返す.
    """
    subject    = request.args.get("subject", "")
    student_id = request.args.get("student_id", "")
    conn = get_connection()
    c = conn.cursor()
    if student_id and subject:
        # 生徒に紐づくテキスト(student_textbooks)のセクションのみ
        c.execute("""
            SELECT DISTINCT ts.section_id, ts.name, ts.order_index,
                   t.name as textbook_name
            FROM textbook_sections ts
            JOIN textbooks t ON ts.textbook_id = t.textbook_id
            JOIN student_textbooks st ON st.textbook_id = t.textbook_id
            WHERE t.subject=? AND st.student_id=?
            ORDER BY t.name, ts.order_index
        """, (subject, student_id))
    elif student_id:
        # 教科指定なし:生徒に紐づく全セクション
        c.execute("""
            SELECT DISTINCT ts.section_id, ts.name, ts.order_index,
                   t.name as textbook_name, t.subject
            FROM textbook_sections ts
            JOIN textbooks t ON ts.textbook_id = t.textbook_id
            JOIN student_textbooks st ON st.textbook_id = t.textbook_id
            WHERE st.student_id=?
            ORDER BY t.subject, t.name, ts.order_index
        """, (student_id,))
    elif subject:
        c.execute("""
            SELECT DISTINCT ts.section_id, ts.name, ts.order_index,
                   t.name as textbook_name
            FROM textbook_sections ts
            JOIN textbooks t ON ts.textbook_id = t.textbook_id
            WHERE t.subject=?
            ORDER BY t.name, ts.order_index
        """, (subject,))
    else:
        c.execute("""
            SELECT ts.section_id, ts.name, ts.order_index,
                   t.name as textbook_name
            FROM textbook_sections ts
            JOIN textbooks t ON ts.textbook_id = t.textbook_id
            ORDER BY t.subject, t.name, ts.order_index
        """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/history/update_score", methods=["POST"])
def history_update_score():
    """Edit RecordsページからScoreを更新する"""
    data = request.get_json()
    history_id = data.get("history_id")
    score      = data.get("score")
    if not history_id or score is None:
        return jsonify({"ok": False, "message": "missing params"}), 400
    score = int(score)
    if not (1 <= score <= 5):
        return jsonify({"ok": False, "message": "invalid score"}), 400
    # scoreに応じてcorrectも更新(4〜5=正答, 1〜3=誤答)
    correct = 1 if score >= 4 else 0
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE history SET score=?, correct=? WHERE history_id=?",
        (score, correct, history_id)
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/textbooks_by_student")
def api_textbooks_by_student():
    """生徒に紐づくテキスト一覧を返す"""
    student_id = request.args.get("student_id", "")
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT t.textbook_id, t.name, t.subject
        FROM textbooks t
        JOIN student_textbooks st ON st.textbook_id = t.textbook_id
        WHERE st.student_id=?
        ORDER BY t.subject, t.name
    """, (student_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/sections_by_textbook")
def api_sections_by_textbook():
    """テキストのセクション一覧を返す"""
    textbook_id = request.args.get("textbook_id", "")
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT section_id, name, order_index
        FROM textbook_sections
        WHERE textbook_id=?
        ORDER BY order_index
    """, (textbook_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/problems_for_assignment")
def api_problems_for_assignment():
    """Assignment一括追加用の問題リストを返す(未アサインの問題のみ)"""
    textbook_id = request.args.get("textbook_id", "")
    section_id  = request.args.get("section_id", "")
    student_id  = request.args.get("student_id", "")
    conn = get_connection()
    c = conn.cursor()
    query = """
        SELECT p.problem_id, p.problem_number, p.importance,
               p.difficulty, p.review_value, p.estimated_minutes
        FROM problems p
        WHERE p.textbook_id=?
    """
    params = [textbook_id]
    if section_id:
        query += " AND p.section_id=?"
        params.append(section_id)
    if student_id:
        # すでにアサイン済みの問題を除外
        query += """
          AND p.problem_id NOT IN (
            SELECT problem_id FROM assignments WHERE student_id=?
          )
        """
        params.append(student_id)
    query += " ORDER BY p.order_in_textbook, p.problem_id"
    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/api/problems_for_record")
def api_problems_for_record():
    """Bulk Record用の問題リストを返す(その生徒にアサイン済みの問題)"""
    textbook_id = request.args.get("textbook_id", "")
    section_id  = request.args.get("section_id", "")
    student_id  = request.args.get("student_id", "")
    conn = get_connection()
    c = conn.cursor()
    query = """
        SELECT DISTINCT p.problem_id, p.problem_number, p.importance,
               p.difficulty, p.review_value, p.estimated_minutes
        FROM problems p
        JOIN assignments a ON a.problem_id = p.problem_id
        WHERE p.textbook_id=? AND a.student_id=?
    """
    params = [textbook_id, student_id]
    if section_id:
        query += " AND p.section_id=?"
        params.append(section_id)
    query += " ORDER BY p.order_in_textbook, p.problem_id"
    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return jsonify(rows)


@app.route("/assignments/bulk_add", methods=["POST"])
def assignments_bulk_add():
    """出題予定を一括登録する"""
    from database import get_auto_next_class_date
    data        = request.get_json()
    student_id  = data.get("student_id")
    problem_ids = data.get("problem_ids", [])
    category    = data.get("category", "New")
    sched_date  = data.get("scheduled_date", "").strip()
    if not student_id or not problem_ids:
        return jsonify({"ok": False, "message": "missing params"}), 400
    conn = get_connection()
    c = conn.cursor()
    added = 0
    for pid in problem_ids:
        # 重複チェック
        c.execute("SELECT 1 FROM assignments WHERE student_id=? AND problem_id=?",
                  (student_id, pid))
        if c.fetchone():
            continue
        # 出題日の決定
        if sched_date:
            effective_date = sched_date
        else:
            c.execute("SELECT subject FROM problems WHERE problem_id=?", (pid,))
            row = c.fetchone()
            subj = row["subject"] if row else ""
            auto = get_auto_next_class_date(student_id, subj)
            effective_date = auto if auto else "2099-12-31"
        c.execute("""
            INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
            VALUES (?, ?, ?, ?)
        """, (student_id, pid, effective_date, category))
        added += 1
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "added": added})


@app.route("/record/bulk", methods=["GET"])
def record_bulk():
    """Bulk Record ページ"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT student_id, name FROM students ORDER BY student_id")
    students = c.fetchall()
    conn.close()
    from datetime import date
    return render_template("record_bulk.html",
                           students=students,
                           today=date.today().isoformat())


@app.route("/record/bulk_add", methods=["POST"])
def record_bulk_add():
    """授業記録を一括登録する"""
    from database import calc_new_mastery
    data       = request.get_json()
    student_id = data.get("student_id")
    date_str   = data.get("date")
    records    = data.get("records", [])
    if not student_id or not date_str or not records:
        return jsonify({"ok": False, "message": "missing params"}), 400
    conn = get_connection()
    c = conn.cursor()
    added = 0
    for rec in records:
        pid   = rec.get("problem_id")
        score = int(rec.get("score", 5))
        if not pid:
            continue
        correct     = 1 if score >= 4 else 0
        new_mastery = calc_new_mastery(student_id, pid, score, date_str)
        c.execute("""
            INSERT INTO history
            (student_id, problem_id, date, correct, mastery, category, score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (student_id, pid, date_str, correct, new_mastery, "Record", score))
        added += 1
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "added": added})


@app.route("/sections/bulk_assign", methods=["POST"])
def sections_bulk_assign():
    """複数の問題を一括でSectionに割り当てる(section_id=nullで解除)"""
    data        = request.get_json()
    problem_ids = data.get("problem_ids", [])
    section_id  = data.get("section_id")  # nullの場合は解除
    if not problem_ids:
        return jsonify({"ok": False, "message": "no problems"}), 400
    conn = get_connection()
    c = conn.cursor()
    for pid in problem_ids:
        c.execute("UPDATE problems SET section_id=? WHERE problem_id=?",
                  (section_id, pid))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "updated": len(problem_ids)})

if __name__ == "__main__":
    init_db()

    # アプリ起動時に自動昇格を実行
    from database import (auto_promote_on_launch,
                          get_last_launch_date,
                          update_last_launch_date)
    from datetime import date as _date, timedelta as _timedelta
    last_launch = get_last_launch_date()
    today = _date.today().isoformat()
    if last_launch < today:
        # 前回起動日の翌日から昨日までを昇格対象とする
        # (今日のは今日の授業が終わってから昇格すべきなので除く)
        from_date = (
            _date.fromisoformat(last_launch) + _timedelta(days=1)
        ).isoformat()
        to_date = (
            _date.today() - _timedelta(days=1)
        ).isoformat()
        if from_date <= to_date:
            promoted = auto_promote_on_launch(from_date, to_date)
            print(f"自動昇格:{promoted}問を処理しました"
                  f"({from_date}〜{to_date})")
    update_last_launch_date()

    app.run(debug=True)
