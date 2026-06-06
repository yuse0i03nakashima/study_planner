import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RAILWAY_URL     = os.environ.get('RAILWAY_URL', '').rstrip('/')
RAILWAY_API_KEY = os.environ.get('RAILWAY_API_KEY', '')

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from tool_handlers import handle_tool

app = Server("study-planner")


def _call_remote(name: str, arguments: dict):
    """Railway の /api/tool エンドポイントにプロキシする。"""
    import urllib.request
    payload = json.dumps({"name": name, "arguments": arguments}).encode()
    req = urllib.request.Request(
        f"{RAILWAY_URL}/api/tool",
        data=payload,
        headers={"Content-Type": "application/json", "X-API-Key": RAILWAY_API_KEY},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="check_connection",
            description="MCPの接続先（ローカルDBかRailwayか）を確認する。問題登録前に必ず実行して接続先を確認すること。",
            inputSchema={"type": "object", "properties": {}}
        ),
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
            name="get_sections",
            description="テキストのセクション一覧を取得する。textbook_idを指定するとそのテキストのみ返す",
            inputSchema={
                "type": "object",
                "properties": {
                    "textbook_id": {"type": "integer", "description": "テキストID（省略時は全セクション）"}
                }
            }
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
                "Specify category: New/Recall/Drill/Reinforce (default: New)."
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
                    "category":       {"type": "string",  "description": "Category: New/Recall/Drill/Reinforce (default: New)"},
                    "scheduled_date": {"type": "string",  "description": "出題日YYYY-MM-DD（省略→授業曜日から自動計算）"},
                    "undecided":      {"type": "boolean", "description": "true=授業日未定として登録（計画表に出さない）"},
                    "total_minutes":  {"type": "integer", "description": "総HP（省略=通常問題=1回完結）。古文精読など複数セッションに分割したい場合に設定。estimated_minutesより大きな値を設定する"},
                    "section_id":     {"type": "integer", "description": "セクションID（get_sectionsで確認）。section_nameと排他"},
                    "section_name":   {"type": "string",  "description": "セクション名。指定すると既存セクションを検索し、なければ新規作成する。section_idと排他"}
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
                    "category":       {"type": "string",  "description": "Category: New/Recall/Drill/Reinforce"},
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
            name="delete_assignment",
            description="出題予定を削除する。問題マスタは削除されない。",
            inputSchema={
                "type": "object",
                "properties": {
                    "assignment_id": {"type": "integer", "description": "削除する出題予定のID"}
                },
                "required": ["assignment_id"]
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
                    "category":      {"type": "string",  "description": "New category: New/Recall/Drill/Reinforce"}
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
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "check_connection":
        if RAILWAY_URL and RAILWAY_API_KEY:
            mode = "remote"
            target = RAILWAY_URL
        else:
            from tool_handlers import DB_PATH
            mode = "local"
            target = DB_PATH
        return [TextContent(type="text", text=json.dumps({
            "mode": mode,
            "target": target,
            "warning": None if mode == "remote" else "⚠️ ローカルDBに書き込まれます。RAILWAY_URLとRAILWAY_API_KEYが未設定です。",
        }, ensure_ascii=False, indent=2))]

    if RAILWAY_URL and RAILWAY_API_KEY:
        result = _call_remote(name, arguments)
    else:
        result = {
            "error": "⚠️ Railway未接続: RAILWAY_URLとRAILWAY_API_KEYが設定されていません。Claude Desktopを再起動してください。",
            "mode": "disconnected"
        }
    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream,
                      app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
