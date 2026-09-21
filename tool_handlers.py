"""
MCP ツールハンドラの共有ロジック。
mcp_server.py（ローカル）と app.py（/api/tool エンドポイント）の両方から使用する。
各関数は plain な Python オブジェクト（dict/list）を返す。
"""
from datetime import date, timedelta

# DB接続は database.py に一本化(mcp_server.py が DB_PATH を参照するため再エクスポート)
from database import DB_PATH, get_connection


def get_auto_next_class_date(student_id, subject):
    """次回授業日（手動設定優先。過去日の手動設定は自動失効し曜日ベースの未来日へフォールバック）"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT next_class_date FROM class_schedule_override WHERE student_id=? AND subject=?",
              (student_id, subject))
    row = c.fetchone()
    if row and row["next_class_date"] and row["next_class_date"] >= date.today().isoformat():
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


def _calc_new_mastery_c(c, student_id, problem_id, score, record_date):
    """calc_new_mastery と同一ロジックのカーソル版。
    add_records のように1トランザクション内で複数件を処理する際、
    同一接続内の未コミット行を参照できるようにするために使う。"""
    c.execute("SELECT mastery FROM history WHERE student_id=? AND problem_id=? ORDER BY date DESC LIMIT 1",
              (student_id, problem_id))
    row = c.fetchone()
    current_mastery = row["mastery"] if row else 1
    if score == 3:
        return current_mastery
    correct = score_to_correct(score)
    if correct == 0:
        return max(1, current_mastery - 1)
    if current_mastery >= 3:
        return 3
    if current_mastery == 1:
        c.execute("SELECT COUNT(*) as cnt FROM history WHERE student_id=? AND problem_id=? AND correct=1 AND date < ?",
                  (student_id, problem_id, record_date))
        cnt = c.fetchone()["cnt"]
        return 2 if cnt >= 1 else 1
    if current_mastery == 2:
        c.execute("SELECT date FROM history WHERE student_id=? AND problem_id=? AND correct=1 ORDER BY date DESC LIMIT 3",
                  (student_id, problem_id))
        dates = [r["date"] for r in c.fetchall()]
        if len(dates) >= 2:
            from datetime import datetime
            d1 = datetime.fromisoformat(dates[-1])
            d2 = datetime.fromisoformat(record_date)
            weeks_diff = (d2 - d1).days // 7
            return 3 if (len(dates) >= 3 and weeks_diff >= 1) else 2
        return 2
    return current_mastery


def _update_assignments_after_record_c(c, student_id, problem_id, record_date, new_mastery):
    """database.update_assignments_after_record と同一ロジックのカーソル版。
    次回出題日を返す（problems に該当がなければ None）。"""
    from database import get_next_date
    c.execute("DELETE FROM assignments WHERE student_id=? AND problem_id=?",
              (student_id, problem_id))
    c.execute("SELECT review_value FROM problems WHERE problem_id=?", (problem_id,))
    row = c.fetchone()
    if not row:
        return None
    next_date = get_next_date(row["review_value"], new_mastery, record_date)
    category = {1: "Recall", 2: "Drill"}.get(new_mastery, "Reinforce")
    c.execute("""
        INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
        VALUES (?, ?, ?, ?)
    """, (student_id, problem_id, next_date.isoformat(), category))
    return next_date.isoformat()


SCORE_LABELS = {5: "Perfect", 4: "Good", 3: "Review", 2: "Retry", 1: "Failed"}

# handle_tool が処理できるツール名の一覧（get_server_info が返す。デプロイ確認用）
SUPPORTED_TOOLS = [
    "get_all_students", "get_student_summary", "get_problems", "get_assignments",
    "get_series", "get_textbooks", "get_class_schedule", "get_sections",
    "get_suppression_list", "get_plan_days", "get_plan_history", "get_history",
    "add_series", "add_textbook", "add_problem", "add_assignment",
    "add_record", "add_records",
    "update_problem", "update_assignment_date", "update_assignment_category",
    "update_mastery", "update_review_value",
    "delete_assignment", "delete_problem", "delete_record",
    "set_class_schedule", "set_next_class_date", "clear_suppression",
    "auto_record_session", "recalc_mastery", "get_server_info", "run_migration",
]

SERVER_VERSION = "2026-09-21-export-plan-api"


def handle_tool(name: str, arguments: dict):
    """ツール名と引数を受け取り、結果を plain Python オブジェクトで返す。"""

    if name == "get_server_info":
        return {"version": SERVER_VERSION, "tools": sorted(SUPPORTED_TOOLS)}

    # ── 一回限りの移行(problem_id/no 再編) ──────────────────────────────
    if name == "run_migration":
        import migrate_renumber
        mode = arguments.get("mode", "dry_run")
        if mode not in ("dry_run", "apply", "diagnose_orphans", "reassign_ids_dry", "reassign_ids"):
            return {"error": "mode は 'dry_run' / 'apply' / 'diagnose_orphans' / 'reassign_ids_dry' / 'reassign_ids'"}
        return migrate_renumber.run(DB_PATH, mode)

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
        today_str = date.today().isoformat()
        for r in override_rows:
            subj = r["subject"]
            if subj not in schedule:
                schedule[subj] = {"dows": [], "next_class_date": None, "auto_next_class_date": None}
            if r["next_class_date"] and r["next_class_date"] < today_str:
                # 経過した手動設定は失効扱い（自動計算日を使う）
                schedule[subj]["expired_override"] = r["next_class_date"]
            else:
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

    elif name == "get_plan_days":
        # 計画表と同じ日別割り当てを返す（読み取り専用。DBは変更しない）
        # source="snapshot" で出力時に保存した日別配置を参照する
        # （生徒に渡した計画表と再計算結果のずれを避ける。homework_watch向け）
        student_id = arguments["student_id"]
        start_date = arguments["start_date"]
        target_date = arguments["target_date"]
        subject = arguments.get("subject") or None
        source = (arguments.get("source") or "live").strip().lower()

        if source == "snapshot":
            import json as _json
            conn = get_connection()
            c = conn.cursor()
            c.execute("""
                SELECT history_id, generated_date, subject, plan_data
                FROM plan_history
                WHERE student_id=? AND start_date=? AND end_date=?
                  AND plan_data <> ''
                ORDER BY history_id DESC
            """, (student_id, start_date, target_date))
            snap_rows = c.fetchall()
            conn.close()
            for r in snap_rows:
                # subject指定時は同一教科（または全教科出力）のスナップショットを使う
                if subject and r["subject"] and r["subject"] != subject:
                    continue
                try:
                    payload = _json.loads(r["plan_data"])
                except Exception:
                    continue
                if not (isinstance(payload, dict) and payload.get("format") == "days_v1"):
                    continue  # 旧形式（日別配置なし）はスキップ
                days = payload.get("days", [])
                unassigned = payload.get("unassigned", [])
                if subject:
                    days = [d for d in days if d.get("subject") == subject]
                    unassigned = [u for u in unassigned if u.get("subject") == subject]
                return {
                    "student_id":     student_id,
                    "start_date":     start_date,
                    "target_date":    target_date,
                    "subject":        subject or "",
                    "source":         "snapshot",
                    "generated_date": r["generated_date"],
                    "history_id":     r["history_id"],
                    "days":           days,
                    "unassigned":     unassigned,
                    "empty_days":     payload.get("empty_days", []),
                }
            # スナップショットが無ければ再計算（sourceで明示して返す）

        from planner import build_plan_data
        data = build_plan_data(student_id, start_date, target_date, subject)
        if not data:
            return {"error": f"student not found: {student_id}"}

        rows = []
        for row in data["rows"]:
            for subj, items in row["subjects"].items():
                for it in items:
                    rows.append({
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

        return {
            "student_id":   student_id,
            "student_name": data["student_name"],
            "start_date":   start_date,
            "target_date":  target_date,
            "subject":      subject or "",
            "source":       "live",
            "snapshot_found": False if source == "snapshot" else None,
            "days":         rows,
            "unassigned":   unassigned,
            "empty_days":   data.get("empty_days", []),
        }

    elif name == "get_plan_history":
        # 計画表の出力履歴（読み取り専用）。講師が計画表を出したかの確認に使う
        student_id = arguments.get("student_id")
        limit = int(arguments.get("limit") or 20)
        conn = get_connection()
        c = conn.cursor()
        if student_id:
            c.execute("""
                SELECT history_id, student_id, generated_date, start_date, end_date,
                       subject, confirmed,
                       CASE WHEN excel_path <> '' THEN 1 ELSE 0 END AS has_excel,
                       CASE WHEN pdf_path   <> '' THEN 1 ELSE 0 END AS has_pdf
                FROM plan_history WHERE student_id=?
                ORDER BY generated_date DESC, history_id DESC LIMIT ?
            """, (student_id, limit))
        else:
            c.execute("""
                SELECT history_id, student_id, generated_date, start_date, end_date,
                       subject, confirmed,
                       CASE WHEN excel_path <> '' THEN 1 ELSE 0 END AS has_excel,
                       CASE WHEN pdf_path   <> '' THEN 1 ELSE 0 END AS has_pdf
                FROM plan_history
                ORDER BY generated_date DESC, history_id DESC LIMIT ?
            """, (limit,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    elif name == "get_history":
        # history を生徒×問題×日付範囲で絞って閲覧する軽量ツール
        student_id = arguments["student_id"]
        problem_id = arguments.get("problem_id")
        date_from  = arguments.get("date_from")
        date_to    = arguments.get("date_to")
        limit      = int(arguments.get("limit") or 100)
        conn = get_connection()
        c = conn.cursor()
        query = """
            SELECT h.history_id, h.problem_id, h.date, h.score, h.correct,
                   h.mastery, h.category, p.problem_number, p.textbook
            FROM history h LEFT JOIN problems p ON h.problem_id = p.problem_id
            WHERE h.student_id=?
        """
        params = [student_id]
        if problem_id:
            query += " AND h.problem_id=?"
            params.append(int(problem_id))
        if date_from:
            query += " AND h.date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND h.date <= ?"
            params.append(date_to)
        query += " ORDER BY h.date DESC, h.history_id DESC LIMIT ?"
        params.append(limit)
        c.execute(query, params)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return {"student_id": student_id, "count": len(rows), "history": rows}

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
        # problem_id は no から決定論的に採番する（id = textbook_id×10000 + no）。
        # AUTOINCREMENT に任せず明示指定することで、登録直後から id 規則が保たれる。
        problem_id = textbook_id * 10000 + order_in_textbook
        c.execute("SELECT problem_id FROM problems WHERE problem_id=?", (problem_id,))
        if c.fetchone():
            conn.close()
            return {"error": f"id衝突: problem_id={problem_id}（textbook_id={textbook_id}, no={order_in_textbook}）"
                             f" は既に使用されています。noが重複している可能性があります。",
                    "conflict_problem_id": problem_id}
        c.execute("""
            INSERT INTO problems
            (problem_id, subject, textbook, textbook_id, section_id, problem_number,
             importance, difficulty, review_value,
             estimated_minutes, instruction, type, order_in_textbook, total_minutes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (problem_id, subject, textbook, textbook_id, section_id, problem_number,
              importance, difficulty, review_value,
              estimated_minutes, instruction, "標準", order_in_textbook, total_minutes))
        conn.commit()
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
        auto_sweep  = bool(arguments.get("auto_sweep", True))  # 省略時は従来どおり掃き込みあり
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
        auto_results = []
        if auto_sweep:
            try:
                from database import auto_record_unreported
                auto_results = auto_record_unreported(student_id, record_date)
            except Exception:
                auto_results = []
        return {
            "new_mastery": new_mastery,
            "mastery_stars": "★" * new_mastery,
            "score": score,
            "score_label": SCORE_LABELS.get(score, str(score)),
            "correct": correct,
            "auto_sweep": auto_sweep,
            "auto_recorded": auto_results,
        }

    elif name == "add_records":
        # 授業で実際に扱った複数問を、明示スコアで一括記録する。
        # sweep（未報告分の自動掃き込み）は既定でオフ。行うなら最後に高々1回。
        student_id  = arguments["student_id"]
        record_date = arguments.get("date", date.today().isoformat())
        auto_sweep  = bool(arguments.get("auto_sweep", False))
        records     = arguments.get("records") or []
        if not records:
            return {"error": "records が空です。[{problem_id, score}, ...] を指定してください"}
        for r in records:
            if "problem_id" not in r:
                return {"error": f"problem_id がない要素があります: {r}"}
        conn = get_connection()
        c = conn.cursor()
        results = []
        try:
            for r in records:
                problem_id = int(r["problem_id"])
                score = int(r.get("score", 5))
                c.execute("SELECT problem_number, textbook FROM problems WHERE problem_id=?", (problem_id,))
                p = c.fetchone()
                if not p:
                    raise ValueError(f"問題が見つかりません: problem_id={problem_id}（全件ロールバックしました）")
                # add_record と同様、過去のAuto記録は手動記録で上書き
                c.execute("""
                    DELETE FROM history
                    WHERE student_id=? AND problem_id=? AND category='Auto' AND date <= ?
                """, (student_id, problem_id, record_date))
                new_mastery = _calc_new_mastery_c(c, student_id, problem_id, score, record_date)
                correct = score_to_correct(score)
                c.execute("""
                    INSERT INTO history (student_id, problem_id, date, correct, mastery, category, score)
                    VALUES (?,?,?,?,?,?,?)
                """, (student_id, problem_id, record_date, correct, new_mastery, "Record", score))
                next_date = _update_assignments_after_record_c(
                    c, student_id, problem_id, record_date, new_mastery)
                results.append({
                    "problem_id": problem_id,
                    "problem_number": p["problem_number"],
                    "score": score,
                    "score_label": SCORE_LABELS.get(score, str(score)),
                    "correct": correct,
                    "new_mastery": new_mastery,
                    "mastery_stars": "★" * new_mastery,
                    "next_scheduled_date": next_date,
                })
            conn.commit()
        except Exception as e:
            conn.rollback()
            conn.close()
            return {"error": str(e)}
        conn.close()
        auto_results = []
        if auto_sweep:
            try:
                from database import auto_record_unreported
                auto_results = auto_record_unreported(student_id, record_date)
            except Exception:
                auto_results = []
        return {
            "recorded_count": len(results),
            "date": record_date,
            "records": results,
            "auto_sweep": auto_sweep,
            "auto_recorded": auto_results,
        }

    # ── 更新・削除系 ─────────────────────────────────────────────────────
    elif name == "update_problem":
        problem_id = arguments["problem_id"]
        conn = get_connection()
        c = conn.cursor()
        # problem_number を変更する場合は、同一テキスト内での重複を防ぐ
        if "problem_number" in arguments:
            c.execute("SELECT textbook_id FROM problems WHERE problem_id=?", (problem_id,))
            row = c.fetchone()
            if not row:
                conn.close()
                return {"error": f"問題が見つかりません: problem_id={problem_id}"}
            textbook_id = row["textbook_id"]
            c.execute("SELECT problem_id FROM problems WHERE textbook_id=? AND problem_number=? AND problem_id<>?",
                      (textbook_id, arguments["problem_number"], problem_id))
            dup = c.fetchone()
            if dup:
                conn.close()
                return {"error": f"同テキスト内に同名の問題が既にあります: problem_id={dup['problem_id']}, "
                                 f"problem_number={arguments['problem_number']}",
                        "conflict_problem_id": dup["problem_id"]}
        for field in ["problem_number", "importance", "difficulty", "review_value", "estimated_minutes", "instruction"]:
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

    elif name == "delete_record":
        # 誤記録の取り消し。confirm=true を付けない限り削除は実行せず対象のプレビューを返す。
        history_id = arguments.get("history_id")
        student_id = arguments.get("student_id")
        problem_id = arguments.get("problem_id")
        rec_date   = arguments.get("date")
        confirm    = bool(arguments.get("confirm", False))
        conn = get_connection()
        c = conn.cursor()
        if history_id:
            c.execute("""
                SELECT h.history_id, h.student_id, h.problem_id, h.date, h.score,
                       h.correct, h.mastery, h.category, p.problem_number, p.textbook
                FROM history h LEFT JOIN problems p ON h.problem_id=p.problem_id
                WHERE h.history_id=?
            """, (int(history_id),))
        elif student_id and problem_id and rec_date:
            c.execute("""
                SELECT h.history_id, h.student_id, h.problem_id, h.date, h.score,
                       h.correct, h.mastery, h.category, p.problem_number, p.textbook
                FROM history h LEFT JOIN problems p ON h.problem_id=p.problem_id
                WHERE h.student_id=? AND h.problem_id=? AND h.date=?
            """, (student_id, int(problem_id), rec_date))
        else:
            conn.close()
            return {"error": "history_id か、student_id+problem_id+date のどちらかを指定してください"}
        targets = [dict(r) for r in c.fetchall()]
        if not targets:
            conn.close()
            return {"error": "該当する記録が見つかりません"}
        if not confirm:
            conn.close()
            return {
                "requires_confirm": True,
                "message": "以下の記録を削除します。実行するには confirm=true を付けて再度呼んでください。",
                "targets": targets,
            }
        del_student = targets[0]["student_id"]
        del_problem = targets[0]["problem_id"]
        del_date    = min(t["date"] for t in targets)
        c.execute(f"DELETE FROM history WHERE history_id IN ({','.join('?'*len(targets))})",
                  [t["history_id"] for t in targets])
        conn.commit()
        conn.close()
        # 残った履歴から mastery を再計算して整合させる。
        # 削除行より前の履歴は保存値を正とし書き換えない（削除の影響範囲だけを再計算）
        from database import recalc_mastery_from_history, update_assignments_after_record
        recalc = recalc_mastery_from_history(del_student, del_problem, since_date=del_date)
        # 出題予定の復元:
        #  - 履歴が残っていれば、最新の残存記録の日付＋再計算後mastery で次回出題日を引き直す
        #  - 履歴が空になったら「未学習」に戻ったとみなし、削除した記録の日付で
        #    category='New' の出題予定を復元する（元カテゴリは復元不能のため要確認）
        conn = get_connection()
        c = conn.cursor()
        restored = None
        if recalc["latest_mastery"] is not None:
            c.execute("SELECT date FROM history WHERE student_id=? AND problem_id=? ORDER BY date DESC, history_id DESC LIMIT 1",
                      (del_student, del_problem))
            latest_date = c.fetchone()["date"]
            conn.close()
            update_assignments_after_record(del_student, del_problem, latest_date, recalc["latest_mastery"])
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT scheduled_date, category FROM assignments WHERE student_id=? AND problem_id=? ORDER BY assignment_id DESC LIMIT 1",
                      (del_student, del_problem))
            row = c.fetchone()
            restored = dict(row) if row else None
            conn.close()
        else:
            c.execute("DELETE FROM assignments WHERE student_id=? AND problem_id=?",
                      (del_student, del_problem))
            c.execute("INSERT INTO assignments (student_id, problem_id, scheduled_date, category) VALUES (?,?,?,?)",
                      (del_student, del_problem, del_date, "New"))
            conn.commit()
            conn.close()
            restored = {"scheduled_date": del_date, "category": "New",
                        "note": "履歴が空になったため未学習として復元。元カテゴリがNew以外なら update_assignment_category で修正してください"}
        return {
            "status": "ok",
            "deleted": targets,
            "mastery_recalc": recalc,
            "restored_assignment": restored,
        }

    elif name == "recalc_mastery":
        # history から mastery を再計算して整合させる（delete_record が内部で行う処理の単体版）
        student_id = arguments["student_id"]
        problem_id = int(arguments["problem_id"])
        from database import recalc_mastery_from_history
        result = recalc_mastery_from_history(student_id, problem_id)
        if result["rows"] == 0:
            return {"status": "ok", "message": "履歴がありません", **result}
        return {"status": "ok", "student_id": student_id, "problem_id": problem_id, **result,
                "mastery_stars": "★" * (result["latest_mastery"] or 0)}

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
