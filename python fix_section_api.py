import os, subprocess, re

base = r"C:\Users\ynaka\study_planner"
prev_path = os.path.join(base, "templates", "preview.html")
app_path  = os.path.join(base, "app.py")
excel_path = os.path.join(base, "excel_export.py")
pdf_path   = os.path.join(base, "pdf_export.py")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. preview.html: selectをmultipleに変更
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with open(prev_path, "r", encoding="utf-8") as f:
    prev = f.read()

old_sec_sel = '''\
            <select name="section_filter" id="section-filter"
              style="padding:8px 12px;background:var(--surface2);
                border:1px solid var(--border-light);color:var(--text);
                font-family:'Noto Serif JP',serif;font-size:13px;min-width:220px;">
              <option value="">— All Sections —</option>'''

new_sec_sel = '''\
            <select name="section_filter" id="section-filter"
              multiple size="5"
              style="padding:4px 8px;background:var(--surface2);
                border:1px solid var(--border-light);color:var(--text);
                font-family:'Noto Serif JP',serif;font-size:12px;
                min-width:220px;min-height:80px;max-height:160px;">'''

if old_sec_sel in prev:
    prev = prev.replace(old_sec_sel, new_sec_sel)
    print("✅ section-filterをmultipleに変更しました")
else:
    print("❌ section-filterが見つかりません")

# multipleのときは「— All Sections —」optionは不要なのでhintを追加
old_sec_hint = '''\
            <label>Section <span style="color:var(--text-dim);font-size:9px;">for exam prep</span></label>'''
new_sec_hint = '''\
            <label>Section <span style="color:var(--text-dim);font-size:9px;">for exam prep — Ctrl/Cmd+click to select multiple</span></label>'''
if old_sec_hint in prev:
    prev = prev.replace(old_sec_hint, new_sec_hint)
    print("✅ Sectionラベルにヒントを追加しました")

# loadSectionsのoptionにselected状態を反映
old_opt = '''\
      var opt = document.createElement('option');
      opt.value = sec.section_id;
      opt.textContent = sec.textbook_name + ' / ' + sec.name;
      if (String(sec.section_id) === currentVal) opt.selected = true;
      secSel.appendChild(opt);'''
new_opt = '''\
      var opt = document.createElement('option');
      opt.value = sec.section_id;
      opt.textContent = sec.textbook_name + ' / ' + sec.name;
      if (currentVals.indexOf(String(sec.section_id)) !== -1) opt.selected = true;
      secSel.appendChild(opt);'''
if old_opt in prev:
    prev = prev.replace(old_opt, new_opt)
    print("✅ loadSectionsのselected判定を複数対応に変更しました")

# currentValをcurrentValsに変更
old_current = '  var currentVal = secSel.value;'
new_current = '  var currentVals = Array.from(secSel.selectedOptions).map(function(o){ return o.value; });'
if old_current in prev:
    prev = prev.replace(old_current, new_current)
    print("✅ currentValをcurrentValsに変更しました")

with open(prev_path, "w", encoding="utf-8") as f:
    f.write(prev)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. app.py: section_filterを複数値対応に
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with open(app_path, "r", encoding="utf-8") as f:
    app = f.read()

# previewルートでsection_filterをgetlistで取得
old_sec_filter = '''\
        section_filter = request.form.get("section_filter", "").strip()
        preview_data = build_plan_data(
            student_id, start_date, end_date,
            subject_filter if subject_filter else None,
            section_id=int(section_filter) if section_filter else None)'''
new_sec_filter = '''\
        section_filters = request.form.getlist("section_filter")
        section_ids = [int(s) for s in section_filters if s.strip()]
        preview_data = build_plan_data(
            student_id, start_date, end_date,
            subject_filter if subject_filter else None,
            section_ids=section_ids if section_ids else None)'''

if old_sec_filter in app:
    app = app.replace(old_sec_filter, new_sec_filter)
    print("✅ previewルートのsection_filterを複数対応に変更しました")
else:
    print("❌ previewルートのsection_filterが見つかりません")

# Excel出力のsection_filter
old_excel_sec = '''\
        section_filter = request.form.get("section_filter", "").strip()
        if action == "excel":
            from excel_export import export_excel
            path = export_excel(student_id, start_date, end_date,
                                subject_filter if subject_filter else None,
                                section_id=int(section_filter) if section_filter else None)'''
new_excel_sec = '''\
        section_filters = request.form.getlist("section_filter")
        section_ids = [int(s) for s in section_filters if s.strip()]
        if action == "excel":
            from excel_export import export_excel
            path = export_excel(student_id, start_date, end_date,
                                subject_filter if subject_filter else None,
                                section_ids=section_ids if section_ids else None)'''

if old_excel_sec in app:
    app = app.replace(old_excel_sec, new_excel_sec)
    print("✅ Excel出力のsection_filterを複数対応に変更しました")

# PDF出力のsection_filter
old_pdf_sec = '''\
        if action == "pdf":
            from pdf_export import export_pdf
            path = export_pdf(student_id, start_date, end_date,
                              subject_filter if subject_filter else None,
                              section_id=int(section_filter) if section_filter else None)'''
new_pdf_sec = '''\
        if action == "pdf":
            from pdf_export import export_pdf
            path = export_pdf(student_id, start_date, end_date,
                              subject_filter if subject_filter else None,
                              section_ids=section_ids if section_ids else None)'''

if old_pdf_sec in app:
    app = app.replace(old_pdf_sec, new_pdf_sec)
    print("✅ PDF出力のsection_filterを複数対応に変更しました")

# render_templateのselected_section_id
old_render_sec = '_sec_filter = request.form.get("section_filter", "").strip() if request.method == "POST" else ""'
new_render_sec = '_sec_filters = request.form.getlist("section_filter") if request.method == "POST" else []'
if old_render_sec in app:
    app = app.replace(old_render_sec, new_render_sec)

old_selected_sec = 'selected_section_id=_sec_filter,'
new_selected_sec = 'selected_section_ids=_sec_filters,'
if old_selected_sec in app:
    app = app.replace(old_selected_sec, new_selected_sec)
    print("✅ render_templateのselected_section_idsを複数対応に変更しました")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(app)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. excel_export.py: section_idをsection_idsに変更
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with open(excel_path, "r", encoding="utf-8") as f:
    excel = f.read()

# build_plan_dataのシグネチャ
excel = excel.replace(
    "def build_plan_data(student_id, start_date_str, target_date_str,\n                    subject_filter=None, section_id=None):",
    "def build_plan_data(student_id, start_date_str, target_date_str,\n                    subject_filter=None, section_ids=None):"
)

# フィルター処理
old_sec_filt = '''\
    # セクションフィルター（テスト範囲の絞り込み）
    if section_id:
        # section_idに属するproblem_idを取得してplanを絞り込む
        conn2 = get_connection()
        c2 = conn2.cursor()
        c2.execute("SELECT problem_id FROM problems WHERE section_id=?", (section_id,))
        section_pids = {r["problem_id"] for r in c2.fetchall()}
        conn2.close()
        plan = [p for p in plan if p.get("problem_id") in section_pids]'''

new_sec_filt = '''\
    # セクションフィルター（テスト範囲の絞り込み・複数選択対応）
    if section_ids:
        conn2 = get_connection()
        c2 = conn2.cursor()
        placeholders = ",".join("?" * len(section_ids))
        c2.execute(f"SELECT problem_id FROM problems WHERE section_id IN ({placeholders})",
                   section_ids)
        section_pids = {r["problem_id"] for r in c2.fetchall()}
        conn2.close()
        plan = [p for p in plan if p.get("problem_id") in section_pids]'''

if old_sec_filt in excel:
    excel = excel.replace(old_sec_filt, new_sec_filt)
    print("✅ excel: section_idをsection_ids（複数）に変更しました")
else:
    print("❌ excel: section_idフィルターが見つかりません")

# export_excelのシグネチャ
excel = re.sub(
    r'def export_excel\((.*?)section_id=None\)',
    lambda m: m.group(0).replace("section_id=None", "section_ids=None"),
    excel
)
# export_excel内のbuild_plan_data呼び出し
excel = excel.replace(
    "section_id=section_id)",
    "section_ids=section_ids)"
)

with open(excel_path, "w", encoding="utf-8") as f:
    f.write(excel)
print("✅ excel_export.py: section_ids対応完了")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. pdf_export.py: section_idをsection_idsに変更
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with open(pdf_path, "r", encoding="utf-8") as f:
    pdf = f.read()

pdf = re.sub(
    r'def export_pdf\((.*?)section_id=None\)',
    lambda m: m.group(0).replace("section_id=None", "section_ids=None"),
    pdf
)
pdf = pdf.replace(
    "section_id=section_id)",
    "section_ids=section_ids)"
)

with open(pdf_path, "w", encoding="utf-8") as f:
    f.write(pdf)
print("✅ pdf_export.py: section_ids対応完了")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. preview.htmlのJinja2変数名を更新
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with open(prev_path, "r", encoding="utf-8") as f:
    prev = f.read()

prev = prev.replace(
    "{% if sec.section_id|string == selected_section_id %}selected{% endif %}",
    "{% if sec.section_id|string in selected_section_ids %}selected{% endif %}"
)

with open(prev_path, "w", encoding="utf-8") as f:
    f.write(prev)
print("✅ preview.html: selected_section_idsに更新しました")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. 構文チェック
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
for p in [app_path, excel_path, pdf_path]:
    r = subprocess.run(
        [r"C:\Users\ynaka\AppData\Local\Programs\Python\Python312\python.exe",
         "-m", "py_compile", p],
        capture_output=True, text=True
    )
    name = os.path.basename(p)
    print(f"{'✅' if r.returncode==0 else '❌'} {name} {'構文OK' if r.returncode==0 else r.stderr}")

print("\n✅ 完了")