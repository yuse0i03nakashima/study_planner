import os

base = r"C:\Users\ynaka\study_planner"
mcp_path = os.path.join(base, "mcp_server.py")

with open(mcp_path, "r", encoding="utf-8") as f:
    content = f.read()

# ツール定義を追加
old_tool = '''        Tool(
            name="generate_excel_plan",'''

new_tool = '''        Tool(
            name="update_assignment_date",
            description="出題予定の予習日を変更する。問題IDと生徒IDを指定して予習日を更新する。",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"},
                    "problem_id": {"type": "integer", "description": "問題ID"},
                    "scheduled_date": {"type": "string", "description": "新しい予習日（YYYY-MM-DD形式）"},
                    "category": {"type": "string", "description": "出題区分（予習/復習/定着/再定着）省略時は予習"}
                },
                "required": ["student_id", "problem_id", "scheduled_date"]
            }
        ),
        Tool(
            name="add_assignment",
            description="問題マスタに登録済みの問題を生徒の出題予定に追加する。予習日が未設定の問題に後から日付を設定する場合に使う。",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"},
                    "problem_id": {"type": "integer", "description": "問題ID"},
                    "scheduled_date": {"type": "string", "description": "予習日（YYYY-MM-DD形式）"},
                    "category": {"type": "string", "description": "出題区分（予習/復習/定着/再定着）省略時は予習"}
                },
                "required": ["student_id", "problem_id", "scheduled_date"]
            }
        ),
        Tool(
            name="generate_excel_plan",'''

content = content.replace(old_tool, new_tool)

# ツール実装を追加
old_impl = '''    elif name == "generate_excel_plan":'''

new_impl = '''    elif name == "update_assignment_date":
        student_id = arguments["student_id"]
        problem_id = arguments["problem_id"]
        scheduled_date = arguments["scheduled_date"]
        category = arguments.get("category", "予習")
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            UPDATE assignments SET scheduled_date=?, category=?
            WHERE student_id=? AND problem_id=?
        """, (scheduled_date, category, student_id, problem_id))
        updated = c.rowcount
        conn.commit()
        conn.close()
        if updated:
            return [TextContent(type="text",
                text=f"問題ID {problem_id} の予習日を {scheduled_date} に更新しました")]
        else:
            return [TextContent(type="text",
                text=f"対象の出題予定が見つかりません。add_assignmentで新規追加してください。")]

    elif name == "add_assignment":
        student_id = arguments["student_id"]
        problem_id = arguments["problem_id"]
        scheduled_date = arguments["scheduled_date"]
        category = arguments.get("category", "予習")
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
            VALUES (?, ?, ?, ?)
        """, (student_id, problem_id, scheduled_date, category))
        conn.commit()
        conn.close()
        return [TextContent(type="text",
            text=f"問題ID {problem_id} を {student_id} の出題予定（{scheduled_date}・{category}）に追加しました")]

    elif name == "generate_excel_plan":'''

content = content.replace(old_impl, new_impl)

with open(mcp_path, "w", encoding="utf-8") as f:
    f.write(content)
print("✅ mcp_server.py を更新しました")
print("✅ 追加ツール：update_assignment_date / add_assignment")