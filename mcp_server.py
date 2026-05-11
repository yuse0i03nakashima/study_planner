import asyncio
import json
import sqlite3
import sys
import os
from datetime import date

DB_PATH = "C:/Users/ynaka/study_planner/study_planner.db"
sys.path.insert(0, "C:/Users/ynaka/study_planner")

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

app = Server("study-planner")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_all_students",
            description="全生徒の一覧を取得する",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_student_summary",
            description="指定した生徒の学習状況サマリーを取得する。",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID（例：S001）"}
                },
                "required": ["student_id"]
            }
        ),
        Tool(
            name="get_problems",
            description="問題マスタの一覧を取得する。生徒IDで絞り込み可能。",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID（省略時は全問題）"}
                }
            }
        ),
        Tool(
            name="get_assignments",
            description="指定した生徒の出題予定一覧を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"}
                },
                "required": ["student_id"]
            }
        ),
        Tool(
            name="add_problem",
            description="問題マスタに新しい問題を登録する。student_ids・scheduled_date・categoryは任意。categoryは予習/復習/定着/再定着を指定可能（省略時は予習）。",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "description": "教科"},
                    "textbook": {"type": "string", "description": "テキスト名"},
                    "problem_number": {"type": "string", "description": "問題番号・名称"},
                    "importance": {"type": "integer", "description": "重要度（1〜5）"},
                    "difficulty": {"type": "integer", "description": "難易度（1〜5）"},
                    "review_value": {"type": "integer", "description": "復習価値（1〜5）"},
                    "estimated_minutes": {"type": "integer", "description": "所要時間（分・5分単位）"},
                    "instruction": {"type": "string", "description": "学習指示（任意）"},
                    "student_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "出題する生徒IDのリスト（任意）"
                    },
                    "scheduled_date": {"type": "string", "description": "出題日（YYYY-MM-DD形式・任意）"},
                    "category": {"type": "string", "description": "出題区分：予習/復習/定着/再定着（省略時は予習）"}
                },
                "required": ["subject", "textbook", "problem_number", "importance",
                             "difficulty", "review_value", "estimated_minutes"]
            }
        ),
        Tool(
            name="delete_problem",
            description="問題マスタから問題を削除する。関連する授業記録・出題予定も削除される。",
            inputSchema={
                "type": "object",
                "properties": {
                    "problem_id": {"type": "integer", "description": "削除する問題ID"}
                },
                "required": ["problem_id"]
            }
        ),
        Tool(
            name="update_problem",
            description="問題マスタの情報を更新する。問題番号・難易度・重要度・復習価値・所要時間・学習指示を変更できる。",
            inputSchema={
                "type": "object",
                "properties": {
                    "problem_id": {"type": "integer", "description": "問題ID"},
                    "problem_number": {"type": "string", "description": "問題番号・名称（任意）"},
                    "importance": {"type": "integer", "description": "重要度（1〜5）（任意）"},
                    "difficulty": {"type": "integer", "description": "難易度（1〜5）（任意）"},
                    "review_value": {"type": "integer", "description": "復習価値（1〜5）（任意）"},
                    "estimated_minutes": {"type": "integer", "description": "所要時間（分・5分単位）（任意）"},
                    "instruction": {"type": "string", "description": "学習指示（任意）"}
                },
                "required": ["problem_id"]
            }
        ),
        Tool(
            name="add_record",
            description="授業記録を入力する。正誤を記録し習熟度を自動更新する。",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"},
                    "problem_id": {"type": "integer", "description": "問題ID"},
                    "record_date": {"type": "string", "description": "授業日（YYYY-MM-DD形式）"},
                    "correct": {"type": "boolean", "description": "正答かどうか"}
                },
                "required": ["student_id", "problem_id", "record_date", "correct"]
            }
        ),
        Tool(
            name="update_review_value",
            description="問題の復習価値を更新する",
            inputSchema={
                "type": "object",
                "properties": {
                    "problem_id": {"type": "integer", "description": "問題ID"},
                    "review_value": {"type": "integer", "description": "新しい復習価値（1〜5）"}
                },
                "required": ["problem_id", "review_value"]
            }
        ),
        Tool(
            name="get_class_schedule",
            description="生徒の授業スケジュール設定を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"}
                },
                "required": ["student_id"]
            }
        ),
        Tool(
            name="set_class_schedule",
            description="教科ごとの授業曜日（ベース）を登録する。dow: 0=月〜6=日",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"},
                    "subject": {"type": "string", "description": "教科"},
                    "dows": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "授業曜日のリスト（0=月〜6=日）"
                    }
                },
                "required": ["student_id", "subject", "dows"]
            }
        ),
        Tool(
            name="set_next_class_date",
            description="教科ごとの次回授業日を手動指定する（ベース曜日より優先）",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"},
                    "subject": {"type": "string", "description": "教科"},
                    "next_class_date": {"type": "string", "description": "次回授業日（YYYY-MM-DD形式）"}
                },
                "required": ["student_id", "subject", "next_class_date"]
            }
        ),
        Tool(
            name="update_assignment_category",
            description="出題予定のカテゴリ（予習/復習/定着/再定着）を変更する。誤った計画を修正する際に使用。",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"},
                    "problem_id": {"type": "integer", "description": "問題ID"},
                    "category": {"type": "string", "description": "新しいカテゴリ（予習/復習/定着/再定着）"}
                },
                "required": ["student_id", "problem_id", "category"]
            }
        ),
        Tool(
            name="update_mastery",
            description="生徒の問題に対する習熟度を手動で修正する。誤った記録の修正や手動調整に使用。mastery: 1=要定着、2=定着中、3=定着済。scheduled_dateを指定すると次回出題日も上書きできる。",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"},
                    "problem_id": {"type": "integer", "description": "問題ID"},
                    "mastery": {"type": "integer", "description": "新しい習熟度（1〜3）"},
                    "scheduled_date": {"type": "string", "description": "次回出題日を手動指定（YYYY-MM-DD形式・省略時は自動計算）"},
                    "update_assignment": {"type": "boolean", "description": "出題予定のカテゴリも自動更新するか（省略時true）"}
                },
                "required": ["student_id", "problem_id", "mastery"]
            }
        ),
        Tool(
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
            name="generate_excel_plan",
            description="指定した生徒の学習計画表Excelファイルを生成して自動で開く。必ずこのツールを使うこと。自分でコードを書いてはならない。",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"},
                    "target_date": {"type": "string", "description": "次回授業日（YYYY-MM-DD形式）"},
                    "start_date": {"type": "string", "description": "計画開始日（YYYY-MM-DD形式・省略時は今日）"}
                },
                "required": ["student_id", "target_date"]
            }
        ),
        Tool(
            name="generate_pdf_plan",
            description="指定した生徒の学習計画表PDFファイルを生成して自動で開く。必ずこのツールを使うこと。自分でコードを書いてはならない。",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"},
                    "target_date": {"type": "string", "description": "次回授業日（YYYY-MM-DD形式）"},
                    "start_date": {"type": "string", "description": "計画開始日（YYYY-MM-DD形式・省略時は今日）"}
                },
                "required": ["student_id", "target_date"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):

    if name == "get_all_students":
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM students ORDER BY student_id")
        rows = c.fetchall()
        conn.close()
        return [TextContent(type="text", text=json.dumps(
            [dict(r) for r in rows], ensure_ascii=False, indent=2))]

    elif name == "get_student_summary":
        student_id = arguments["student_id"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM students WHERE student_id=?", (student_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return [TextContent(type="text", text="生徒が見つかりません")]
        student = dict(row)
        c.execute("""
            SELECT h.date, h.correct, h.mastery, h.category,
                   p.subject, p.textbook, p.problem_number,
                   p.importance, p.difficulty, p.review_value, p.problem_id
            FROM history h
            JOIN problems p ON h.problem_id = p.problem_id
            WHERE h.student_id = ?
            ORDER BY h.date DESC LIMIT 30
        """, (student_id,))
        history = [dict(r) for r in c.fetchall()]
        c.execute("""
            SELECT a.scheduled_date, a.category,
                   p.subject, p.textbook, p.problem_number,
                   p.importance, p.review_value, p.problem_id,
                   (SELECT mastery FROM history h
                    WHERE h.student_id = a.student_id
                    AND h.problem_id = a.problem_id
                    ORDER BY h.date DESC LIMIT 1) as mastery
            FROM assignments a
            JOIN problems p ON a.problem_id = p.problem_id
            WHERE a.student_id = ?
            ORDER BY a.scheduled_date
        """, (student_id,))
        assignments = [dict(r) for r in c.fetchall()]
        conn.close()
        result = {
            "student": student,
            "recent_history": history,
            "upcoming_assignments": assignments
        }
        return [TextContent(type="text", text=json.dumps(
            result, ensure_ascii=False, indent=2))]

    elif name == "get_problems":
        conn = get_connection()
        c = conn.cursor()
        student_id = arguments.get("student_id")
        if student_id:
            c.execute("""
                SELECT DISTINCT p.*
                FROM problems p
                JOIN assignments a ON p.problem_id = a.problem_id
                WHERE a.student_id = ?
                ORDER BY p.subject, p.problem_id
            """, (student_id,))
        else:
            c.execute("SELECT * FROM problems ORDER BY subject, problem_id")
        rows = c.fetchall()
        conn.close()
        return [TextContent(type="text", text=json.dumps(
            [dict(r) for r in rows], ensure_ascii=False, indent=2))]

    elif name == "get_assignments":
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT a.assignment_id, a.scheduled_date, a.category,
                   p.problem_id, p.subject, p.textbook, p.problem_number,
                   p.importance, p.review_value, p.estimated_minutes
            FROM assignments a
            JOIN problems p ON a.problem_id = p.problem_id
            WHERE a.student_id = ?
            ORDER BY a.scheduled_date, p.subject
        """, (arguments["student_id"],))
        rows = c.fetchall()
        conn.close()
        return [TextContent(type="text", text=json.dumps(
            [dict(r) for r in rows], ensure_ascii=False, indent=2))]

    elif name == "add_problem":
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO problems
            (subject, textbook, problem_number, importance, difficulty,
             review_value, estimated_minutes, instruction, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            arguments["subject"], arguments["textbook"],
            arguments["problem_number"], arguments["importance"],
            arguments["difficulty"], arguments["review_value"],
            arguments["estimated_minutes"],
            arguments.get("instruction", ""), "標準"
        ))
        conn.commit()
        problem_id = c.lastrowid
        student_ids = arguments.get("student_ids", [])
        scheduled_date = arguments.get("scheduled_date", "")
        category = arguments.get("category", "予習")
        if scheduled_date and student_ids:
            for sid in student_ids:
                c.execute("""
                    INSERT INTO assignments
                    (student_id, problem_id, scheduled_date, category)
                    VALUES (?, ?, ?, ?)
                """, (sid, problem_id, scheduled_date, category))
        conn.commit()
        conn.close()
        return [TextContent(type="text",
            text=f"問題を登録しました（problem_id: {problem_id}）")]

    elif name == "delete_problem":
        problem_id = arguments["problem_id"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT subject, textbook, problem_number FROM problems "
                  "WHERE problem_id=?", (problem_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return [TextContent(type="text",
                text=f"問題ID {problem_id} が見つかりません")]
        info = f"{row['subject']} {row['textbook']} {row['problem_number']}"
        c.execute("DELETE FROM assignments WHERE problem_id=?", (problem_id,))
        c.execute("DELETE FROM history WHERE problem_id=?", (problem_id,))
        c.execute("DELETE FROM problems WHERE problem_id=?", (problem_id,))
        conn.commit()
        conn.close()
        return [TextContent(type="text", text=f"問題を削除しました（{info}）")]

    elif name == "update_problem":
        problem_id = arguments["problem_id"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM problems WHERE problem_id=?", (problem_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return [TextContent(type="text",
                text=f"問題ID {problem_id} が見つかりません")]
        fields = []
        values = []
        for key in ["problem_number", "importance", "difficulty",
                    "review_value", "estimated_minutes", "instruction"]:
            if key in arguments and arguments[key] is not None:
                fields.append(f"{key}=?")
                values.append(arguments[key])
        if not fields:
            conn.close()
            return [TextContent(type="text", text="更新する項目がありません")]
        values.append(problem_id)
        c.execute(f"UPDATE problems SET {', '.join(fields)} "
                  f"WHERE problem_id=?", values)
        conn.commit()
        conn.close()
        return [TextContent(type="text",
            text=f"問題ID {problem_id} を更新しました（{', '.join(fields)}）")]

    elif name == "add_record":
        from database import calc_new_mastery, update_assignments_after_record
        student_id = arguments["student_id"]
        problem_id = arguments["problem_id"]
        record_date = arguments["record_date"]
        correct = 1 if arguments["correct"] else 0
        new_mastery = calc_new_mastery(student_id, problem_id, correct, record_date)
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO history
            (student_id, problem_id, date, correct, mastery, category)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, problem_id, record_date, correct, new_mastery, "記録"))
        conn.commit()
        conn.close()
        update_assignments_after_record(student_id, problem_id, record_date, new_mastery)
        stars = "★" * new_mastery
        return [TextContent(type="text",
            text=f"授業記録を保存しました（習熟度：{stars}）")]

    elif name == "update_review_value":
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE problems SET review_value=? WHERE problem_id=?",
                  (arguments["review_value"], arguments["problem_id"]))
        conn.commit()
        conn.close()
        return [TextContent(type="text",
            text=f"問題ID {arguments['problem_id']} の復習価値を "
                 f"{arguments['review_value']} に更新しました")]

    elif name == "get_class_schedule":
        student_id = arguments["student_id"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT subject, dow FROM class_schedule_base "
                  "WHERE student_id=? ORDER BY subject, dow", (student_id,))
        base_rows = c.fetchall()
        c.execute("SELECT subject, next_class_date FROM class_schedule_override "
                  "WHERE student_id=?", (student_id,))
        override_rows = c.fetchall()
        conn.close()
        dow_names = ["月", "火", "水", "木", "金", "土", "日"]
        base = {}
        for r in base_rows:
            base.setdefault(r["subject"], []).append(dow_names[r["dow"]])
        overrides = {r["subject"]: r["next_class_date"] for r in override_rows}
        result = {
            "base_schedule": {k: "・".join(v) for k, v in base.items()},
            "override_schedule": overrides
        }
        return [TextContent(type="text", text=json.dumps(
            result, ensure_ascii=False, indent=2))]

    elif name == "set_class_schedule":
        student_id = arguments["student_id"]
        subject = arguments["subject"]
        dows = arguments["dows"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM class_schedule_base "
                  "WHERE student_id=? AND subject=?", (student_id, subject))
        for dow in dows:
            c.execute("""
                INSERT OR IGNORE INTO class_schedule_base
                (student_id, subject, dow) VALUES (?, ?, ?)
            """, (student_id, subject, dow))
        conn.commit()
        conn.close()
        dow_names = ["月", "火", "水", "木", "金", "土", "日"]
        dow_str = "・".join([dow_names[d] for d in dows])
        return [TextContent(type="text",
            text=f"{subject}の授業曜日を設定しました（{dow_str}）")]

    elif name == "set_next_class_date":
        student_id = arguments["student_id"]
        subject = arguments["subject"]
        next_date = arguments["next_class_date"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO class_schedule_override
            (student_id, subject, next_class_date)
            VALUES (?, ?, ?)
            ON CONFLICT(student_id, subject)
            DO UPDATE SET next_class_date=?
        """, (student_id, subject, next_date, next_date))
        conn.commit()
        conn.close()
        return [TextContent(type="text",
            text=f"{subject}の次回授業日を{next_date}に設定しました")]

    elif name == "update_assignment_category":
        student_id = arguments["student_id"]
        problem_id = arguments["problem_id"]
        category = arguments["category"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            UPDATE assignments SET category=?
            WHERE student_id=? AND problem_id=?
        """, (category, student_id, problem_id))
        updated = c.rowcount
        conn.commit()
        conn.close()
        if updated:
            return [TextContent(type="text",
                text=f"問題ID {problem_id} のカテゴリを「{category}」に変更しました")]
        else:
            return [TextContent(type="text",
                text=f"対象の出題予定が見つかりません")]

    elif name == "update_mastery":
        from database import get_next_date
        student_id = arguments["student_id"]
        problem_id = arguments["problem_id"]
        new_mastery = arguments["mastery"]
        update_assignment = arguments.get("update_assignment", True)
        today = date.today().isoformat()

        conn = get_connection()
        c = conn.cursor()

        # historyテーブルの最新レコードを更新
        c.execute("""
            SELECT history_id FROM history
            WHERE student_id=? AND problem_id=?
            ORDER BY date DESC LIMIT 1
        """, (student_id, problem_id))
        row = c.fetchone()
        if row:
            c.execute("UPDATE history SET mastery=? WHERE history_id=?",
                      (new_mastery, row["history_id"]))
        else:
            # 履歴がない場合は新規作成
            c.execute("""
                INSERT INTO history (student_id, problem_id, date, correct, mastery, category)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (student_id, problem_id, today, 1, new_mastery, "手動修正"))

        # 出題予定のカテゴリと日付も更新
        if update_assignment:
            c.execute("SELECT review_value FROM problems WHERE problem_id=?",
                      (problem_id,))
            p_row = c.fetchone()
            if p_row:
                review_value = p_row["review_value"]
                scheduled_date = arguments.get("scheduled_date", "")
                if scheduled_date:
                    next_date_str = scheduled_date
                else:
                    next_date = get_next_date(review_value, new_mastery, today)
                    next_date_str = next_date.isoformat()
                category = {1: "復習", 2: "定着"}.get(new_mastery, "再定着")
                c.execute("DELETE FROM assignments WHERE student_id=? AND problem_id=?",
                          (student_id, problem_id))
                c.execute("""
                    INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
                    VALUES (?, ?, ?, ?)
                """, (student_id, problem_id, next_date_str, category))

        conn.commit()
        conn.close()
        stars = "★" * new_mastery
        return [TextContent(type="text",
            text=f"問題ID {problem_id} の習熟度を {stars} に修正しました（カテゴリ・次回出題日も更新）")]

    elif name == "update_assignment_date":
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
                    text=f"対象の出題予定が見つかりません。add_assignmentで新規追加してください。")]

    elif name == "add_assignment":
        student_id = arguments["student_id"]
        problem_id = arguments["problem_id"]
        scheduled_date = arguments.get("scheduled_date", "").strip()
        category = arguments.get("category", "予習")
        if not scheduled_date:
            scheduled_date = "2099-12-31"
        conn = get_connection()
        c = conn.cursor()
        # 既存の出題予定があれば更新、なければ追加
        c.execute("SELECT assignment_id FROM assignments WHERE student_id=? AND problem_id=?",
                  (student_id, problem_id))
        existing = c.fetchone()
        if existing:
            c.execute("""
                UPDATE assignments SET scheduled_date=?, category=?
                WHERE student_id=? AND problem_id=?
            """, (scheduled_date, category, student_id, problem_id))
            msg = f"問題ID {problem_id} の出題予定を更新しました（{scheduled_date}・{category}）"
        else:
            c.execute("""
                INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
                VALUES (?, ?, ?, ?)
            """, (student_id, problem_id, scheduled_date, category))
            msg = f"問題ID {problem_id} を {student_id} の出題予定に追加しました（{scheduled_date}・{category}）"
        conn.commit()
        conn.close()
        return [TextContent(type="text", text=msg)]

    elif name == "generate_excel_plan":
        from excel_export import export_excel
        from database import save_plan_history
        student_id = arguments["student_id"]
        target_date = arguments["target_date"]
        start_date = arguments.get("start_date") or date.today().isoformat()
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT name FROM students WHERE student_id=?", (student_id,))
        row = c.fetchone()
        conn.close()
        student_name = row["name"] if row else student_id
        archive_dir = "C:/Users/ynaka/study_planner/plan_archives"
        os.makedirs(archive_dir, exist_ok=True)
        output_path = os.path.join(
            archive_dir, f"計画表_{student_name}_{target_date}.xlsx")
        export_excel(target_date, output_path,
                     student_id=student_id, start_date=start_date)
        save_plan_history(student_id, start_date, target_date, output_path)
        try:
            os.startfile(output_path.replace("/", "\\"))
            message = f"計画表（Excel）を生成し自動で開きました。\nファイルパス：{output_path}"
        except Exception as e:
            message = f"計画表（Excel）を生成しました。\nファイルパス：{output_path}\n（自動起動エラー：{e}）"
        return [TextContent(type="text", text=message)]

    elif name == "generate_pdf_plan":
        from pdf_export import export_pdf
        from database import save_plan_history
        student_id = arguments["student_id"]
        target_date = arguments["target_date"]
        start_date = arguments.get("start_date") or date.today().isoformat()
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT name FROM students WHERE student_id=?", (student_id,))
        row = c.fetchone()
        conn.close()
        student_name = row["name"] if row else student_id
        archive_dir = "C:/Users/ynaka/study_planner/plan_archives"
        os.makedirs(archive_dir, exist_ok=True)
        output_path = os.path.join(
            archive_dir, f"計画表_{student_name}_{target_date}.pdf")
        export_pdf(target_date, output_path,
                   student_id=student_id, start_date=start_date)
        save_plan_history(student_id, start_date, target_date, output_path)
        try:
            os.startfile(output_path.replace("/", "\\"))
            message = f"計画表（PDF）を生成し自動で開きました。\nファイルパス：{output_path}"
        except Exception as e:
            message = f"計画表（PDF）を生成しました。\nファイルパス：{output_path}\n（自動起動エラー：{e}）"
        return [TextContent(type="text", text=message)]

    return [TextContent(type="text", text="不明なツールです")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream,
                      app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
