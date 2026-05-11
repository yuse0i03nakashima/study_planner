import os

base = r"C:\Users\ynaka\study_planner"

code = """from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from excel_export import build_plan_data

pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))

CATEGORY_COLORS = {
    "予習":   colors.HexColor("#DDEEFF"),
    "復習":   colors.HexColor("#DDFFDD"),
    "定着":   colors.HexColor("#FFFADD"),
    "再定着": colors.HexColor("#FFE5DD"),
    "未割当": colors.HexColor("#F0F0F0"),
}


def export_pdf(target_date_str, output_path, student_id=None,
               start_date=None, subject_filter=None):
    from database import get_connection
    from datetime import date

    conn = get_connection()
    c = conn.cursor()
    if student_id:
        c.execute("SELECT student_id, name, subjects, plan_mode FROM students "
                  "WHERE student_id=?", (student_id,))
    else:
        c.execute("SELECT student_id, name, subjects, plan_mode FROM students "
                  "ORDER BY student_id")
    students = c.fetchall()
    conn.close()

    start_str = start_date if start_date else date.today().isoformat()
    font = "HeiseiKakuGo-W5"

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm)

    title_style = ParagraphStyle(
        "title", fontName=font, fontSize=12, spaceAfter=6)
    cell_style = ParagraphStyle(
        "cell", fontName=font, fontSize=8, leading=12)

    story = []

    for student in students:
        sid = student["student_id"]
        name = student["name"]
        plan_mode = student["plan_mode"] if student["plan_mode"] else "all"

        if subject_filter:
            subjects_to_process = [subject_filter]
        elif plan_mode == "per_subject":
            subjects_to_process = [
                s.strip() for s in student["subjects"].split(",")]
        else:
            subjects_to_process = [None]

        for subj in subjects_to_process:
            data = build_plan_data(sid, start_str, target_date_str, subj)
            if not data:
                continue

            title_text = name
            if subj:
                title_text += " - " + subj
            story.append(Paragraph(title_text + " の学習計画表", title_style))
            story.append(Spacer(1, 4*mm))

            subjects = data["subjects"]
            rows = data["rows"]
            unassigned = data["unassigned"]

            # ヘッダー
            header = ["実施日"]
            for subject in subjects:
                header.append(subject + "(問題)")
                header.append(subject + "(指示)")

            col_w = [25*mm]
            remain = A4[0] - 30*mm - 25*mm
            per_col = remain / (len(subjects) * 2) if subjects else remain
            for _ in subjects:
                col_w.append(per_col * 0.6)
                col_w.append(per_col * 0.4)

            table_data = [[Paragraph(h, cell_style) for h in header]]

            order = {"復習": 0, "定着": 1, "再定着": 2, "予習": 3}

            for row in rows:
                tr = [Paragraph(row["date"], cell_style)]
                for subject in subjects:
                    si = sorted(
                        row["subjects"].get(subject, []),
                        key=lambda x: order.get(x["category"], 9))
                    prob = chr(10).join(
                        ["[" + i["category"] + "]" + i["textbook"] +
                         " " + i["problem_number"] for i in si])
                    instr = chr(10).join(
                        [i.get("instruction", "") or "" for i in si])
                    tr.append(Paragraph(prob, cell_style))
                    tr.append(Paragraph(instr, cell_style))
                table_data.append(tr)

            all_unassigned = []
            for subject in subjects:
                all_unassigned.extend(unassigned.get(subject, []))

            if all_unassigned:
                tr = [Paragraph("未割当", cell_style)]
                for subject in subjects:
                    si = unassigned.get(subject, [])
                    prob = chr(10).join(
                        ["[" + i["category"] + "]" + i["textbook"] +
                         " " + i["problem_number"] for i in si])
                    instr = chr(10).join(
                        [i.get("instruction", "") or "" for i in si])
                    tr.append(Paragraph(prob, cell_style))
                    tr.append(Paragraph(instr, cell_style))
                table_data.append(tr)

            t = Table(table_data, colWidths=col_w, repeatRows=1)
            style_cmds = [
                ("FONTNAME", (0, 0), (-1, -1), font),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
            t.setStyle(TableStyle(style_cmds))
            story.append(t)
            story.append(Spacer(1, 8*mm))

    doc.build(story)
    return output_path
"""

pdf_path = os.path.join(base, "pdf_export.py")
with open(pdf_path, "w", encoding="utf-8") as f:
    f.write(code)
print("✅ pdf_export.py を完全に書き直しました")