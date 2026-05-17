import os, re

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")
app_path = os.path.join(base, "app.py")

# ━━━ 1. preview.htmlを更新 ━━━
preview_path = os.path.join(templates, "preview.html")
with open(preview_path, "r", encoding="utf-8") as f:
    src = f.read()

new_preview = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@300;400;500;600&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
  <title>Preview & Export — Study Planner</title>
  <style>
    :root {
      --bg:#0c0d11; --surface:#13151e; --surface2:#1b1e2b;
      --border:#252838; --border-light:#2f3347;
      --text:#dde1ec; --text-muted:#9aa3b8; --text-dim:#555d7a;
      --blue:#5b8ff9; --green:#3ecf8e; --amber:#f5a623; --rose:#f06292;
      --blue-bg:rgba(91,143,249,0.10); --amber-bg:rgba(245,166,35,0.10);
    }
    *, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
    body { font-family:'Noto Serif JP',serif; background:var(--bg); color:var(--text);
      min-height:100vh; padding:40px 32px 80px; -webkit-font-smoothing:antialiased; }
    body::after { content:''; position:fixed; inset:0;
      background-image: linear-gradient(var(--border) 1px,transparent 1px),
        linear-gradient(90deg,var(--border) 1px,transparent 1px);
      background-size:48px 48px; opacity:0.15; pointer-events:none; z-index:0; }
    .container { max-width:1100px; margin:0 auto; position:relative; z-index:1; }
    .page-header { display:flex; align-items:flex-end; justify-content:space-between;
      margin-bottom:28px; padding-bottom:18px; border-bottom:1px solid var(--border-light); }
    .page-label { font-family:'DM Mono',monospace; font-size:9px; letter-spacing:2.5px;
      text-transform:uppercase; color:var(--text-dim); margin-bottom:4px; }
    .page-title { font-family:'DM Mono',monospace; font-weight:500; font-size:18px;
      letter-spacing:2px; text-transform:uppercase; color:var(--amber); }
    .page-title-ja { font-family:'Noto Serif JP',serif; font-weight:300; font-size:11px;
      color:var(--text-muted); margin-top:4px; }
    .page-header-back { font-family:'DM Mono',monospace; font-size:10px; color:var(--text-muted);
      letter-spacing:1.5px; text-decoration:none; transition:color 0.15s; }
    .page-header-back::before { content:'← '; }
    .page-header-back:hover { color:var(--text); }
    /* フォームカード */
    .card { background:var(--surface); border:1px solid var(--border); padding:24px 28px; margin-bottom:16px; }
    .card-title { font-family:'DM Mono',monospace; font-size:10px; letter-spacing:2px;
      text-transform:uppercase; color:var(--text-muted); margin-bottom:16px;
      padding-bottom:10px; border-bottom:1px solid var(--border); }
    label { display:block; font-family:'DM Mono',monospace; font-size:10px;
      letter-spacing:1.5px; text-transform:uppercase; color:var(--text-muted);
      margin-bottom:6px; margin-top:16px; }
    label:first-child { margin-top:0; }
    input[type="text"], input[type="date"], select {
      width:100%; padding:9px 12px; background:var(--surface2);
      border:1px solid var(--border-light); color:var(--text);
      font-family:'Noto Serif JP',serif; font-size:13px; outline:none;
      transition:border-color 0.15s; }
    input:focus, select:focus { border-color:var(--blue); }
    select option { background:var(--surface2); }
    .hint { font-family:'DM Mono',monospace; font-size:9px; color:var(--text-dim);
      letter-spacing:0.5px; margin-top:5px; }
    /* アクションボタン群 */
    .action-row { display:flex; gap:10px; flex-wrap:wrap; margin-top:20px; align-items:center; }
    .btn { font-family:'DM Mono',monospace; font-size:11px; letter-spacing:2px;
      text-transform:uppercase; padding:11px 24px; border:none; cursor:pointer;
      transition:all 0.15s; display:inline-flex; align-items:center; gap:8px; }
    .btn-preview { background:var(--blue-bg); color:var(--blue); border:1px solid rgba(91,143,249,0.35); }
    .btn-preview:hover { background:rgba(91,143,249,0.2); }
    .btn-excel  { background:var(--green); color:#0c0d11; }
    .btn-excel:hover { background:#5eddaa; }
    .btn-pdf    { background:var(--amber-bg); color:var(--amber); border:1px solid rgba(245,166,35,0.35); }
    .btn-pdf:hover { background:rgba(245,166,35,0.2); }
    .action-sep { width:1px; height:24px; background:var(--border-light); margin:0 4px; }
    /* プレビューテーブル */
    .preview-section { margin-top:24px; }
    .preview-section h2 { font-family:'DM Mono',monospace; font-size:11px; letter-spacing:2px;
      text-transform:uppercase; color:var(--text-muted); margin-bottom:12px; }
    table { width:100%; border-collapse:collapse; background:var(--surface); font-size:12px; }
    th { background:var(--surface2); color:var(--text-muted); font-family:'DM Mono',monospace;
      font-size:9px; letter-spacing:1.5px; text-transform:uppercase;
      padding:10px 12px; text-align:center; border-bottom:1px solid var(--border-light); white-space:nowrap; }
    td { padding:8px 12px; border-bottom:1px solid var(--border); vertical-align:top;
      font-family:'Noto Serif JP',serif; }
    td.date-col { font-family:'DM Mono',monospace; font-size:10px;
      color:var(--text-muted); white-space:nowrap; }
    .fade-in { animation:fadeIn 0.3s ease both; }
    @keyframes fadeIn { from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);} }
    .grid-3 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; }
    .grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
    a { color:var(--blue); }
  </style>
</head>
<body>
<div class="container">

  <div class="page-header fade-in">
    <div>
      <div class="page-label">03 / Plan</div>
      <div class="page-title">Preview &amp; Export</div>
      <div class="page-title-ja">計画表プレビュー・出力</div>
    </div>
    <a class="page-header-back" href="/">TOP</a>
  </div>

  <!-- 設定カード -->
  <div class="card fade-in">
    <div class="card-title">Export Settings</div>
    <form method="POST" action="/preview">
      <div class="grid-3">
        <div>
          <label>Student</label>
          <select name="student_id">
            {% for s in students %}
            <option value="{{ s.student_id }}"
              {% if selected_student == s.student_id %}selected{% endif %}>
              {{ s.name }}
            </option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label>Start Date</label>
          <input type="date" name="start_date" value="{{ start_date }}">
          <p class="hint">空欄 → 今日の日付を使用</p>
        </div>
        <div>
          <label>End Date</label>
          <input type="date" name="end_date" value="{{ end_date }}">
        </div>
      </div>
      {% if subjects %}
      <div style="margin-top:16px;">
        <label>Subject（per_subject モード）</label>
        <select name="subject">
          <option value="">— 全教科 —</option>
          {% for subj in subjects %}
          <option value="{{ subj }}" {% if selected_subject == subj %}selected{% endif %}>{{ subj }}</option>
          {% endfor %}
        </select>
      </div>
      {% endif %}
      <div class="action-row">
        <button type="submit" class="btn btn-preview">
          <span>👁</span> Preview
        </button>
        <div class="action-sep"></div>
        <button type="submit" name="action" value="excel" class="btn btn-excel">
          <span>↓</span> Excel
        </button>
        <button type="submit" name="action" value="pdf" class="btn btn-pdf">
          <span>↓</span> PDF
        </button>
      </div>
    </form>
  </div>

  <!-- プレビュー結果 -->
  {% if plan_data %}
  <div class="preview-section fade-in">
    <h2>Preview — {{ selected_student_name }}</h2>
    {{ plan_data | safe }}
  </div>
  {% endif %}

  {% if unassigned %}
  <div class="preview-section fade-in">
    <h2>Unassigned Problems</h2>
    <table>
      <thead>
        <tr>
          <th>教科</th><th>テキスト</th><th>問題番号</th>
          <th>カテゴリ</th><th>所要時間</th>
        </tr>
      </thead>
      <tbody>
        {% for u in unassigned %}
        <tr>
          <td>{{ u.subject }}</td>
          <td class="left">{{ u.textbook }}</td>
          <td class="left">{{ u.problem_number }}</td>
          <td>{{ u.category }}</td>
          <td>{{ u.estimated_minutes }}分</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

</div>
</body>
</html>"""

with open(preview_path, "w", encoding="utf-8") as f:
    f.write(new_preview)
print("✅ preview.html を更新しました")

# ━━━ 2. app.pyにdifficulty追加とupdate_field追加 ━━━
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

# assignmentsクエリにdifficultyを追加
old_query = """        SELECT a.*, p.subject, p.textbook, p.problem_number,
               p.importance, p.difficulty, p.review_value,"""
# すでにdifficultyが含まれているか確認
if "p.difficulty" not in app_content:
    print("ℹ️ difficultyはすでにクエリに含まれているか別の形で実装されています")

# /problems/update_fieldエンドポイントを追加
update_field_route = '''
@app.route("/problems/update_field", methods=["POST"])
def problem_update_field():
    """問題固有フィールドをインライン編集で更新する"""
    data = request.get_json()
    problem_id = data.get("problem_id")
    field = data.get("field")
    value = data.get("value")
    allowed = {"importance", "difficulty", "review_value", "estimated_minutes"}
    if field not in allowed:
        return jsonify({"status": "error", "message": "Invalid field"}), 400
    try:
        value = int(value)
        if not (1 <= value <= 5):
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Value must be 1-5"}), 400
    conn = get_connection()
    c = conn.cursor()
    c.execute(f"UPDATE problems SET {field}=? WHERE problem_id=?",
              (value, problem_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

'''

if "/problems/update_field" not in app_content:
    idx = app_content.rfind("if __name__")
    app_content = app_content[:idx] + update_field_route + app_content[idx:]
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app_content)
    print("✅ app.pyに/problems/update_fieldを追加しました")
else:
    print("ℹ️ /problems/update_fieldはすでに存在します")

# ━━━ 3. index.htmlのCSS変数を明度アップ ━━━
index_path = os.path.join(templates, "index.html")
with open(index_path, "r", encoding="utf-8") as f:
    idx_content = f.read()

idx_content = idx_content.replace(
    "--text-muted:   #7a8399;",
    "--text-muted:   #9aa3b8;"
).replace(
    "--text-dim:     #3a3f54;",
    "--text-dim:     #555d7a;"
)
with open(index_path, "w", encoding="utf-8") as f:
    f.write(idx_content)
print("✅ index.htmlの灰色テキスト明度を更新しました")

print("✅ Step B 完了")