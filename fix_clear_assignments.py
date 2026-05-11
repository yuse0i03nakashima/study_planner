import sqlite3
import os

DB_PATH = r"C:\Users\ynaka\study_planner\study_planner.db"

# ─── 1. 対象のassignmentsを削除 ────────────────────────
problem_ids = [
    113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125,
    126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138,
    139, 140, 141
]

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

placeholders = ",".join(["?"] * len(problem_ids))
c.execute(f"""
    DELETE FROM assignments
    WHERE student_id='S003'
    AND problem_id IN ({placeholders})
    AND category='予習'
""", problem_ids)

print(f"✅ {c.rowcount}件の出題予定を削除しました")
conn.commit()
conn.close()

# ─── 2. mcp_server.pyのupdate_assignment_dateを修正 ────
mcp_path = r"C:\Users\ynaka\study_planner\mcp_server.py"
with open(mcp_path, "r", encoding="utf-8") as f:
    content = f.read()

old = '''        Tool(
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
        ),'''

new = '''        Tool(
            name="update_assignment_date",
            description="出題予定の予習日を変更または削除する。scheduled_dateを空文字にすると出題予定ごと削除（予習日未定に戻す）。",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"},
                    "problem_id": {"type": "integer", "description": "問題ID"},
                    "scheduled_date": {"type": "string", "description": "新しい予習日（YYYY-MM-DD形式）。空文字を指定すると出題予定を削除して未定に戻す。"},
                    "category": {"type": "string", "description": "出題区分（予習/復習/定着/再定着）省略時は予習"}
                },
                "required": ["student_id", "problem_id", "scheduled_date"]
            }
        ),'''

content = content.replace(old, new)

old_impl = '''    elif name == "update_assignment_date":
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
                text=f"対象の出題予定が見つかりません。add_assignmentで新規追加してください。")]'''

new_impl = '''    elif name == "update_assignment_date":
        student_id = arguments["student_id"]
        problem_id = arguments["problem_id"]
        scheduled_date = arguments["scheduled_date"].strip()
        category = arguments.get("category", "予習")
        conn = get_connection()
        c = conn.cursor()
        if not scheduled_date:
            # 空文字の場合は出題予定を削除（予習日未定に戻す）
            c.execute("""
                DELETE FROM assignments
                WHERE student_id=? AND problem_id=? AND category=?
            """, (student_id, problem_id, category))
            conn.commit()
            conn.close()
            return [TextContent(type="text",
                text=f"問題ID {problem_id} の出題予定を削除しました（予習日未定に戻しました）")]
        else:
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
                    text=f"対象の出題予定が見つかりません。add_assignmentで新規追加してください。")]'''

content = content.replace(old_impl, new_impl)

with open(mcp_path, "w", encoding="utf-8") as f:
    f.write(content)
print("✅ mcp_server.py を更新しました")
print("✅ 完了")