import os

base = r"C:\Users\ynaka\study_planner"
mcp_path = os.path.join(base, "mcp_server.py")

with open(mcp_path, "r", encoding="utf-8") as f:
    content = f.read()

# ─── ツール定義を追加 ────────────────────────────────
old_last_tool = '''        Tool(
            name="generate_pdf_plan",'''

new_tools = '''        Tool(
            name="get_series",
            description="シリーズ一覧を取得する",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="add_series",
            description="新しいシリーズを登録する",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "シリーズ名"},
                    "description": {"type": "string", "description": "説明（任意）"}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="get_textbooks",
            description="テキスト一覧を取得する。生徒IDで絞り込み可能。",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID（任意）"},
                    "subject": {"type": "string", "description": "教科（任意）"}
                }
            }
        ),
        Tool(
            name="add_textbook",
            description="新しいテキストを登録する",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "テキスト名"},
                    "subject": {"type": "string", "description": "教科"},
                    "series_id": {"type": "integer", "description": "シリーズID（任意）"},
                    "student_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "紐づける生徒IDのリスト（任意）"
                    }
                },
                "required": ["name", "subject"]
            }
        ),
        Tool(
            name="get_suppression_list",
            description="指定した生徒の現在抑制中の問題一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"}
                },
                "required": ["student_id"]
            }
        ),
        Tool(
            name="clear_suppression",
            description="特定の問題の抑制を手動で解除する",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"},
                    "problem_id": {"type": "integer", "description": "問題ID"}
                },
                "required": ["student_id", "problem_id"]
            }
        ),
        Tool(
            name="generate_pdf_plan",'''

content = content.replace(old_last_tool, new_tools)

# ─── ツール実装を追加 ────────────────────────────────
old_impl = '''    elif name == "generate_excel_plan":'''

new_impls = '''    elif name == "get_series":
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT s.series_id, s.name, s.description,
                   COUNT(t.textbook_id) as textbook_count
            FROM series s
            LEFT JOIN textbooks t ON s.series_id = t.series_id
            GROUP BY s.series_id ORDER BY s.name
        """)
        rows = c.fetchall()
        conn.close()
        return [TextContent(type="text", text=json.dumps(
            [dict(r) for r in rows], ensure_ascii=False, indent=2))]

    elif name == "add_series":
        name_val = arguments["name"]
        description = arguments.get("description", "")
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO series (name, description) VALUES (?, ?)",
                  (name_val, description))
        conn.commit()
        series_id = c.lastrowid
        conn.close()
        return [TextContent(type="text",
            text=f"シリーズ「{name_val}」を登録しました（series_id: {series_id}）")]

    elif name == "get_textbooks":
        conn = get_connection()
        c = conn.cursor()
        student_id = arguments.get("student_id")
        subject = arguments.get("subject")
        if student_id:
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
        elif subject:
            c.execute("""
                SELECT t.textbook_id, t.name, t.subject,
                       s.name as series_name,
                       COUNT(DISTINCT p.problem_id) as problem_count
                FROM textbooks t
                LEFT JOIN series s ON t.series_id = s.series_id
                LEFT JOIN problems p ON t.textbook_id = p.textbook_id
                WHERE t.subject=?
                GROUP BY t.textbook_id ORDER BY t.name
            """, (subject,))
        else:
            c.execute("""
                SELECT t.textbook_id, t.name, t.subject,
                       s.name as series_name,
                       COUNT(DISTINCT p.problem_id) as problem_count
                FROM textbooks t
                LEFT JOIN series s ON t.series_id = s.series_id
                LEFT JOIN problems p ON t.textbook_id = p.textbook_id
                GROUP BY t.textbook_id ORDER BY t.subject, t.name
            """)
        rows = c.fetchall()
        conn.close()
        return [TextContent(type="text", text=json.dumps(
            [dict(r) for r in rows], ensure_ascii=False, indent=2))]

    elif name == "add_textbook":
        name_val = arguments["name"]
        subject = arguments["subject"]
        series_id = arguments.get("series_id")
        student_ids = arguments.get("student_ids", [])
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO textbooks (series_id, name, subject)
            VALUES (?, ?, ?)
        """, (series_id, name_val, subject))
        conn.commit()
        textbook_id = c.lastrowid
        for sid in student_ids:
            c.execute("""
                INSERT OR IGNORE INTO student_textbooks (student_id, textbook_id)
                VALUES (?, ?)
            """, (sid, textbook_id))
        conn.commit()
        conn.close()
        return [TextContent(type="text",
            text=f"テキスト「{name_val}」を登録しました（textbook_id: {textbook_id}）")]

    elif name == "get_suppression_list":
        student_id = arguments["student_id"]
        conn = get_connection()
        c = conn.cursor()
        today = date.today().isoformat()
        c.execute("""
            SELECT s.problem_id, s.suppressed_until, s.reason,
                   p.subject, p.textbook, p.problem_number
            FROM suppression s
            JOIN problems p ON s.problem_id = p.problem_id
            WHERE s.student_id=? AND s.suppressed_until >= ?
            ORDER BY s.suppressed_until
        """, (student_id, today))
        rows = c.fetchall()
        conn.close()
        if not rows:
            return [TextContent(type="text", text="抑制中の問題はありません")]
        return [TextContent(type="text", text=json.dumps(
            [dict(r) for r in rows], ensure_ascii=False, indent=2))]

    elif name == "clear_suppression":
        from database import clear_suppression
        student_id = arguments["student_id"]
        problem_id = arguments["problem_id"]
        clear_suppression(student_id, problem_id)
        return [TextContent(type="text",
            text=f"問題ID {problem_id} の抑制を解除しました")]

    elif name == "generate_excel_plan":'''

content = content.replace(old_impl, new_impls)

with open(mcp_path, "w", encoding="utf-8") as f:
    f.write(content)
print("✅ mcp_server.py を更新しました")
print("✅ Step4完了")