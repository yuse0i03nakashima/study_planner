import os

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")

preview_html = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>計画表プレビュー</title>
  <style>
    body { font-family: sans-serif; max-width: 1200px; margin: 40px auto; background: #f5f7fa; }
    h1 { color: #2c3e50; }
    .form-box { background: white; padding: 24px; border-radius: 8px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    label { display: block; margin-top: 12px; font-weight: bold; }
    select, input[type="date"] { width: 100%; padding: 8px; margin-top: 4px; border: 1px solid #ccc; border-radius: 4px; font-size: 15px; box-sizing: border-box; }
    .btn-row { display: flex; gap: 12px; margin-top: 16px; flex-wrap: wrap; }
    button { padding: 10px 24px; color: white; border: none; border-radius: 6px; font-size: 15px; cursor: pointer; }
    .btn-preview { background: #4472C4; }
    .btn-preview:hover { background: #2c5fa8; }
    .btn-excel { background: #27ae60; }
    .btn-excel:hover { background: #1e8449; }
    .btn-pdf { background: #e74c3c; }
    .btn-pdf:hover { background: #c0392b; }
    .preview-box { background: white; border-radius: 8px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); overflow-x: auto; }
    h2 { color: #2c3e50; margin-bottom: 16px; }
    table { border-collapse: collapse; width: 100%; }
    th { background: #4472C4; color: white; padding: 10px 14px; text-align: center; white-space: nowrap; }
    td { border: 1px solid #ddd; padding: 10px 12px; vertical-align: top; min-width: 180px; }
    td.date-cell { background: #e8eef8; font-weight: bold; text-align: center; white-space: nowrap; width: 100px; }
    td.unassigned-label { background: #f0f0f0; font-weight: bold; text-align: center; }
    .problem-item { margin-bottom: 8px; padding: 6px 8px; border-radius: 4px; font-size: 13px; line-height: 1.5; }
    .cat-予習  { background: #DDEEFF; }
    .cat-復習  { background: #DDFFDD; }
    .cat-定着  { background: #FFFADD; }
    .cat-再定着 { background: #FFE5DD; }
    .cat-label { font-weight: bold; }
    .instruction { color: #555; font-size: 12px; margin-top: 2px; }
    p.note { color: #888; font-size: 13px; margin-top: 6px; }
    a { color: #4472C4; }
  </style>
</head>
<body>
  <h1>④ 計画表プレビュー・出力</h1>
  <div class="form-box">
    <form method="POST" id="main-form">
      <input type="hidden" name="action" value="preview">
      <label>生徒</label>
      <select name="student_id">
        {% for s in students %}
        <option value="{{ s.student_id }}"
          {% if selected.get('student_id') == s.student_id %}selected{% endif %}>
          {{ s.name }}
        </option>
        {% endfor %}
      </select>

      <label>次回授業日（計画終了日）</label>
      <input type="date" name="date" value="{{ selected.get('date', '') }}" required>

      <label>計画開始日（任意・空欄で今日）</label>
      <input type="date" name="start_date" value="{{ selected.get('start_date', '') }}">
      <p class="note">空欄の場合は今日の日付が自動的に使われます。</p>

      <div class="btn-row">
        <button type="submit" class="btn-preview"
          onclick="document.getElementById('main-form').action='/preview';">
          🔍 プレビュー
        </button>
        <button type="submit" class="btn-excel"
          onclick="document.getElementById('main-form').action='/export';">
          📊 Excelダウンロード
        </button>
        <button type="submit" class="btn-pdf"
          onclick="document.getElementById('main-form').action='/export_pdf';">
          📄 PDFダウンロード
        </button>
      </div>
    </form>
  </div>

  {% if preview_data %}
  <div class="preview-box">
    <h2>{{ preview_data.student_name }} の学習計画</h2>
    <table>
      <tr>
        <th>実施日</th>
        {% for subject in preview_data.subjects %}
        <th>{{ subject }}</th>
        {% endfor %}
      </tr>
      {% for row in preview_data.rows %}
      <tr>
        <td class="date-cell">{{ row.date }}</td>
        {% for subject in preview_data.subjects %}
        <td>
          {% for item in row.subjects.get(subject, []) %}
          <div class="problem-item cat-{{ item.category }}">
            <div class="cat-label">【{{ item.category }}】{{ item.textbook }} {{ item.problem_number }}</div>
            {% if item.instruction %}
            <div class="instruction">{{ item.instruction }}</div>
            {% endif %}
          </div>
          {% endfor %}
        </td>
        {% endfor %}
      </tr>
      {% endfor %}
      {% if preview_data.unassigned.values() | sum(start=[]) %}
      <tr>
        <td class="unassigned-label">未割当</td>
        {% for subject in preview_data.subjects %}
        <td>
          {% for item in preview_data.unassigned.get(subject, []) %}
          <div class="problem-item cat-{{ item.category }}">
            <div class="cat-label">【{{ item.category }}】{{ item.textbook }} {{ item.problem_number }}</div>
            {% if item.instruction %}
            <div class="instruction">{{ item.instruction }}</div>
            {% endif %}
          </div>
          {% endfor %}
        </td>
        {% endfor %}
      </tr>
      {% endif %}
    </table>
  </div>
  {% endif %}

  <p><a href="/">← トップに戻る</a></p>
</body>
</html>"""

with open(os.path.join(templates, "preview.html"), "w", encoding="utf-8") as f:
    f.write(preview_html)
print("✅ preview.html を更新しました")