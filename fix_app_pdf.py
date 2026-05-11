import os

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")

# ─── app.py にPDFルートを追加 ──────────────────────────
app_path = os.path.join(base, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

pdf_route = '''
@app.route("/export_pdf", methods=["POST"])
def export_pdf_route():
    from pdf_export import export_pdf
    student_id = request.form["student_id"]
    target_date = request.form["date"]
    start_date = request.form.get("start_date", "")
    if not start_date:
        start_date = date.today().isoformat()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM students WHERE student_id=?", (student_id,))
    row = c.fetchone()
    conn.close()
    student_name = row["name"] if row else student_id
    os.makedirs("plan_archives", exist_ok=True)
    output_path = os.path.join(
        "plan_archives", f"計画表_{student_name}_{target_date}.pdf")
    export_pdf(target_date, output_path,
               student_id=student_id, start_date=start_date)
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
    print("✅ app.py にPDFルートを追加しました")
else:
    print("ℹ️ PDFルートはすでに存在します")

# ─── export.html を更新 ────────────────────────────────
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
    <form method="POST" id="export-form" action="/export">
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
          onclick="document.getElementById('export-form').action='/export'; return true;">
          📊 Excelダウンロード
        </button>
        <button type="submit" class="btn-pdf"
          onclick="document.getElementById('export-form').action='/export_pdf'; return true;">
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
print("✅ 完了")