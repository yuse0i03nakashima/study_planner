from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer, HRFlowable)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from planner import build_plan_data
from export_theme import get_palette, normalize_theme
import os

pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
FONT = "HeiseiKakuGo-W5"

DOW_JA = ["月", "火", "水", "木", "金", "土", "日"]


class _Palette:
    """テーマ名からreportlab用のカラー一式を作る"""

    def __init__(self, theme=None):
        p = get_palette(theme)
        def c(key): return colors.HexColor("#" + p[key])

        self.BG_MAIN     = c("bg_main")
        self.BG_SURFACE  = c("bg_surface")
        self.BG_SURFACE2 = c("bg_surface2")
        self.BG_HEADER   = c("bg_header")
        self.BG_DAY_A    = c("bg_day_a")
        self.BG_DAY_B    = c("bg_day_b")
        self.TEXT        = c("text")
        self.MUTED       = c("muted")
        self.DIM         = c("dim")
        self.BLUE        = c("blue")
        self.GREEN       = c("green")
        self.AMBER       = c("amber")
        self.ROSE        = c("rose")
        self.RED         = c("red")
        self.BORDER      = c("border")
        self.BORDER_L    = c("border_light")
        self.UNASSIGNED  = c("unassigned_bg")

        self.CAT_COLORS = {
            "New": self.BLUE, "Recall": self.GREEN,
            "Drill": self.AMBER, "Reinforce": self.ROSE,
            "予習":   self.BLUE,
            "復習":   self.GREEN,
            "定着":   self.AMBER,
            "再定着": self.ROSE,
        }
        self.MASTERY_COLORS = {1: self.ROSE, 2: self.AMBER, 3: self.GREEN}


# 既定（ダーク）パレット — モジュール外からの参照互換用
_DEFAULT_PAL = _Palette("dark")
C_TEXT = _DEFAULT_PAL.TEXT




def _pdf_prob_text(item):
    """PDFのProblem列テキストを生成（ASCII進捗バー付き）"""
    prob = str(item.get("problem_number", ""))
    stot = int(item.get("session_total", 1) or 1)
    if stot <= 1:
        return prob
    sidx = int(item.get("session_index", 1) or 1)
    pa   = float(item.get("progress_after", 1.0) or 1.0)
    fil  = int(pa * 8)
    bar  = "#" * fil + "-" * (8 - fil)
    pct  = int(pa * 100)
    return prob + "  [" + bar + "] " + str(pct) + "% (" + str(sidx) + "/" + str(stot) + ")"

def _para(text, color=None, size=8, bold=False, align="LEFT"):
    """Paragraphオブジェクトを生成するヘルパー"""
    c = color or C_TEXT
    style = ParagraphStyle(
        "p",
        fontName=FONT,
        fontSize=size,
        leading=size * 1.4,
        textColor=c,
        alignment={"LEFT": 0, "CENTER": 1, "RIGHT": 2}.get(align, 0),
    )
    return Paragraph(str(text) if text else "—", style)


def export_pdf(student_id, start_date_str, end_date_str,
               subject_filter=None, output_path=None, section_ids=None,
               theme="dark"):
    """計画表をPDFファイルに出力して保存パスを返す

    theme: "dark"（既定）または "light"
    """
    from datetime import date as date_cls

    theme = normalize_theme(theme)
    pal = _Palette(theme)

    plan_data = build_plan_data(
        student_id, start_date_str, end_date_str, subject_filter,
        section_ids=section_ids)
    if not plan_data:
        return None

    # 出力先
    if not output_path:
        archive_dir = os.path.join(os.path.dirname(__file__), "plan_archives")
        os.makedirs(archive_dir, exist_ok=True)
        student_name = plan_data["student_name"]
        theme_suffix = "" if theme == "dark" else f"_{theme}"
        base_name = (f"{student_name}_{start_date_str}_{end_date_str}"
                     f"{theme_suffix}")
        output_path = os.path.join(archive_dir, f"{base_name}.pdf")
        # ロック対策
        if os.path.exists(output_path):
            try:
                with open(output_path, "a"):
                    pass
            except PermissionError:
                from datetime import datetime as _dt
                output_path = os.path.join(
                    archive_dir,
                    f"{base_name}_{_dt.now().strftime('%H%M%S')}.pdf")

    student_name = plan_data["student_name"]
    subjects     = plan_data["subjects"]
    rows         = plan_data["rows"]
    unassigned   = plan_data.get("unassigned", {})

    # 横向きA4
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        leftMargin=8*mm, rightMargin=8*mm,
        topMargin=8*mm, bottomMargin=8*mm,
        title=f"{student_name} Study Plan",
    )

    page_w = landscape(A4)[0] - 16*mm  # 実効幅 ≈ 261mm

    # ── 列幅（mm）: Date/Day/Subject/Cat/Textbook/Problem/Mastery/Min/Instruction ──
    col_widths_mm = [14, 10, 14, 11, 28, 52, 13, 8, 111]
    col_widths = [w * mm for w in col_widths_mm]

    story = []

    # ── タイトル ──
    title_style = ParagraphStyle(
        "title", fontName=FONT, fontSize=13, leading=18,
        textColor=pal.BLUE,
        spaceAfter=2*mm,
    )
    story.append(Paragraph(
        f"[SP]　{student_name}　　{start_date_str} → {end_date_str}",
        title_style
    ))
    story.append(HRFlowable(
        width="100%", thickness=0.5,
        color=pal.BORDER_L, spaceAfter=3*mm
    ))

    # ── ヘッダ行 ──
    headers = ["Date", "Day", "Subject", "Cat",
               "Textbook", "Problem", "Mastery", "Min", "Instruction"]
    header_row = [
        _para(h, color=pal.MUTED, size=8, align="CENTER")
        for h in headers
    ]

    # ── データ行を構築 ──
    table_data = [header_row]
    row_styles = []   # (row_index, bg_color, cat_color_col3)
    row_index = 1     # 0はヘッダ

    day_toggle = False

    for day_row in rows:
        date_str_raw = day_row.get("date_str", "")
        subjects_dict = day_row.get("subjects", {})

        # この日の全問題
        day_items = []
        for subj in subjects:
            for item in subjects_dict.get(subj, []):
                day_items.append((subj, item))

        if not day_items:
            continue

        day_bg = pal.BG_DAY_A if day_toggle else pal.BG_DAY_B
        day_toggle = not day_toggle

        try:
            d_obj = date_cls.fromisoformat(date_str_raw)
            dow = DOW_JA[d_obj.weekday()]
            date_disp = f"{d_obj.month}/{d_obj.day}"
            is_weekend = d_obj.weekday() >= 5
        except Exception:
            dow = ""
            date_disp = date_str_raw
            is_weekend = False

        dow_color = pal.ROSE if is_weekend else pal.MUTED

        for i, (subj, item) in enumerate(day_items):
            cat = item.get("category", "")
            cat_color = pal.CAT_COLORS.get(cat, pal.DIM)
            mastery_int = item.get("mastery_int", 1)
            mastery_color = pal.MASTERY_COLORS.get(mastery_int, pal.TEXT)

            row = [
                _para(date_disp if i == 0 else "", pal.MUTED, 8, align="CENTER"),
                _para(dow if i == 0 else "", dow_color, 8, align="CENTER"),
                _para(subj, pal.MUTED, 8, align="CENTER"),
                _para(cat, cat_color, 8, align="CENTER"),
                _para(item.get("textbook", ""), pal.MUTED, 8),
                _para(_pdf_prob_text(item), pal.TEXT, 9),
                _para(item.get("mastery", "★"), mastery_color, 9, align="CENTER"),
                _para(str(item.get("estimated_minutes", "")), pal.DIM, 8, align="CENTER"),
                _para(item.get("instruction", ""), pal.MUTED, 8),
            ]
            table_data.append(row)

            is_last = (i == len(day_items) - 1)
            row_styles.append((row_index, day_bg, is_last))
            row_index += 1

    # ── 未割当 ──
    all_unassigned = []
    for subj in subjects:
        for item in unassigned.get(subj, []):
            all_unassigned.append((subj, item))

    if all_unassigned:
        # 区切り行
        sep_row = [_para("── UNASSIGNED ──", pal.RED, 7)] + [""] * 8
        table_data.append(sep_row)
        row_styles.append((row_index, pal.UNASSIGNED, False))
        row_index += 1

        for subj, item in all_unassigned:
            cat = item.get("category", "")
            cat_color = pal.CAT_COLORS.get(cat, pal.DIM)
            row = [
                _para("—", pal.DIM, 7, align="CENTER"),
                _para("—", pal.DIM, 7, align="CENTER"),
                _para(subj, pal.DIM, 7, align="CENTER"),
                _para(cat, cat_color, 7, align="CENTER"),
                _para(item.get("textbook", ""), pal.DIM, 7),
                _para(item.get("problem_number", ""), pal.DIM, 8),
                _para("—", pal.DIM, 7, align="CENTER"),
                _para(str(item.get("estimated_minutes", "")), pal.DIM, 7),
                _para(item.get("instruction", ""), pal.DIM, 7),
            ]
            table_data.append(row)
            row_styles.append((row_index, pal.UNASSIGNED, True))
            row_index += 1

    # ── テーブルスタイル ──
    ts = TableStyle([
        # 全体
        ("BACKGROUND", (0, 0), (-1, 0), pal.BG_HEADER),   # ヘッダ
        ("TEXTCOLOR",  (0, 0), (-1, 0), pal.MUTED),
        ("FONTNAME",   (0, 0), (-1, -1), FONT),
        ("FONTSIZE",   (0, 0), (-1, 0), 7),
        ("ROWBACKGROUND", (0, 0), (-1, 0), pal.BG_SURFACE2),
        ("GRID",       (0, 0), (-1, -1), 0.3, pal.BORDER),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",  (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ])

    # 行ごとの背景色
    for ri, bg, is_last in row_styles:
        ts.add("BACKGROUND", (0, ri), (-1, ri), bg)
        if is_last:
            ts.add("LINEBELOW", (0, ri), (-1, ri), 0.8, pal.BORDER_L)

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(ts)
    story.append(tbl)

    # ── ページ背景色（テーマに追従） ──
    def draw_bg(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(pal.BG_MAIN)
        canvas.rect(0, 0, landscape(A4)[0], landscape(A4)[1],
                    fill=True, stroke=False)
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_bg, onLaterPages=draw_bg)
    return output_path
