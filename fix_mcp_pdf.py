import os

base = r"C:\Users\ynaka\study_planner"

# ─── pdf_export.py の新規作成 ──────────────────────────
pdf_code = '''from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from database import get_connection, get_plan, get_schedule
from datetime import date, timedelta

pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))

CATEGORY_COLORS = {
    "予習":   colors.HexColor("#DDEEFF"),
    "復習":   colors.HexColor("#DDFFDD"),
    "定着":   colors.HexColor("#FFFADD"),
    "再定着": colors.HexColor("#FFE5DD"),
    "未割当": colors.HexColor("#F0F0F0"),
}

DOW_JA = ["月", "火", "水", "木", "金", "土", "日"]

def export_pdf(target_date_str, output_path, student_id=None, start_date=None):
    conn = get_connection()
    c = conn.cursor()
    if student_id:
        c.execute("SELECT student_id, name, subjects FROM students WHERE student_id=?", (student_id,))
    else:
        c.execute("SELECT student_id, name, subjects FROM students ORDER BY student_id")
    students = c.fetchall()
    conn.close()

    from excel_export import assign_days
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    font = "HeiseiKakuGo-W5"

    title_style = ParagraphStyle("title", fontName=font, fontSize=14, spaceAfter=6)
    cell_style = ParagraphStyle("cell", fontName=font, fontSize=8, leading=12)

    story = []

    for student in students:
        sid = student["student_id"]
        name = student["name"]
        subjects = [s.strip() for s in student["subjects"].split(",")]

        if start_date:
            schedule = get_schedule(sid, start_date, target_date_str)
        else:
            start = date.fromisoformat(target_date_str) - timedelta(weeks=1)
            schedule = get_schedule(sid, start.isoformat(), target_date_str)

        plan = get_plan(sid, target_date_str)
        assigned, unassigned = assign_days(plan, schedule)
        dates_with_time = sorted([d for d, m in schedule.items() if m > 0])

        story.append(Paragraph(f"{name} の学習計画表", title_style))
        story.append(Spacer(1, 4*mm))

        # ヘッダー行
        header = ["実施日"] + subjects + ["未割当"]
        col_widths = [25*mm] + [int((A4[0] - 30*mm - 25*mm) / (len(subjects) + 1))] * (len(subjects) + 1)

        table_data = [header]

        for d in dates_with_time:
            d_obj = date.fromisoformat(d)
            date_label = f"{d_obj.month}/{d_obj.day}({DOW_JA[d_obj.weekday()]})"
            day_items = [item for item in assigned if item["assigned_date"] == d]
            row = [Paragraph(date_label, cell_style)]
            for subject in subjects:
                subject_items = [item for item in day_items if item["subject"] == subject]
                lines = []
                for item in subject_items:
                    lines.append(f"【{item['category']}】{item['textbook']} {item['problem_number']}")
                    if item.get("instruction"):
                        lines.append(item["instruction"])
                cell_text = "\\n".join(lines)
                row.append(Paragraph(cell_text, cell_style))
            row.append(Paragraph("", cell_style))
            table_data.append(row)

        # 未割当行
        if unassigned:
            row = [Paragraph("未割当", cell_style)]
            for subject in subjects:
                subject_items = [item for item in unassigned if item["subject"] == subject]
                lines = [f"【{item['category']}】{item['textbook']} {item['problem_number']}" for item in subject_items]
                row.append(Paragraph("\\n".join(lines), cell_style))
            row.append(Paragraph("", cell_style))
            table_data.append(row)

        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        style_cmds = [
            ("FONTNAME", (0, 0), (-1, -1), font),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ]

        # カテゴリ色をセルに適用
        for row_idx, d in enumerate(dates_with_time, start=1):
            day_items = [item for item in assigned if item["assigned_date"] == d]
            for col_idx, subject in enumerate(subjects, start=1):
                subject_items = [item for item in day_items if item["subject"] == subject]
                if subject_items:
                    color = CATEGORY_COLORS.get(subject_items[0]["category"], colors.white)
                    style_cmds.append(("BACKGROUND", (col_idx, row_idx), (col_idx, row_idx), color))

        t.setStyle(TableStyle(style_cmds))
        story.append(t)
        story.append(Spacer(1, 8*mm))

    doc.build(story)
    return output_path
'''

with open(os.path.join(base, "pdf_export.py"), "w", encoding="utf-8") as f:
    f.write(pdf_code)
print("✅ pdf_export.py を作成しました")

# ─── mcp_server.py を更新 ──────────────────────────────
mcp_code = '''import asyncio
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
            name="get_all_students",
            description="全生徒の一覧を取得する",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="add_problem",
            description="問題マスタに新しい問題を登録する",
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
                        "description": "出題する生徒IDのリスト"
                    },
                    "scheduled_date": {"type": "string", "description": "予習日（YYYY-MM-DD形式）"}
                },
                "required": ["subject", "textbook", "problem_number", "importance",
                             "difficulty", "review_value", "estimated_minutes",
                             "student_ids", "scheduled_date"]
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
        return [TextContent(type="text", text=json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2))]

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
            ORDER BY h.date DESC
            LIMIT 30
        """, (student_id,))
        history = [dict(r) for r in c.fetchall()]
        c.execute("""
            SELECT a.scheduled_date, a.category,
                   p.subject, p.textbook, p.problem_number,
                   p.importance, p.review_value, p.problem_id,
                   (SELECT mastery FROM history h
                    WHERE h.student_id = a.student_id AND h.problem_id = a.problem_id
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
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

    elif name == "add_problem":
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO problems
            (subject, textbook, problem_number, importance, difficulty,
             review_value, estimated_minutes, instruction, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            arguments["subject"],
            arguments["textbook"],
            arguments["problem_number"],
            arguments["importance"],
            arguments["difficulty"],
            arguments["review_value"],
            arguments["estimated_minutes"],
            arguments.get("instruction", ""),
            "標準"
        ))
        conn.commit()
        problem_id = c.lastrowid
        for sid in arguments["student_ids"]:
            c.execute("""
                INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
                VALUES (?, ?, ?, ?)
            """, (sid, problem_id, arguments["scheduled_date"], "予習"))
        conn.commit()
        conn.close()
        return [TextContent(type="text", text=f"問題を登録しました（problem_id: {problem_id}）")]

    elif name == "delete_problem":
        problem_id = arguments["problem_id"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT subject, textbook, problem_number FROM problems WHERE problem_id=?", (problem_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return [TextContent(type="text", text=f"問題ID {problem_id} が見つかりません")]
        info = f"{row['subject']} {row['textbook']} {row['problem_number']}"
        c.execute("DELETE FROM assignments WHERE problem_id=?", (problem_id,))
        c.execute("DELETE FROM history WHERE problem_id=?", (problem_id,))
        c.execute("DELETE FROM problems WHERE problem_id=?", (problem_id,))
        conn.commit()
        conn.close()
        return [TextContent(type="text", text=f"問題を削除しました（{info}）")]

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
            INSERT INTO history (student_id, problem_id, date, correct, mastery, category)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, problem_id, record_date, correct, new_mastery, "記録"))
        conn.commit()
        conn.close()
        update_assignments_after_record(student_id, problem_id, record_date, new_mastery)
        stars = "★" * new_mastery
        return [TextContent(type="text", text=f"授業記録を保存しました（習熟度：{stars}）")]

    elif name == "update_review_value":
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE problems SET review_value=? WHERE problem_id=?",
                  (arguments["review_value"], arguments["problem_id"]))
        conn.commit()
        conn.close()
        return [TextContent(type="text",
            text=f"問題ID {arguments['problem_id']} の復習価値を {arguments['review_value']} に更新しました")]

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
        return [TextContent(type="text",
            text=json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2))]

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
        return [TextContent(type="text",
            text=json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2))]

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
        output_path = os.path.join(archive_dir, f"計画表_{student_name}_{target_date}.xlsx")
        export_excel(target_date, output_path, student_id=student_id, start_date=start_date)
        save_plan_history(student_id, start_date, target_date, output_path)
        try:
            os.startfile(output_path.replace("/", "\\\\"))
            message = f"計画表（Excel）を生成し自動で開きました。\\nファイルパス：{output_path}"
        except Exception as e:
            message = f"計画表（Excel）を生成しました。\\nファイルパス：{output_path}\\n（自動起動エラー：{e}）"
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
        output_path = os.path.join(archive_dir, f"計画表_{student_name}_{target_date}.pdf")
        export_pdf(target_date, output_path, student_id=student_id, start_date=start_date)
        save_plan_history(student_id, start_date, target_date, output_path)
        try:
            os.startfile(output_path.replace("/", "\\\\"))
            message = f"計画表（PDF）を生成し自動で開きました。\\nファイルパス：{output_path}"
        except Exception as e:
            message = f"計画表（PDF）を生成しました。\\nファイルパス：{output_path}\\n（自動起動エラー：{e}）"
        return [TextContent(type="text", text=message)]

    return [TextContent(type="text", text="不明なツールです")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
'''

with open(os.path.join(base, "mcp_server.py"), "w", encoding="utf-8") as f:
    f.write(mcp_code)
print("✅ mcp_server.py を更新しました")

# ─── app.pyにPDF出力ルートを追加 ───────────────────────
app_path = os.path.join(base, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

pdf_route = '''
@app.route("/export_pdf", methods=["POST"])
def export_pdf_route():
    from pdf_export import export_pdf
    conn = get_connection()
    c = conn.cursor()
    student_id = request.form["student_id"]
    target_date = request.form["date"]
    start_date = request.form.get("start_date", "")
    if not start_date:
        start_date = date.today().isoformat()
    c.execute("SELECT name FROM students WHERE student_id=?", (student_id,))
    row = c.fetchone()
    conn.close()
    student_name = row["name"] if row else student_id
    os.makedirs("plan_archives", exist_ok=True)
    output_path = os.path.join("plan_archives", f"計画表_{student_name}_{target_date}.pdf")
    export_pdf(target_date, output_path, student_id=student_id, start_date=start_date)
    save_plan_history(student_id, start_date, target_date, output_path)
    return send_file(output_path, as_attachment=True)

'''

if "/export_pdf" not in app_content:
    app_content = app_content.replace(
        "if __name__ == '__main__':",
        pdf_route + "if __name__ == '__main__':"
    )
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app_content)
    print("✅ app.py にPDF出力ルートを追加しました")

# ─── export.htmlにPDFボタンを追加 ──────────────────────
export_html = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>計画表出力</title>
  <style>
    body { font-family: sans-serif; max-width: 500px; margin: 60px auto; background: #f5f7fa; }
    h1 { color: #2c3e50; }
    .form-box { background: white; padding: 24px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    label { display: block; margin-top: 12px; font-weight: bold; }
    select, input[type="date"] { width: 100%; padding: 8px; margin-top: 4px; border: 1px solid #ccc; border-radius: 4px; font-size: 15px; box-sizing: border-box; }
    .btn-row { display: flex; gap: 12px; margin-top: 20px; }
    .btn-excel { padding: 10px 24px; background: #27ae60; color: white; border: none; border-radius: 6px; font-size: 15px; cursor: pointer; flex: 1; }
    .btn-excel:hover { background: #1e8449; }
    .btn-pdf { padding: 10px 24px; background: #e74c3c; color: white; border: none; border-radius: 6px; font-size: 15px; cursor: pointer; flex: 1; }
    .btn-pdf:hover { background: #c0392b; }
    p.note { color: #888; font-size: 13px; margin-top: 6px; }
    a { color: #4472C4; }
  </style>
</head>
<body>
  <h1>③ 計画表出力</h1>
  <div class="form-box">
    <form method="POST" id="export-form">
      <label>生徒</label>
      <select name="student_id">
        {% for s in students %}
        <option value="{{ s.student_id }}">{{ s.name }}</option>
        {% endfor %}
      </select>

      <label>次回授業日（計画終了日）</label>
      <input type="date" name="date" required>

      <label>計画開始日（任意）</label>
      <input type="date" name="start_date">
      <p class="note">空欄の場合は今日の日付が自動的に使われます。</p>

      <div class="btn-row">
        <button type="submit" class="btn-excel"
          onclick="document.getElementById('export-form').action='/export'">
          📊 Excelダウンロード
        </button>
        <button type="submit" class="btn-pdf"
          onclick="document.getElementById('export-form').action='/export_pdf'">
          📄 PDFダウンロード
        </button>
      </div>
    </form>
  </div>
  <p><a href="/">← トップに戻る</a></p>
</body>
</html>"""

with open(os.path.join(templates, "export.html"), "w", encoding="utf-8") as f:
    f.write(export_html)
print("✅ export.html を更新しました")
print("✅ 全て完了")