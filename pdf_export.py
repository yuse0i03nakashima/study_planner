from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from excel_export import build_plan_data

pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))


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

    # 横向きA4
    doc = SimpleDocTemplate(
        output_path, pagesize=landscape(A4),
        leftMargin=10*mm, rightMargin=10*mm,
        topMargin=10*mm, bottomMargin=10*mm)

    title_style = ParagraphStyle(
        "title", fontName=font, fontSize=11, spaceAfter=4)
    cell_style = ParagraphStyle(
        "cell", fontName=font, fontSize=7, leading=10)
    head_style = ParagraphStyle(
        "head", fontName=font, fontSize=8, leading=10,
        textColor=colors.white)

    story = []
    page_w = landscape(A4)[0] - 20*mm  # 実効幅

    order = {"復習": 0, "定着": 1, "再定着": 2, "予習": 3}

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

            title_text = name + (" - " + subj if subj else "") + " の学習計画表"
            story.append(Paragraph(title_text, title_style))
            story.append(Spacer(1, 3*mm))

            subjects = data["subjects"]
            rows = data["rows"]
            unassigned = data["unassigned"]

            # 列幅：実施日20mm、各教科は問題列とメモ列
            date_w = 20*mm
            remain = page_w - date_w
            n_subj = len(subjects)
            prob_w = remain * 0.6 / n_subj if n_subj else remain * 0.6
            instr_w = remain * 0.4 / n_subj if n_subj else remain * 0.4

            col_w = [date_w]
            for _ in subjects:
                col_w.append(prob_w)
                col_w.append(instr_w)

            # ヘッダー行
            header_row = [Paragraph("実施日", head_style)]
            for subject in subjects:
                header_row.append(Paragraph(subject + "（問題）", head_style))
                header_row.append(Paragraph(subject + "（指示）", head_style))

            table_data = [header_row]

            # データ行（1日1行・高さ上限あり）
            for row in rows:
                tr = [Paragraph(row["date"], cell_style)]
                for subject in subjects:
                    si = sorted(
                        row["subjects"].get(subject, []),
                        key=lambda x: order.get(x["category"], 9))
                    prob = "<br/>".join(
                        ["[" + i["category"] + "]" +
                         i["textbook"] + " " + i["problem_number"]
                         for i in si])
                    instr = "<br/>".join(
                        [i.get("instruction", "") or "―" for i in si])
                    tr.append(Paragraph(prob or "　", cell_style))
                    tr.append(Paragraph(instr or "　", cell_style))
                table_data.append(tr)

            # 未割当行
            all_unassigned = []
            for subject in subjects:
                all_unassigned.extend(unassigned.get(subject, []))
            if all_unassigned:
                tr = [Paragraph("未割当", cell_style)]
                for subject in subjects:
                    si = unassigned.get(subject, [])
                    prob = "<br/>".join(
                        ["[" + i["category"] + "]" +
                         i["textbook"] + " " + i["problem_number"]
                         for i in si])
                    instr = "<br/>".join(
                        [i.get("instruction", "") or "―" for i in si])
                    tr.append(Paragraph(prob or "　", cell_style))
                    tr.append(Paragraph(instr or "　", cell_style))
                table_data.append(tr)

            # 行高さ上限を設定（1行あたり最大60pt）
            row_heights = [14]  # ヘッダー
            for _ in table_data[1:]:
                row_heights.append(None)  # 自動

            t = Table(table_data, colWidths=col_w,
                      rowHeights=row_heights,
                      repeatRows=1, splitByRow=True)

            style_cmds = [
                ("FONTNAME", (0, 0), (-1, -1), font),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (1, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#F5F5F5")]),
            ]
            t.setStyle(TableStyle(style_cmds))
            story.append(t)
            story.append(Spacer(1, 6*mm))

    doc.build(story)
    return output_path
