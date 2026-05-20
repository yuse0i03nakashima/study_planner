import asyncio
import json
import sqlite3
import sys
import os
from datetime import date, timedelta

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


def get_auto_next_class_date(student_id, subject):
    """授業曜日から今日以降の最初の授業日を自動計算する"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT next_class_date FROM class_schedule_override
        WHERE student_id=? AND subject=?
    """, (student_id, subject))
    row = c.fetchone()
    if row and row["next_class_date"]:
        conn.close()
        return row["next_class_date"]
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


def score_to_correct(score):
    return 1 if score >= 4 else 0


def calc_new_mastery(student_id, problem_id, score, record_date):
    """5段階スコアから新しい習熟度を計算する"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT mastery FROM history
        WHERE student_id=? AND problem_id=?
        ORDER BY date DESC LIMIT 1
    """, (student_id, problem_id))
    row = c.fetchone()
    current_mastery = row["mastery"] if row else 1

    if score == 3:
        conn.close()
        return current_mastery

    correct = score_to_correct(score)

    if correct == 0:
        new_mastery = max(1, current_mastery - 1)
        conn.close()
        return new_mastery

    # 正答の場合：昇格判定
    if current_mastery >= 3:
        conn.close()
        return 3

    if current_mastery == 1:
        c.execute("""
            SELECT COUNT(*) as cnt FROM history
            WHERE student_id=? AND problem_id=? AND correct=1
            AND date < ?
        """, (student_id, problem_id, record_date))
        cnt = c.fetchone()["cnt"]
        new_mastery = 2 if cnt >= 1 else 1

    elif current_mastery == 2:
        c.execute("""
            SELECT date FROM history
            WHERE student_id=? AND problem_id=? AND correct=1
            ORDER BY date DESC LIMIT 3
        """, (student_id, problem_id))
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
            description="指定した生徒の学習状況サマリー（直近30件の授業記録・出題予定）を取得する",
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
            description="問題マスタの一覧を取得する。student_idで生徒に紐づく問題のみに絞り込み可能",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID（省略時は全問題）"},
                    "subject":    {"type": "string", "description": "教科（省略時は全教科）"}
                }
            }
        ),
        Tool(
            name="get_assignments",
            description="指定した生徒の出題予定一覧を取得する。scheduled_date=2099-12-31は授業日未定の問題",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"}
                },
                "required": ["student_id"]
            }
        ),
        Tool(
            name="get_series",
            description="テキストシリーズの一覧を取得する",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_textbooks",
            description="テキストの一覧を取得する。subject指定で絞り込み可能",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "description": "教科（省略時は全テキスト）"}
                }
            }
        ),
        Tool(
            name="get_class_schedule",
            description="生徒の授業スケジュール（授業曜日・次回授業日）を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"}
                },
                "required": ["student_id"]
            }
        ),
        Tool(
            name="get_suppression_list",
            description="代表問題の抑制リスト（正答済みのため次回スキップする問題のID一覧）を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"}
                },
                "required": ["student_id"]
            }
        ),
        Tool(
            name="add_series",
            description="テキストシリーズを登録する",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "シリーズ名（例：青チャート）"}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="add_textbook",
            description="テキストを登録する。student_idを指定すると生徒との紐づけも同時に行う",
            inputSchema={
                "type": "object",
                "properties": {
                    "series_id":  {"type": "integer", "description": "シリーズID（任意）"},
                    "name":       {"type": "string",  "description": "テキスト名"},
                    "subject":    {"type": "string",  "description": "教科"},
                    "student_id": {"type": "string",  "description": "紐づける生徒ID（任意）"}
                },
                "required": ["name", "subject"]
            }
        ),
        Tool(
            name="add_problem",
            description=(
                "問題マスタに新しい問題を登録する。"
                "student_idsを指定すると出題予定も同時登録。"
                "scheduled_dateを省略すると授業曜日から次回授業日を自動計算。"
                "undecided=trueで授業日未定として登録（計画表に出さない）。"
                "order_in_textbookを省略すると同テキスト内の最大No.+1を自動設定。"
                "categoryは予習/復習/定着/再定着を指定可能（省略時は予習）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "subject":            {"type": "string",  "description": "教科"},
                    "textbook_id":        {"type": "integer", "description": "テキストID（get_textbooksで確認）"},
                    "problem_number":     {"type": "string",  "description": "問題番号・名称"},
                    "importance":         {"type": "integer", "description": "重要度（1〜5）"},
                    "difficulty":         {"type": "integer", "description": "難易度（1〜5）"},
                    "review_value":       {"type": "integer", "description": "復習価値（1〜5）。4以上が代表問題"},
                    "estimated_minutes":  {"type": "integer", "description": "所要時間（分・5分単位）"},
                    "instruction":        {"type": "string",  "description": "学習指示（任意）"},
                    "order_in_textbook":  {"type": "integer", "description": "テキスト内No.（省略→自動設定）"},
                    "student_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "出題する生徒IDのリスト（任意）"
                    },
                    "category":       {"type": "string",  "description": "カテゴリ：予習/復習/定着/再定着（省略時は予習）"},
                    "scheduled_date": {"type": "string",  "description": "出題日YYYY-MM-DD（省略→授業曜日から自動計算）"},
                    "undecided":      {"type": "boolean", "description": "true=授業日未定として登録（計画表に出さない）"},
                    "total_minutes":  {"type": "integer", "description": "総HP（省略=通常問題=1回完結）。古文精読など複数セッションに分割したい場合に設定。estimated_minutesより大きな値を設定する"}
                },
                "required": ["subject", "textbook_id", "problem_number",
                             "importance", "difficulty", "review_value", "estimated_minutes"]
            }
        ),
        Tool(
            name="add_assignment",
            description="既存の問題に出題予定を追加する。scheduled_dateを省略すると授業曜日から自動計算",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id":     {"type": "string",  "description": "生徒ID"},
                    "problem_id":     {"type": "integer", "description": "問題ID"},
                    "category":       {"type": "string",  "description": "カテゴリ：予習/復習/定着/再定着"},
                    "scheduled_date": {"type": "string",  "description": "出題日YYYY-MM-DD（省略→自動計算）"}
                },
                "required": ["student_id", "problem_id", "category"]
            }
        ),
        Tool(
            name="add_record",
            description=(
                "授業記録を登録し習熟度を自動更新する。"
                "score: 5=Perfect(正答), 4=Good(正答), 3=Review(変化なし), "
                "2=Retry(誤答), 1=Failed(誤答)。"
                "報告がない問題はscore=5として扱う。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string",  "description": "生徒ID"},
                    "problem_id": {"type": "integer", "description": "問題ID"},
                    "date":       {"type": "string",  "description": "授業日YYYY-MM-DD（省略時は今日）"},
                    "score":      {"type": "integer", "description": "評価スコア1〜5（省略時は5=Perfect）"}
                },
                "required": ["student_id", "problem_id"]
            }
        ),
        Tool(
            name="update_problem",
            description="問題のパラメータ（重要度・難易度・復習価値・所要時間・学習指示）を更新する",
            inputSchema={
                "type": "object",
                "properties": {
                    "problem_id":        {"type": "integer", "description": "問題ID"},
                    "importance":        {"type": "integer", "description": "重要度（1〜5）"},
                    "difficulty":        {"type": "integer", "description": "難易度（1〜5）"},
                    "review_value":      {"type": "integer", "description": "復習価値（1〜5）"},
                    "estimated_minutes": {"type": "integer", "description": "所要時間（分）"},
                    "instruction":       {"type": "string",  "description": "学習指示"}
                },
                "required": ["problem_id"]
            }
        ),
        Tool(
            name="delete_problem",
            description="問題を削除する。関連する出題予定・授業記録も削除される。慎重に使用すること",
            inputSchema={
                "type": "object",
                "properties": {
                    "problem_id": {"type": "integer", "description": "問題ID"}
                },
                "required": ["problem_id"]
            }
        ),
        Tool(
            name="update_assignment_date",
            description="出題予定の日付を変更する",
            inputSchema={
                "type": "object",
                "properties": {
                    "assignment_id":  {"type": "integer", "description": "出題予定ID"},
                    "scheduled_date": {"type": "string",  "description": "新しい出題日YYYY-MM-DD"}
                },
                "required": ["assignment_id", "scheduled_date"]
            }
        ),
        Tool(
            name="update_assignment_category",
            description="出題予定のカテゴリを変更する",
            inputSchema={
                "type": "object",
                "properties": {
                    "assignment_id": {"type": "integer", "description": "出題予定ID"},
                    "category":      {"type": "string",  "description": "新しいカテゴリ：予習/復習/定着/再定着"}
                },
                "required": ["assignment_id", "category"]
            }
        ),
        Tool(
            name="update_mastery",
            description="習熟度を手動で変更する（履歴に記録される）",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string",  "description": "生徒ID"},
                    "problem_id": {"type": "integer", "description": "問題ID"},
                    "mastery":    {"type": "integer", "description": "習熟度1〜3（★の数）"}
                },
                "required": ["student_id", "problem_id", "mastery"]
            }
        ),
        Tool(
            name="update_review_value",
            description="問題の復習価値を変更する",
            inputSchema={
                "type": "object",
                "properties": {
                    "problem_id":   {"type": "integer", "description": "問題ID"},
                    "review_value": {"type": "integer", "description": "復習価値1〜5（4以上が代表問題）"}
                },
                "required": ["problem_id", "review_value"]
            }
        ),
        Tool(
            name="set_class_schedule",
            description="授業曜日を設定する。既存設定を上書きする",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"},
                    "subject":    {"type": "string", "description": "教科"},
                    "dows": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "曜日リスト：mon/tue/wed/thu/fri/sat/sun"
                    }
                },
                "required": ["student_id", "subject", "dows"]
            }
        ),
        Tool(
            name="set_next_class_date",
            description="次回授業日を手動設定する。変則的な授業日のみ使用。省略/空文字でリセット（授業曜日から自動計算に戻る）",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id":      {"type": "string", "description": "生徒ID"},
                    "subject":         {"type": "string", "description": "教科"},
                    "next_class_date": {"type": "string", "description": "次回授業日YYYY-MM-DD（省略でリセット）"}
                },
                "required": ["student_id", "subject"]
            }
        ),
        Tool(
            name="clear_suppression",
            description="代表問題の抑制リストをリセットする",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"}
                },
                "required": ["student_id"]
            }
        ),
        Tool(
            name="generate_excel_plan",
            description="計画表をExcelファイルに出力する。plan_archivesフォルダに保存される。ブラウザUIから出力することを推奨",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id":     {"type": "string", "description": "生徒ID"},
                    "start_date":     {"type": "string", "description": "開始日YYYY-MM-DD（省略→今日）"},
                    "end_date":       {"type": "string", "description": "終了日YYYY-MM-DD（省略→次回授業日）"},
                    "subject_filter": {"type": "string", "description": "教科絞り込み（省略→全教科）"}
                },
                "required": ["student_id"]
            }
        ),
        Tool(
            name="auto_record_session",
            description=(
                "授業報告を受けた後、未報告の問題を自動登録する。"
                "難易度1〜3の問題はscore=5(Perfect)、難易度4〜5はscore=4(Good)で登録。"
                "通常はadd_recordを呼んだ時点で自動実行されるが、"
                "手動でまとめて実行したい場合に使用する。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id":   {"type": "string", "description": "生徒ID"},
                    "record_date":  {"type": "string",
                                    "description": "基準日YYYY-MM-DD（省略→今日）。この日以前の未報告問題を処理"}
                },
                "required": ["student_id"]
            }
        ),
        Tool(
            name="generate_pdf_plan",
            description="計画表をPDFファイルに出力する。plan_archivesフォルダに保存される。ブラウザUIから出力することを推奨",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id":     {"type": "string", "description": "生徒ID"},
                    "start_date":     {"type": "string", "description": "開始日YYYY-MM-DD（省略→今日）"},
                    "end_date":       {"type": "string", "description": "終了日YYYY-MM-DD（省略→次回授業日）"},
                    "subject_filter": {"type": "string", "description": "教科絞り込み（省略→全教科）"}
                },
                "required": ["student_id"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):

    # ── 参照系 ──────────────────────────────────────────
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
            SELECT h.date, h.correct, h.mastery, h.category, h.score,
                   p.subject, p.textbook, p.problem_number,
                   p.importance, p.difficulty, p.review_value, p.problem_id
            FROM history h
            JOIN problems p ON h.problem_id = p.problem_id
            WHERE h.student_id = ?
            ORDER BY h.date DESC LIMIT 30
        """, (student_id,))
        history = [dict(r) for r in c.fetchall()]
        c.execute("""
            SELECT a.assignment_id, a.scheduled_date, a.category,
                   p.problem_id, p.subject, p.textbook, p.problem_number,
                   p.importance, p.review_value, p.estimated_minutes,
                   p.order_in_textbook,
                   (SELECT mastery FROM history h
                    WHERE h.student_id = a.student_id
                    AND h.problem_id = a.problem_id
                    ORDER BY h.date DESC LIMIT 1) as mastery
            FROM assignments a
            JOIN problems p ON a.problem_id = p.problem_id
            WHERE a.student_id = ?
            ORDER BY a.scheduled_date, p.subject
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
        subject    = arguments.get("subject")
        query = """
            SELECT p.problem_id, p.subject, p.textbook, p.textbook_id,
                   p.problem_number, p.importance, p.difficulty,
                   p.review_value, p.estimated_minutes, p.instruction,
                   p.order_in_textbook
            FROM problems p
            WHERE 1=1
        """
        params = []
        if student_id:
            query += """
                AND p.problem_id IN (
                    SELECT problem_id FROM assignments WHERE student_id=?)
            """
            params.append(student_id)
        if subject:
            query += " AND p.subject=?"
            params.append(subject)
        query += " ORDER BY p.subject, p.order_in_textbook, p.problem_id"
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        return [TextContent(type="text", text=json.dumps(
            [dict(r) for r in rows], ensure_ascii=False, indent=2))]

    elif name == "get_assignments":
        student_id = arguments["student_id"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT a.assignment_id, a.scheduled_date, a.category,
                   p.problem_id, p.subject, p.textbook, p.problem_number,
                   p.importance, p.review_value, p.estimated_minutes,
                   p.order_in_textbook,
                   (SELECT mastery FROM history h
                    WHERE h.student_id = a.student_id
                    AND h.problem_id = a.problem_id
                    ORDER BY h.date DESC LIMIT 1) as mastery
            FROM assignments a
            JOIN problems p ON a.problem_id = p.problem_id
            WHERE a.student_id = ?
            ORDER BY a.scheduled_date, p.subject, p.order_in_textbook
        """, (student_id,))
        rows = c.fetchall()
        conn.close()
        return [TextContent(type="text", text=json.dumps(
            [dict(r) for r in rows], ensure_ascii=False, indent=2))]

    elif name == "get_series":
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT s.*, COUNT(t.textbook_id) as textbook_count
            FROM series s
            LEFT JOIN textbooks t ON s.series_id = t.series_id
            GROUP BY s.series_id ORDER BY s.name
        """)
        rows = c.fetchall()
        conn.close()
        return [TextContent(type="text", text=json.dumps(
            [dict(r) for r in rows], ensure_ascii=False, indent=2))]

    elif name == "get_textbooks":
        conn = get_connection()
        c = conn.cursor()
        subject = arguments.get("subject")
        if subject:
            c.execute("""
                SELECT t.*, s.name as series_name
                FROM textbooks t
                LEFT JOIN series s ON t.series_id = s.series_id
                WHERE t.subject=?
                ORDER BY s.name, t.name
            """, (subject,))
        else:
            c.execute("""
                SELECT t.*, s.name as series_name
                FROM textbooks t
                LEFT JOIN series s ON t.series_id = s.series_id
                ORDER BY t.subject, s.name, t.name
            """)
        rows = c.fetchall()
        conn.close()
        return [TextContent(type="text", text=json.dumps(
            [dict(r) for r in rows], ensure_ascii=False, indent=2))]

    elif name == "get_class_schedule":
        student_id = arguments["student_id"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT subject, dow FROM class_schedule_base WHERE student_id=?",
                  (student_id,))
        base_rows = c.fetchall()
        c.execute("SELECT subject, next_class_date FROM class_schedule_override WHERE student_id=?",
                  (student_id,))
        override_rows = c.fetchall()
        conn.close()
        schedule = {}
        for r in base_rows:
            subj = r["subject"]
            if subj not in schedule:
                schedule[subj] = {"dows": [], "next_class_date": None,
                                  "auto_next_class_date": None}
            schedule[subj]["dows"].append(r["dow"])
        for r in override_rows:
            subj = r["subject"]
            if subj not in schedule:
                schedule[subj] = {"dows": [], "next_class_date": None,
                                  "auto_next_class_date": None}
            schedule[subj]["next_class_date"] = r["next_class_date"]
        for subj in schedule:
            if not schedule[subj]["next_class_date"]:
                schedule[subj]["auto_next_class_date"] = \
                    get_auto_next_class_date(student_id, subj)
        return [TextContent(type="text", text=json.dumps(
            schedule, ensure_ascii=False, indent=2))]

    elif name == "get_suppression_list":
        student_id = arguments["student_id"]
        conn = get_connection()
        c = conn.cursor()
        try:
            c.execute("SELECT problem_id FROM suppression WHERE student_id=?",
                      (student_id,))
            rows = [r["problem_id"] for r in c.fetchall()]
        except Exception:
            rows = []
        conn.close()
        return [TextContent(type="text", text=json.dumps(rows, ensure_ascii=False))]

    # ── 登録系 ──────────────────────────────────────────
    elif name == "add_series":
        series_name = arguments["name"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO series (name) VALUES (?)", (series_name,))
        conn.commit()
        series_id = c.lastrowid
        conn.close()
        return [TextContent(type="text", text=json.dumps(
            {"series_id": series_id, "name": series_name}, ensure_ascii=False))]

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
        return [TextContent(type="text", text=json.dumps(
            {"textbook_id": textbook_id, "name": tb_name, "subject": subject},
            ensure_ascii=False))]

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
        category          = arguments.get("category", "予習")
        scheduled_date    = arguments.get("scheduled_date", "").strip()
        undecided         = arguments.get("undecided", False)
        order_in_textbook = arguments.get("order_in_textbook")

        conn = get_connection()
        c = conn.cursor()

        # テキスト名を取得
        c.execute("SELECT name FROM textbooks WHERE textbook_id=?", (textbook_id,))
        tb_row = c.fetchone()
        textbook = tb_row["name"] if tb_row else ""

        # order_in_textbookの自動設定
        if order_in_textbook is None:
            c.execute("SELECT MAX(order_in_textbook) as m FROM problems WHERE textbook_id=?",
                      (textbook_id,))
            r = c.fetchone()
            order_in_textbook = (r["m"] if r and r["m"] else 0) + 1

        total_minutes = arguments.get("total_minutes")
        c.execute("""
            INSERT INTO problems
            (subject, textbook, textbook_id, problem_number,
             importance, difficulty, review_value,
             estimated_minutes, instruction, type, order_in_textbook,
             total_minutes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (subject, textbook, textbook_id, problem_number,
              importance, difficulty, review_value,
              estimated_minutes, instruction, "標準", order_in_textbook,
              total_minutes))
        conn.commit()
        problem_id = c.lastrowid

        # 出題予定の登録
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
            c.execute("""
                INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
                VALUES (?,?,?,?)
            """, (sid, problem_id, effective_date, category))

        conn.commit()
        conn.close()
        return [TextContent(type="text", text=json.dumps({
            "problem_id": problem_id,
            "textbook": textbook,
            "order_in_textbook": order_in_textbook,
            "scheduled_dates": {sid: (
                "2099-12-31（未定）" if undecided
                else (scheduled_date or get_auto_next_class_date(sid, subject) or "2099-12-31")
            ) for sid in student_ids}
        }, ensure_ascii=False, indent=2))]

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

        c.execute("""
            INSERT OR REPLACE INTO assignments (student_id, problem_id, scheduled_date, category)
            VALUES (?,?,?,?)
        """, (student_id, problem_id, effective_date, category))
        conn.commit()
        assignment_id = c.lastrowid
        conn.close()
        return [TextContent(type="text", text=json.dumps({
            "assignment_id": assignment_id,
            "scheduled_date": effective_date,
            "category": category
        }, ensure_ascii=False))]

    elif name == "add_record":
        student_id  = arguments["student_id"]
        problem_id  = arguments["problem_id"]
        record_date = arguments.get("date", date.today().isoformat())
        score       = int(arguments.get("score", 5))
        correct     = score_to_correct(score)
        new_mastery = calc_new_mastery(student_id, problem_id, score, record_date)

        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO history
            (student_id, problem_id, date, correct, mastery, category, score)
            VALUES (?,?,?,?,?,?,?)
        """, (student_id, problem_id, record_date, correct, new_mastery, "記録", score))
        conn.commit()
        conn.close()

        score_labels = {5:"Perfect",4:"Good",3:"Review",2:"Retry",1:"Failed"}

        # 未報告問題の自動登録（報告があった問題より前の出題予定を処理）
        try:
            from database import auto_record_unreported
            auto_results = auto_record_unreported(student_id, record_date)
        except Exception:
            auto_results = []

        return [TextContent(type="text", text=json.dumps({
            "new_mastery": new_mastery,
            "mastery_stars": "★" * new_mastery,
            "score": score,
            "score_label": score_labels.get(score, str(score)),
            "correct": correct,
            "auto_recorded": auto_results
        }, ensure_ascii=False))]

    # ── 更新系 ──────────────────────────────────────────
    elif name == "update_problem":
        problem_id = arguments["problem_id"]
        conn = get_connection()
        c = conn.cursor()
        fields = ["importance","difficulty","review_value","estimated_minutes","instruction"]
        for field in fields:
            if field in arguments:
                c.execute(f"UPDATE problems SET {field}=? WHERE problem_id=?",
                          (arguments[field], problem_id))
        conn.commit()
        conn.close()
        return [TextContent(type="text", text=json.dumps(
            {"status":"ok","problem_id":problem_id}, ensure_ascii=False))]

    elif name == "delete_problem":
        problem_id = arguments["problem_id"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM assignments WHERE problem_id=?", (problem_id,))
        c.execute("DELETE FROM history WHERE problem_id=?", (problem_id,))
        c.execute("DELETE FROM problems WHERE problem_id=?", (problem_id,))
        conn.commit()
        conn.close()
        return [TextContent(type="text", text=json.dumps(
            {"status":"ok","deleted_problem_id":problem_id}, ensure_ascii=False))]

    elif name == "update_assignment_date":
        assignment_id  = arguments["assignment_id"]
        scheduled_date = arguments["scheduled_date"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE assignments SET scheduled_date=? WHERE assignment_id=?",
                  (scheduled_date, assignment_id))
        conn.commit()
        conn.close()
        return [TextContent(type="text", text=json.dumps(
            {"status":"ok","assignment_id":assignment_id,"scheduled_date":scheduled_date},
            ensure_ascii=False))]

    elif name == "update_assignment_category":
        assignment_id = arguments["assignment_id"]
        category      = arguments["category"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE assignments SET category=? WHERE assignment_id=?",
                  (category, assignment_id))
        conn.commit()
        conn.close()
        return [TextContent(type="text", text=json.dumps(
            {"status":"ok","assignment_id":assignment_id,"category":category},
            ensure_ascii=False))]

    elif name == "update_mastery":
        student_id = arguments["student_id"]
        problem_id = arguments["problem_id"]
        mastery    = int(arguments["mastery"])
        mastery    = max(1, min(3, mastery))
        today      = date.today().isoformat()
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO history (student_id, problem_id, date, correct, mastery, category)
            VALUES (?,?,?,?,?,?)
        """, (student_id, problem_id, today, 1, mastery, "手動修正"))
        conn.commit()
        conn.close()
        return [TextContent(type="text", text=json.dumps(
            {"status":"ok","mastery":mastery,"mastery_stars":"★"*mastery},
            ensure_ascii=False))]

    elif name == "update_review_value":
        problem_id   = arguments["problem_id"]
        review_value = arguments["review_value"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE problems SET review_value=? WHERE problem_id=?",
                  (review_value, problem_id))
        conn.commit()
        conn.close()
        return [TextContent(type="text", text=json.dumps(
            {"status":"ok","problem_id":problem_id,"review_value":review_value},
            ensure_ascii=False))]

    elif name == "set_class_schedule":
        student_id = arguments["student_id"]
        subject    = arguments["subject"]
        dows       = arguments["dows"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM class_schedule_base WHERE student_id=? AND subject=?",
                  (student_id, subject))
        for dow in dows:
            c.execute("INSERT INTO class_schedule_base (student_id, subject, dow) VALUES (?,?,?)",
                      (student_id, subject, dow))
        conn.commit()
        conn.close()
        return [TextContent(type="text", text=json.dumps(
            {"status":"ok","student_id":student_id,"subject":subject,"dows":dows},
            ensure_ascii=False))]

    elif name == "set_next_class_date":
        student_id      = arguments["student_id"]
        subject         = arguments["subject"]
        next_class_date = arguments.get("next_class_date", "").strip()
        conn = get_connection()
        c = conn.cursor()
        if next_class_date:
            c.execute("""
                INSERT OR REPLACE INTO class_schedule_override
                (student_id, subject, next_class_date) VALUES (?,?,?)
            """, (student_id, subject, next_class_date))
        else:
            c.execute("DELETE FROM class_schedule_override WHERE student_id=? AND subject=?",
                      (student_id, subject))
        conn.commit()
        auto_next = get_auto_next_class_date(student_id, subject) if not next_class_date else None
        conn.close()
        return [TextContent(type="text", text=json.dumps({
            "status": "ok",
            "next_class_date": next_class_date or "(リセット)",
            "auto_calculated": auto_next
        }, ensure_ascii=False))]

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
        return [TextContent(type="text", text=json.dumps(
            {"status":"ok","cleared":student_id}, ensure_ascii=False))]

    # ── 出力系 ──────────────────────────────────────────
    elif name == "auto_record_session":
        student_id  = arguments["student_id"]
        record_date = arguments.get("record_date", date.today().isoformat())
        try:
            from database import auto_record_unreported
            results = auto_record_unreported(student_id, record_date)
        except Exception as e:
            results = [{"error": str(e)}]
        score_labels = {5:"Perfect",4:"Good",3:"Review",2:"Retry",1:"Failed"}
        summary = []
        for r in results:
            summary.append({
                "problem_id":     r["problem_id"],
                "scheduled_date": r["scheduled_date"],
                "difficulty":     r["difficulty"],
                "score":          r["score"],
                "score_label":    score_labels.get(r["score"], str(r["score"])),
                "new_mastery":    r["new_mastery"],
                "mastery_stars":  "★" * r["new_mastery"],
            })
        return [TextContent(type="text", text=json.dumps({
            "auto_recorded_count": len(summary),
            "records": summary
        }, ensure_ascii=False, indent=2))]

    elif name == "generate_excel_plan":
        student_id     = arguments["student_id"]
        start_date     = arguments.get("start_date", date.today().isoformat())
        end_date       = arguments.get("end_date", "")
        subject_filter = arguments.get("subject_filter", "")

        if not end_date:
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT subjects FROM students WHERE student_id=?", (student_id,))
            row = c.fetchone()
            conn.close()
            if row:
                subjects = [s.strip() for s in row["subjects"].split(",")]
                dates = [get_auto_next_class_date(student_id, s) for s in subjects]
                dates = [d for d in dates if d]
                end_date = min(dates) if dates else (
                    __import__("datetime").date.fromisoformat(start_date) +
                    __import__("datetime").timedelta(days=7)).isoformat()
            else:
                end_date = (__import__("datetime").date.fromisoformat(start_date) +
                            __import__("datetime").timedelta(days=7)).isoformat()

        try:
            from excel_export import export_excel
            path = export_excel(student_id, start_date, end_date,
                                subject_filter if subject_filter else None)
            return [TextContent(type="text", text=json.dumps(
                {"status":"ok","path":path}, ensure_ascii=False))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps(
                {"status":"error","message":str(e)}, ensure_ascii=False))]

    elif name == "generate_pdf_plan":
        student_id     = arguments["student_id"]
        start_date     = arguments.get("start_date", date.today().isoformat())
        end_date       = arguments.get("end_date", "")
        subject_filter = arguments.get("subject_filter", "")

        if not end_date:
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT subjects FROM students WHERE student_id=?", (student_id,))
            row = c.fetchone()
            conn.close()
            if row:
                subjects = [s.strip() for s in row["subjects"].split(",")]
                dates = [get_auto_next_class_date(student_id, s) for s in subjects]
                dates = [d for d in dates if d]
                end_date = min(dates) if dates else (
                    __import__("datetime").date.fromisoformat(start_date) +
                    __import__("datetime").timedelta(days=7)).isoformat()
            else:
                end_date = (__import__("datetime").date.fromisoformat(start_date) +
                            __import__("datetime").timedelta(days=7)).isoformat()

        try:
            from pdf_export import export_pdf
            path = export_pdf(student_id, start_date, end_date,
                              subject_filter if subject_filter else None)
            return [TextContent(type="text", text=json.dumps(
                {"status":"ok","path":path}, ensure_ascii=False))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps(
                {"status":"error","message":str(e)}, ensure_ascii=False))]

    return [TextContent(type="text", text=json.dumps(
        {"error":f"Unknown tool: {name}"}, ensure_ascii=False))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream,
                      app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
