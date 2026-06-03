"""
MCP ツールハンドラの共有ロジック。
mcp_server.py（ローカル）と app.py（/api/tool エンドポイント）の両方から使用する。
各関数は plain な Python オブジェクト（dict/list）を返す。
"""
import os
import sqlite3
from datetime import date, timedelta

DB_PATH = os.environ.get(
    'DB_PATH',
    os.path.join(os.path.dirname(__file__), 'study_planner.db')
)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_auto_next_class_date(student_id, subject):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT next_class_date FROM class_schedule_override WHERE student_id=? AND subject=?",
              (student_id, subject))
    row = c.fetchone()
    if row and row["next_class_date"]:
        conn.close()
        return row["next_class_date"]
    c.execute("SELECT dow FROM class_schedule_base WHERE student_id=? AND subject=?",
              (student_id, subject))
    rows = c.fetchall()
    conn.close()
    if not rows:
        return None
    dow_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
    class_dows = set(dow_map[r["dow"]] for r in rows if r["dow"] in dow_map)
    today = date.today()
    for delta in range(1, 14):
        d = today + timedelta(days=delta)
        if d.weekday() in class_dows:
            return d.isoformat()
    return None


def score_to_correct(score):
    return 1 if score >= 4 else 0


def calc_new_mastery(student_id, problem_id, score, record_date):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT mastery FROM history WHERE student_id=? AND problem_id=? ORDER BY date DESC LIMIT 1",
              (student_id, problem_id))
    row = c.fetchone()
    current_mastery = row["mastery"] if row else 1
    if score == 3:
        conn.close()
        return current_mastery
    correct = score_to_correct(score)
    if correct == 0:
        conn.close()
        return max(1, current_mastery - 1)
    if current_mastery >= 3:
        conn.close()
        return 3
    if current_mastery == 1:
        c.execute("SELECT COUNT(*) as cnt FROM history WHERE student_id=? AND problem_id=? AND correct=1 AND date < ?",
                  (student_id, problem_id, record_date))
        cnt = c.fetchone()["cnt"]
        new_mastery = 2 if cnt >= 1 else 1
    elif current_mastery == 2:
        c.execute("SELECT date FROM history WHERE student_id=? AND problem_id=? AND correct=1 ORDER BY date DESC LIMIT 3",
                  (student_id, problem_id))
        dates = [r["date"] for r in c.fetchall()]
        if len(dates) >= 2:
            from datetime import datetime
            d1 = datetime.fromisoformat(dates[-1])
            d2 = datetime.fromisoformat(record_date)
            weeks_diff = (d2 - d1).days // 7
            new_mastery = 3 if (len(dates) >= 3 and weeks_diff >= 1) else 2
        else:
            new_mastery = 2
    else:
        new_mastery = current_mastery
    conn.close()
    return new_mastery


def handle_tool(name: str, arguments: dict):
    """ツール名と引数を受け取り、結果を plain Python オブジェクトで返す。"""

    # ── 参照系 ──────────────────────────────────────────────────────────
    if name == "get_all_students":
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM students ORDER BY student_id")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    elif name == "get_student_summary":
        student_id = arguments["student_id"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM students WHERE student_id=?", (student_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return {"error": "生徒が見つかりません"}
        student = dict(row)
        c.execute("""
            SELECT h.date, h.correct, h.mastery, h.category, h.score,
                   p.subject, p.textbook, p.problem_number,
                   p.importance, p.difficulty, p.review_value, p.problem_id
            FROM history h JOIN problems p ON h.problem_id = p.problem_id
            WHERE h.student_id=? ORDER BY h.date DESC LIMIT 30
        """, (student_id,))
        history = [dict(r) for r in c.fetchall()]
        c.execute("""
            SELECT a.assignment_id, a.scheduled_date, a.category,
                   p.problem_id, p.subject, p.textbook, p.problem_number,
                   p.importance, p.review_value, p.estimated_minutes, p.order_in_textbook,
                   (SELECT mastery FROM history h
                    WHERE h.student_id=a.student_id AND h.problem_id=a.problem_id
                    ORDER BY h.date DESC LIMIT 1) as mastery
            FROM assignments a JOIN problems p ON a.problem_id=p.problem_id
            WHERE a.student_id=? ORDER BY a.scheduled_date, p.subject
        """, (student_id,))
        assignments = [dict(r) for r in c.fetchall()]
        conn.close()
        return {"student": student, "recent_history": history, "upcoming_assignments": assignments}

    elif name == "get_problems":
        conn = get_connection()
        c = conn.cursor()
        student_id = arguments.get("student_id")
        subject    = arguments.get("subject")
        query = """
            SELECT p.problem_id, p.subject, p.textbook, p.textbook_id,
                   p.problem_number, p.importance, p.difficulty,
                   p.review_value, p.estimated_minutes, p.instruction, p.order_in_textbook
            FROM problems p WHERE 1=1
        """
        params = []
        if student_id:
            query += " AND p.problem_id IN (SELECT problem_id FROM assignments WHERE student_id=?)"
            params.append(student_id)
        if subject:
            query += " AND p.subject=?"
            params.append(subject)
        query += " ORDER BY p.subject, p.order_in_textbook, p.problem_id"
        c.execute(query, params)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    elif name == "get_assignments":
        student_id = arguments["student_id"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT a.assignment_id, a.scheduled_date, a.category,
                   p.problem_id, p.subject, p.textbook, p.problem_number,
                   p.importance, p.review_value, p.estimated_minutes, p.order_in_textbook,
                   (SELECT mastery FROM history h
                    WHERE h.student_id=a.student_id AND h.problem_id=a.problem_id
                    ORDER BY h.date DESC LIMIT 1) as mastery
            FROM assignments a JOIN problems p ON a.problem_id=p.problem_id
            WHERE a.student_id=? ORDER BY a.scheduled_date, p.subject, p.order_in_textbook
        """, (student_id,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    elif name == "get_series":
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT s.*, COUNT(t.textbook_id) as textbook_count
            FROM series s LEFT JOIN textbooks t ON s.series_id=t.series_id
            GROUP BY s.series_id ORDER BY s.name
        """)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    elif name == "get_textbooks":
        conn = get_connection()
        c = conn.cursor()
        subject = arguments.get("subject")
        if subject:
            c.execute("""
                SELECT t.*, s.name as series_name FROM textbooks t
                LEFT JOIN series s ON t.series_id=s.series_id
                WHERE t.subject=? ORDER BY s.name, t.name
            """, (subject,))
        else:
            c.execute("""
                SELECT t.*, s.name as series_name FROM textbooks t
                LEFT JOIN series s ON t.series_id=s.series_id
                ORDER BY t.subject, s.name, t.name
            """)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    elif name == "get_class_schedule":
        student_id = arguments["student_id"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT subject, dow FROM class_schedule_base WHERE student_id=?", (student_id,))
        base_rows = c.fetchall()
        c.execute("SELECT subject, next_class_date FROM class_schedule_override WHERE student_id=?", (student_id,))
        override_rows = c.fetchall()
        conn.close()
        schedule = {}
        for r in base_rows:
            subj = r["subject"]
            if subj not in schedule:
                schedule[subj] = {"dows": [], "next_class_date": None, "auto_next_class_date": None}
            schedule[subj]["dows"].append(r["dow"])
        for r in override_rows:
            subj = r["subject"]
            if subj not in schedule:
                schedule[subj] = {"dows": [], "next_class_date": None, "auto_next_class_date": None}
            schedule[subj]["next_class_date"] = r["next_class_date"]
        for subj in schedule:
            if not schedule[subj]["next_class_date"]:
                schedule[subj]["auto_next_class_date"] = get_auto_next_class_date(student_id, subj)
        return schedule

    elif name == "get_sections":
        textbook_id = arguments.get("textbook_id")
        conn = get_connection()
        c = conn.cursor()
        if textbook_id:
            c.execute("SELECT * FROM textbook_sections WHERE textbook_id=? ORDER BY order_index, section_id",
                      (textbook_id,))
        else:
            c.execute("SELECT * FROM textbook_sections ORDER BY textbook_id, order_index, section_id")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    elif name == "get_suppression_list":
        student_id = arguments["student_id"]
        conn = get_connection()
        c = conn.cursor()
        try:
            c.execute("SELECT problem_id FROM suppression WHERE student_id=?", (student_id,))
            rows = [r["problem_id"] for r in c.fetchall()]
        except Exception:
            rows = []
        conn.close()
        return rows

    # ── 登録系 ──────────────────────────────────────────────────────────
    elif name == "add_series":
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO series (name) VALUES (?)", (arguments["name"],))
        conn.commit()
        series_id = c.lastrowid
        conn.close()
        return {"series_id": series_id, "name": arguments["name"]}

    elif name == "add_textbook":
        series_id  = arguments.get("series_id")
        tb_name    = arguments["name"]
        subject    = arguments["subject"]
        student_id = arguments.get("student_id")
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO textbooks (series_id, name, subject) VALUES (?,?,?)",
                  (series_id, tb_name, subject))
        conn.commit()
        textbook_id = c.lastrowid
        if student_id:
            c.execute("INSERT OR IGNORE INTO student_textbooks (student_id, textbook_id) VALUES (?,?)",
                      (student_id, textbook_id))
            conn.commit()
        conn.close()
        return {"textbook_id": textbook_id, "name": tb_name, "subject": subject}

    elif name == "add_problem":
        subject           = arguments["subject"]
        textbook_id       = arguments["textbook_id"]
        problem_number    = arguments["problem_number"]
        importance        = arguments["importance"]
        difficulty        = arguments["difficulty"]
        review_value      = arguments["review_value"]
        estimated_minutes = arguments["estimated_minutes"]
        instruction       = arguments.get("instruction", "")
        student_ids       = arguments.get("student_ids", [])
        category          = arguments.get("category", "New")
        scheduled_date    = arguments.get("scheduled_date", "").strip()
        undecided         = arguments.get("undecided", False)
        order_in_textbook = arguments.get("order_in_textbook")
        total_minutes     = arguments.get("total_minutes")
        section_id        = arguments.get("section_id")
        section_name      = arguments.get("section_name", "").strip()

        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT name FROM textbooks WHERE textbook_id=?", (textbook_id,))
        tb_row = c.fetchone()
        textbook = tb_row["name"] if tb_row else ""
        # 重複チェック：同テキスト内に同じ問題番号が既にあれば登録しない
        c.execute("SELECT problem_id FROM problems WHERE textbook_id=? AND problem_number=?",
                  (textbook_id, problem_number))
        existing = c.fetchone()
        if existing:
            conn.close()
            return {"error": f"既に登録済みです: problem_id={existing['problem_id']}, problem_number={problem_number}",
                    "existing_problem_id": existing["problem_id"]}
        # セクション処理: section_nameが指定されたら既存を探し、なければ新規作成
        if section_name and not section_id:
            c.execute("SELECT section_id FROM textbook_sections WHERE textbook_id=? AND name=?",
                      (textbook_id, section_name))
            sec_row = c.fetchone()
            if sec_row:
                section_id = sec_row["section_id"]
            else:
                c.execute("SELECT MAX(order_index) as m FROM textbook_sections WHERE textbook_id=?",
                          (textbook_id,))
                max_order = c.fetchone()["m"] or 0
                c.execute("INSERT INTO textbook_sections (textbook_id, name, order_index) VALUES (?,?,?)",
                          (textbook_id, section_name, max_order + 1))
                conn.commit()
                section_id = c.lastrowid
        if order_in_textbook is None:
            c.execute("SELECT MAX(order_in_textbook) as m FROM problems WHERE textbook_id=?", (textbook_id,))
            r = c.fetchone()
            order_in_textbook = (r["m"] if r and r["m"] else 0) + 1
        c.execute("""
            INSERT INTO problems
            (subject, textbook, textbook_id, section_id, problem_number,
             importance, difficulty, review_value,
             estimated_minutes, instruction, type, order_in_textbook, total_minutes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (subject, textbook, textbook_id, section_id, problem_number,
              importance, difficulty, review_value,
              estimated_minutes, instruction, "標準", order_in_textbook, total_minutes))
        conn.commit()
        problem_id = c.lastrowid
        for sid in student_ids:
            if undecided:
                effective_date = "2099-12-31"
            elif not scheduled_date:
                auto_date = get_auto_next_class_date(sid, subject)
                effective_date = auto_date if auto_date else "2099-12-31"
            else:
                effective_date = scheduled_date
            c.execute("INSERT OR IGNORE INTO student_textbooks (student_id, textbook_id) VALUES (?,?)",
                      (sid, textbook_id))
            c.execute("INSERT INTO assignments (student_id, problem_id, scheduled_date, category) VALUES (?,?,?,?)",
                      (sid, problem_id, effective_date, category))
        conn.commit()
        conn.close()
        return {
            "problem_id": problem_id,
            "textbook": textbook,
            "order_in_textbook": order_in_textbook,
            "db_path": DB_PATH,
            "scheduled_dates": {
                sid: ("2099-12-31（未定）" if undecided
                      else (scheduled_date or get_auto_next_class_date(sid, subject) or "2099-12-31"))
                for sid in student_ids
            }
        }

    elif name == "add_assignment":
        student_id     = arguments["student_id"]
        problem_id     = arguments["problem_id"]
        category       = arguments["category"]
        scheduled_date = arguments.get("scheduled_date", "").strip()
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT subject FROM problems WHERE problem_id=?", (problem_id,))
        p = c.fetchone()
        subject = p["subject"] if p else ""
        if not scheduled_date:
            auto_date = get_auto_next_class_date(student_id, subject)
            effective_date = auto_date if auto_date else "2099-12-31"
        else:
            effective_date = scheduled_date
        c.execute("INSERT OR REPLACE INTO assignments (student_id, problem_id, scheduled_date, category) VALUES (?,?,?,?)",
                  (student_id, problem_id, effective_date, category))
        conn.commit()
        assignment_id = c.lastrowid
        conn.close()
        return {"assignment_id": assignment_id, "scheduled_date": effective_date, "category": category}

    elif name == "add_record":
        student_id  = arguments["student_id"]
        problem_id  = arguments["problem_id"]
        record_date = arguments.get("date", date.today().isoformat())
        score       = int(arguments.get("score", 5))
        correct     = score_to_correct(score)
        conn = get_connection()
        c = conn.cursor()
        # 同じ問題の自動記録(Auto)が過去に存在する場合は手動記録で上書き
        c.execute("""
            DELETE FROM history
            WHERE student_id=? AND problem_id=? AND category='Auto' AND date <= ?
        """, (student_id, problem_id, record_date))
        conn.commit()
        conn.close()
        new_mastery = calc_new_mastery(student_id, problem_id, score, record_date)
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO history (student_id, problem_id, date, correct, mastery, category, score)
            VALUES (?,?,?,?,?,?,?)
        """, (student_id, problem_id, record_date, correct, new_mastery, "Record", score))
        conn.commit()
        conn.close()
        from database import update_assignments_after_record
        update_assignments_after_record(student_id, problem_id, record_date, new_mastery)
        try:
            from database import auto_record_unreported
            auto_results = auto_record_unreported(student_id, record_date)
        except Exception:
            auto_results = []
        score_labels = {5: "Perfect", 4: "Good", 3: "Review", 2: "Retry", 1: "Failed"}
        return {
            "new_mastery": new_mastery,
            "mastery_stars": "★" * new_mastery,
            "score": score,
            "score_label": score_labels.get(score, str(score)),
            "correct": correct,
            "auto_recorded": auto_results,
        }

    # ── 更新・削除系 ─────────────────────────────────────────────────────
    elif name == "update_problem":
        problem_id = arguments["problem_id"]
        conn = get_connection()
        c = conn.cursor()
        for field in ["importance", "difficulty", "review_value", "estimated_minutes", "instruction"]:
            if field in arguments:
                c.execute(f"UPDATE problems SET {field}=? WHERE problem_id=?",
                          (arguments[field], problem_id))
        conn.commit()
        conn.close()
        return {"status": "ok", "problem_id": problem_id}

    elif name == "delete_assignment":
        assignment_id = arguments.get("assignment_id")
        if not assignment_id:
            return {"error": "assignment_id is required"}
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT a.assignment_id, a.student_id, a.category, a.scheduled_date,
                   p.subject, p.textbook, p.problem_number
            FROM assignments a JOIN problems p ON a.problem_id=p.problem_id
            WHERE a.assignment_id=?
        """, (assignment_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return {"error": f"assignment_id {assignment_id} not found"}
        info = dict(row)
        c.execute("DELETE FROM assignments WHERE assignment_id=?", (assignment_id,))
        conn.commit()
        conn.close()
        return {"status": "ok", "deleted": info}

    elif name == "delete_problem":
        problem_id = arguments["problem_id"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM assignments WHERE problem_id=?", (problem_id,))
        c.execute("DELETE FROM history WHERE problem_id=?", (problem_id,))
        c.execute("DELETE FROM problems WHERE problem_id=?", (problem_id,))
        conn.commit()
        conn.close()
        return {"status": "ok", "deleted_problem_id": problem_id}

    elif name == "update_assignment_date":
        assignment_id  = arguments["assignment_id"]
        scheduled_date = arguments["scheduled_date"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE assignments SET scheduled_date=? WHERE assignment_id=?",
                  (scheduled_date, assignment_id))
        conn.commit()
        conn.close()
        return {"status": "ok", "assignment_id": assignment_id, "scheduled_date": scheduled_date}

    elif name == "update_assignment_category":
        assignment_id = arguments["assignment_id"]
        category      = arguments["category"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE assignments SET category=? WHERE assignment_id=?",
                  (category, assignment_id))
        conn.commit()
        conn.close()
        return {"status": "ok", "assignment_id": assignment_id, "category": category}

    elif name == "update_mastery":
        student_id = arguments["student_id"]
        problem_id = arguments["problem_id"]
        mastery    = max(1, min(3, int(arguments["mastery"])))
        today      = date.today().isoformat()
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO history (student_id, problem_id, date, correct, mastery, category) VALUES (?,?,?,?,?,?)",
                  (student_id, problem_id, today, 1, mastery, "Manual"))
        conn.commit()
        conn.close()
        return {"status": "ok", "mastery": mastery, "mastery_stars": "★" * mastery}

    elif name == "update_review_value":
        problem_id   = arguments["problem_id"]
        review_value = arguments["review_value"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE problems SET review_value=? WHERE problem_id=?", (review_value, problem_id))
        conn.commit()
        conn.close()
        return {"status": "ok", "problem_id": problem_id, "review_value": review_value}

    elif name == "set_class_schedule":
        student_id = arguments["student_id"]
        subject    = arguments["subject"]
        dows       = arguments["dows"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM class_schedule_base WHERE student_id=? AND subject=?", (student_id, subject))
        for dow in dows:
            c.execute("INSERT INTO class_schedule_base (student_id, subject, dow) VALUES (?,?,?)",
                      (student_id, subject, dow))
        conn.commit()
        conn.close()
        return {"status": "ok", "student_id": student_id, "subject": subject, "dows": dows}

    elif name == "set_next_class_date":
        student_id      = arguments["student_id"]
        subject         = arguments["subject"]
        next_class_date = arguments.get("next_class_date", "").strip()
        conn = get_connection()
        c = conn.cursor()
        if next_class_date:
            c.execute("INSERT OR REPLACE INTO class_schedule_override (student_id, subject, next_class_date) VALUES (?,?,?)",
                      (student_id, subject, next_class_date))
        else:
            c.execute("DELETE FROM class_schedule_override WHERE student_id=? AND subject=?",
                      (student_id, subject))
        conn.commit()
        conn.close()
        return {"status": "ok", "next_class_date": next_class_date or "(リセット)"}

    elif name == "clear_suppression":
        student_id = arguments["student_id"]
        conn = get_connection()
        c = conn.cursor()
        try:
            c.execute("DELETE FROM suppression WHERE student_id=?", (student_id,))
            conn.commit()
        except Exception:
            pass
        conn.close()
        return {"status": "ok", "cleared": student_id}

    elif name == "auto_record_session":
        student_id  = arguments["student_id"]
        record_date = arguments.get("record_date", date.today().isoformat())
        try:
            from database import auto_record_unreported
            results = auto_record_unreported(student_id, record_date)
        except Exception as e:
            results = [{"error": str(e)}]
        score_labels = {5: "Perfect", 4: "Good", 3: "Review", 2: "Retry", 1: "Failed"}
        summary = [{
            "problem_id":     r["problem_id"],
            "scheduled_date": r["scheduled_date"],
            "difficulty":     r["difficulty"],
            "score":          r["score"],
            "score_label":    score_labels.get(r["score"], str(r["score"])),
            "new_mastery":    r["new_mastery"],
            "mastery_stars":  "★" * r["new_mastery"],
        } for r in results if "error" not in r]
        return {"auto_recorded_count": len(summary), "records": summary}

    return {"error": f"Unknown tool: {name}"}
