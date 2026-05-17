import os

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")

# ━━━ 共通CSS（全ページで使い回す） ━━━
COMMON_HEAD = """  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@300;400;500;600&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg:           #0c0d11;
      --surface:      #13151e;
      --surface2:     #1b1e2b;
      --surface3:     #222536;
      --border:       #252838;
      --border-light: #2f3347;
      --text:         #dde1ec;
      --text-muted:   #7a8399;
      --text-dim:     #3a3f54;
      --blue:   #5b8ff9;
      --green:  #3ecf8e;
      --amber:  #f5a623;
      --rose:   #f06292;
      --red:    #ef4444;
      --blue-bg:  rgba(91,143,249,0.10);
      --green-bg: rgba(62,207,142,0.10);
      --amber-bg: rgba(245,166,35,0.10);
      --rose-bg:  rgba(240,98,146,0.10);
    }
    *, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
    body {
      font-family: 'Noto Serif JP', serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 40px 32px 80px;
      -webkit-font-smoothing: antialiased;
    }
    body::after {
      content: '';
      position: fixed;
      inset: 0;
      background-image:
        linear-gradient(var(--border) 1px, transparent 1px),
        linear-gradient(90deg, var(--border) 1px, transparent 1px);
      background-size: 48px 48px;
      opacity: 0.15;
      pointer-events: none;
      z-index: 0;
    }
    .container { max-width: 1100px; margin: 0 auto; position: relative; z-index: 1; }
    /* ── ページヘッダー ── */
    .page-header {
      display: flex; align-items: flex-end; justify-content: space-between;
      margin-bottom: 32px; padding-bottom: 20px;
      border-bottom: 1px solid var(--border-light);
    }
    .page-header-left { display: flex; align-items: flex-end; gap: 14px; }
    .page-header-back {
      font-family: 'DM Mono', monospace; font-size: 10px;
      color: var(--text-muted); letter-spacing: 1.5px; text-decoration: none;
      display: flex; align-items: center; gap: 6px;
      transition: color 0.15s;
    }
    .page-header-back:hover { color: var(--text); }
    .page-header-back::before { content: '←'; }
    .page-title-block {}
    .page-label {
      font-family: 'DM Mono', monospace; font-size: 9px;
      letter-spacing: 2.5px; text-transform: uppercase;
      color: var(--text-dim); margin-bottom: 4px;
    }
    .page-title {
      font-family: 'DM Mono', monospace; font-weight: 500;
      font-size: 18px; letter-spacing: 2px; text-transform: uppercase;
    }
    .page-title-ja {
      font-family: 'Noto Serif JP', serif; font-weight: 300;
      font-size: 11px; color: var(--text-muted); margin-top: 4px;
      letter-spacing: 0.5px;
    }
    /* ── カード・フォームボックス ── */
    .card {
      background: var(--surface); border: 1px solid var(--border);
      padding: 24px 28px; margin-bottom: 20px;
    }
    .card-title {
      font-family: 'DM Mono', monospace; font-size: 10px;
      letter-spacing: 2px; text-transform: uppercase;
      color: var(--text-muted); margin-bottom: 16px;
      padding-bottom: 10px; border-bottom: 1px solid var(--border);
    }
    /* ── フォーム要素 ── */
    label {
      display: block; font-family: 'DM Mono', monospace;
      font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase;
      color: var(--text-muted); margin-bottom: 6px; margin-top: 16px;
    }
    label:first-child { margin-top: 0; }
    input[type="text"], input[type="date"], input[type="number"],
    select, textarea {
      width: 100%; padding: 9px 12px;
      background: var(--surface2); border: 1px solid var(--border-light);
      color: var(--text); font-family: 'Noto Serif JP', serif;
      font-size: 13px; outline: none;
      transition: border-color 0.15s;
    }
    input[type="text"]:focus, input[type="date"]:focus,
    input[type="number"]:focus, select:focus, textarea:focus {
      border-color: var(--blue);
    }
    select option { background: var(--surface2); }
    textarea { resize: vertical; min-height: 60px; }
    /* ── ボタン ── */
    .btn {
      font-family: 'DM Mono', monospace; font-size: 11px;
      letter-spacing: 2px; text-transform: uppercase;
      padding: 10px 24px; border: none; cursor: pointer;
      transition: all 0.15s; display: inline-flex;
      align-items: center; gap: 8px;
    }
    .btn-primary { background: var(--blue); color: #0c0d11; }
    .btn-primary:hover { background: #7aaafb; }
    .btn-success { background: var(--green); color: #0c0d11; }
    .btn-success:hover { background: #5eddaa; }
    .btn-danger  { background: var(--red);  color: white; }
    .btn-danger:hover  { background: #f87171; }
    .btn-ghost {
      background: transparent; color: var(--text-muted);
      border: 1px solid var(--border-light);
    }
    .btn-ghost:hover { border-color: var(--text-muted); color: var(--text); }
    /* ── テーブル ── */
    .data-table {
      width: 100%; border-collapse: collapse;
      background: var(--surface); font-size: 12px;
    }
    .data-table th {
      background: var(--surface2); color: var(--text-muted);
      font-family: 'DM Mono', monospace; font-size: 9px;
      letter-spacing: 1.5px; text-transform: uppercase;
      padding: 10px 12px; text-align: center;
      border-bottom: 1px solid var(--border-light);
      white-space: nowrap;
    }
    .data-table td {
      padding: 9px 12px; border-bottom: 1px solid var(--border);
      text-align: center; vertical-align: middle;
      font-family: 'Noto Serif JP', serif;
    }
    .data-table tr:hover td { background: var(--surface2); }
    .data-table td.left { text-align: left; }
    /* ── バッジ（カテゴリ） ── */
    .badge {
      font-family: 'DM Mono', monospace; font-size: 9px;
      letter-spacing: 1px; padding: 2px 8px; display: inline-block;
    }
    .badge-予習  { background: var(--blue-bg);  color: var(--blue);  border: 1px solid rgba(91,143,249,0.3); }
    .badge-復習  { background: var(--green-bg); color: var(--green); border: 1px solid rgba(62,207,142,0.3); }
    .badge-定着  { background: var(--amber-bg); color: var(--amber); border: 1px solid rgba(245,166,35,0.3); }
    .badge-再定着 { background: var(--rose-bg);  color: var(--rose);  border: 1px solid rgba(240,98,146,0.3); }
    /* ── セレクト（カテゴリ色付き） ── */
    select.cat-予習  { border-left: 2px solid var(--blue); }
    select.cat-復習  { border-left: 2px solid var(--green); }
    select.cat-定着  { border-left: 2px solid var(--amber); }
    select.cat-再定着 { border-left: 2px solid var(--rose); }
    /* ── グリッドレイアウト ── */
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
    /* ── フィルターバー ── */
    .filter-bar {
      background: var(--surface); border: 1px solid var(--border);
      padding: 16px 20px; margin-bottom: 16px;
      display: flex; gap: 16px; align-items: flex-end; flex-wrap: wrap;
    }
    .filter-bar label { margin: 0 0 4px 0; }
    .filter-bar select, .filter-bar input { width: auto; }
    /* ── 一括更新バー ── */
    .bulk-bar {
      background: var(--surface2); border: 1px solid var(--border-light);
      border-left: 2px solid var(--green);
      padding: 12px 20px; margin-bottom: 12px;
      display: flex; align-items: center; gap: 16px;
    }
    .bulk-bar-label {
      font-family: 'DM Mono', monospace; font-size: 10px;
      letter-spacing: 1.5px; text-transform: uppercase;
      color: var(--text-muted);
    }
    /* ── カウント・メタ情報 ── */
    .meta-text {
      font-family: 'DM Mono', monospace; font-size: 10px;
      color: var(--text-dim); letter-spacing: 1px;
    }
    /* ── チェックボックス ── */
    input[type="checkbox"] { accent-color: var(--blue); width: 14px; height: 14px; }
    /* ── 習熟度 ── */
    .mastery-1 { color: var(--rose); }
    .mastery-2 { color: var(--amber); }
    .mastery-3 { color: var(--green); }
    /* ── アニメーション ── */
    .fade-in { animation: fadeIn 0.3s ease both; }
    @keyframes fadeIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
    /* ── アラート ── */
    .alert {
      font-family: 'DM Mono', monospace; font-size: 11px;
      letter-spacing: 1px; padding: 10px 16px;
      margin-bottom: 16px; border-left: 2px solid;
    }
    .alert-success { background: var(--green-bg); color: var(--green); border-color: var(--green); }
    .alert-error   { background: rgba(239,68,68,0.08); color: #f87171; border-color: var(--red); }
    .alert-info    { background: var(--blue-bg); color: var(--blue); border-color: var(--blue); }
  </style>"""

# ━━━ ページヘッダーHTML生成関数 ━━━
def page_header(num, en, ja, color="var(--text)"):
    return f"""  <div class="container">
  <div class="page-header fade-in">
    <div class="page-header-left">
      <div class="page-title-block">
        <div class="page-label">{num}</div>
        <div class="page-title" style="color:{color};">{en}</div>
        <div class="page-title-ja">{ja}</div>
      </div>
    </div>
    <a class="page-header-back" href="/">TOP</a>
  </div>"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 出題予定管理（assignments_list.html）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
assignments_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
{COMMON_HEAD}
  <title>Assignments — Study Planner</title>
  <style>
    .row-予習  td {{ border-left: 2px solid var(--blue);  }}
    .row-復習  td:first-child {{ border-left: 2px solid var(--green); }}
    .row-復習  {{ border-left: 2px solid var(--green); }}
    .row-定着  {{ border-left: 2px solid var(--amber); }}
    .row-再定着 {{ border-left: 2px solid var(--rose);  }}
    tr.changed-row td {{ outline: 1px solid var(--amber); outline-offset: -1px; }}
  </style>
</head>
<body>
{page_header("04 / Records", "Assignments", "出題予定管理", "var(--rose)")}

  <!-- フィルター -->
  <div class="filter-bar fade-in">
    <form method="GET" style="display:contents;">
      <div>
        <label>Student</label>
        <select name="student_id" onchange="this.form.submit()" style="min-width:140px;">
          {{% for s in students %}}
          <option value="{{{{ s.student_id }}}}"
            {{%- if s.student_id == selected_student %}} selected{{%- endif %}}>
            {{{{ s.name }}}}
          </option>
          {{%- endfor %}}
        </select>
      </div>
    </form>
    <span class="meta-text" style="margin-left:auto;">{{{{ assignments | length }}}} items</span>
  </div>

  <!-- 一括更新バー -->
  <div class="bulk-bar fade-in">
    <span class="bulk-bar-label">Bulk Edit</span>
    <button class="btn btn-success" onclick="bulkUpdate()">✓ Apply Changes</button>
    <span id="change-count" class="meta-text"></span>
  </div>

  <!-- テーブル -->
  <div class="fade-in" style="overflow-x:auto;">
  <table class="data-table" id="assignments-table">
    <thead>
      <tr>
        <th><input type="checkbox" id="check-all" onchange="toggleAll(this)"></th>
        <th>Subject</th><th>Textbook</th><th>Problem</th>
        <th>Imp</th><th>RV</th><th>Mastery</th>
        <th>Category</th><th>Date</th><th>Del</th>
      </tr>
    </thead>
    <tbody>
    {{%- for a in assignments %}}
    <tr id="row-{{{{ a.assignment_id }}}}" class="row-{{{{ a.category }}}}">
      <td><input type="checkbox" class="row-check" value="{{{{ a.assignment_id }}}}"></td>
      <td class="meta-text">{{{{ a.subject }}}}</td>
      <td class="left" style="font-size:11px;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{{{ a.textbook }}}}</td>
      <td class="left" style="font-size:11px;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{{{ a.problem_number }}}}</td>
      <td class="meta-text">{{{{ a.importance }}}}</td>
      <td class="meta-text">{{{{ a.review_value }}}}</td>
      <td>
        {{%- set m = a.mastery or 1 %}}
        <span class="mastery-{{{{ m }}}}">{{{{ '★' * m }}}}</span>
      </td>
      <td>
        <select class="edit-field" data-id="{{{{ a.assignment_id }}}}" data-field="category"
          onchange="markChanged(this, {{{{ a.assignment_id }}}})">
          {{%- for cat in ['予習','復習','定着','再定着'] %}}
          <option value="{{{{ cat }}}}" {{%- if cat == a.category %}} selected{{%- endif %}}>{{{{ cat }}}}</option>
          {{%- endfor %}}
        </select>
      </td>
      <td>
        <input type="date" class="edit-field" data-id="{{{{ a.assignment_id }}}}" data-field="scheduled_date"
          value="{{{{ '' if a.scheduled_date == '2099-12-31' else a.scheduled_date }}}}"
          onchange="markChanged(this, {{{{ a.assignment_id }}}})"
          style="width:130px;">
      </td>
      <td>
        <button class="btn btn-danger" style="padding:4px 10px;font-size:9px;"
          onclick="deleteAssignment({{{{ a.assignment_id }}}}, this)">×</button>
      </td>
    </tr>
    {{%- endfor %}}
    </tbody>
  </table>
  </div>

<script>
  const changedRows = new Map();

  function markChanged(el, id) {{
    const row = document.getElementById('row-' + id);
    const fields = row.querySelectorAll('.edit-field');
    const data = {{}};
    fields.forEach(f => {{ data[f.dataset.field] = f.value; }});
    changedRows.set(id, data);
    row.classList.add('changed-row');
    document.getElementById('change-count').textContent =
      changedRows.size + ' row(s) pending';
  }}

  async function bulkUpdate() {{
    if (changedRows.size === 0) {{ alert('No changes to apply.'); return; }}
    const updates = [];
    changedRows.forEach((data, id) => updates.push({{ assignment_id: id, ...data }}));
    const res = await fetch('/assignments/bulk_update', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ student_id: '{{{{ selected_student }}}}', updates }})
    }});
    if (res.ok) {{
      changedRows.forEach((data, id) => {{
        const row = document.getElementById('row-' + id);
        if (row) {{
          row.classList.remove('changed-row');
          row.className = 'row-' + data.category;
        }}
      }});
      changedRows.clear();
      document.getElementById('change-count').textContent = '✓ Saved';
      setTimeout(() => document.getElementById('change-count').textContent = '', 3000);
    }} else {{ alert('Error saving changes.'); }}
  }}

  function toggleAll(cb) {{
    document.querySelectorAll('.row-check').forEach(c => c.checked = cb.checked);
  }}

  async function deleteAssignment(id, btn) {{
    if (!confirm('Delete this assignment?')) return;
    const res = await fetch('/assignments/delete/' + id, {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
      body: 'student_id={{{{ selected_student }}}}'
    }});
    if (res.ok || res.redirected) {{
      document.getElementById('row-' + id)?.remove();
    }} else {{ alert('Delete failed.'); }}
  }}
</script>
</div>
</body>
</html>"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 授業記録入力（record.html）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
record_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
{COMMON_HEAD}
  <title>Add Record — Study Planner</title>
</head>
<body>
{page_header("04 / Records", "Add Record", "授業記録入力", "var(--rose)")}

  {{%- with messages = get_flashed_messages(with_categories=true) %}}
  {{%- for cat, msg in messages %}}
  <div class="alert alert-{{{{ 'success' if cat == 'success' else 'error' }}}} fade-in">{{{{ msg }}}}</div>
  {{%- endfor %}}
  {{%- endwith %}}

  <div class="card fade-in">
    <div class="card-title">Record Entry</div>
    <form method="POST" action="/record">
      <div class="grid-2">
        <div>
          <label>Student</label>
          <select name="student_id" id="student-select" onchange="filterProblems()">
            {{%- for s in students %}}
            <option value="{{{{ s.student_id }}}}">{{{{ s.name }}}}</option>
            {{%- endfor %}}
          </select>
        </div>
        <div>
          <label>Date</label>
          <input type="date" name="record_date" value="{{{{ today }}}}">
        </div>
      </div>
      <div class="grid-2">
        <div>
          <label>Problem</label>
          <select name="problem_id" id="problem-select">
            {{%- for p in problems %}}
            <option value="{{{{ p.problem_id }}}}" data-student="{{{{ p.student_ids }}}}">
              [{{{{ p.subject }}}}] {{{{ p.textbook }}}} {{{{ p.problem_number }}}}
            </option>
            {{%- endfor %}}
          </select>
        </div>
        <div>
          <label>Result</label>
          <select name="correct">
            <option value="1">✓ Correct</option>
            <option value="0">✗ Incorrect</option>
          </select>
        </div>
      </div>
      <div style="margin-top:20px;">
        <button type="submit" class="btn btn-primary">Register Record →</button>
      </div>
    </form>
  </div>

<script>
  function filterProblems() {{
    const sid = document.getElementById('student-select').value;
    const sel = document.getElementById('problem-select');
    for (const opt of sel.options) {{
      const ids = (opt.dataset.student || '').split(',');
      opt.hidden = !ids.includes(sid);
    }}
    for (const opt of sel.options) {{
      if (!opt.hidden) {{ opt.selected = true; break; }}
    }}
  }}
  filterProblems();
</script>
</div>
</body>
</html>"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 授業記録修正（record_list.html）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
record_list_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
{COMMON_HEAD}
  <title>Edit Records — Study Planner</title>
</head>
<body>
{page_header("04 / Records", "Edit Records", "授業記録修正・習熟度変更", "var(--rose)")}

  <!-- フィルター -->
  <div class="filter-bar fade-in">
    <form method="GET" style="display:contents;">
      <div>
        <label>Student</label>
        <select name="student_id" onchange="this.form.submit()" style="min-width:140px;">
          {{%- for s in students %}}
          <option value="{{{{ s.student_id }}}}"
            {{%- if s.student_id == selected_student %}} selected{{%- endif %}}>
            {{{{ s.name }}}}
          </option>
          {{%- endfor %}}
        </select>
      </div>
    </form>
    <span class="meta-text" style="margin-left:auto;">{{{{ records | length }}}} records</span>
  </div>

  <!-- 一括更新バー -->
  <div class="bulk-bar fade-in">
    <span class="bulk-bar-label">Bulk Edit</span>
    <button class="btn btn-success" onclick="bulkUpdateMastery()">✓ Apply Mastery Changes</button>
    <span id="mastery-change-count" class="meta-text"></span>
  </div>

  <!-- テーブル -->
  <div class="fade-in" style="overflow-x:auto;">
  <table class="data-table">
    <thead>
      <tr>
        <th>Date</th><th>Subject</th><th>Textbook</th><th>Problem</th>
        <th>Result</th><th>Mastery</th><th>Category</th>
      </tr>
    </thead>
    <tbody>
    {{%- for r in records %}}
    <tr>
      <td class="meta-text" style="white-space:nowrap;">{{{{ r.date }}}}</td>
      <td class="meta-text">{{{{ r.subject }}}}</td>
      <td class="left" style="font-size:11px;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{{{ r.textbook }}}}</td>
      <td class="left" style="font-size:11px;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{{{ r.problem_number }}}}</td>
      <td>
        {{%- if r.correct == 1 %}}
        <span style="color:var(--green);font-family:'DM Mono',monospace;font-size:11px;">✓</span>
        {{%- else %}}
        <span style="color:var(--rose);font-family:'DM Mono',monospace;font-size:11px;">✗</span>
        {{%- endif %}}
      </td>
      <td>
        <select class="mastery-select" data-id="{{{{ r.history_id }}}}"
          style="width:80px;"
          onchange="markMasteryChanged(this, {{{{ r.history_id }}}})">
          {{%- for m in [1,2,3] %}}
          <option value="{{{{ m }}}}" {{%- if m == r.mastery %}} selected{{%- endif %}}>
            {{{{ '★' * m }}}}
          </option>
          {{%- endfor %}}
        </select>
      </td>
      <td><span class="badge badge-{{{{ r.category or '—' }}}}">{{{{ r.category or '—' }}}}</span></td>
    </tr>
    {{%- endfor %}}
    </tbody>
  </table>
  </div>

<script>
  const masteryChanges = new Map();

  function markMasteryChanged(el, id) {{
    masteryChanges.set(id, parseInt(el.value));
    el.style.borderColor = 'var(--amber)';
    document.getElementById('mastery-change-count').textContent =
      masteryChanges.size + ' row(s) pending';
  }}

  async function bulkUpdateMastery() {{
    if (masteryChanges.size === 0) {{ alert('No changes to apply.'); return; }}
    const updates = [];
    masteryChanges.forEach((mastery, id) => updates.push({{ history_id: id, mastery }}));
    const res = await fetch('/mastery/bulk_update', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ updates }})
    }});
    if (res.ok) {{
      masteryChanges.forEach((_, id) => {{
        const sel = document.querySelector('.mastery-select[data-id="' + id + '"]');
        if (sel) sel.style.borderColor = '';
      }});
      masteryChanges.clear();
      document.getElementById('mastery-change-count').textContent = '✓ Saved';
      setTimeout(() => document.getElementById('mastery-change-count').textContent = '', 3000);
    }} else {{ alert('Error saving changes.'); }}
  }}
</script>
</div>
</body>
</html>"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 計画表プレビュー（preview.html）を読み込んでヘッダーだけ置換
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
preview_path = os.path.join(templates, "preview.html")
with open(preview_path, "r", encoding="utf-8") as f:
    preview_src = f.read()

# 既存のpreview.htmlのstyleとbodyを最小限にダークテーマ対応
preview_dark_style = """  <style>
    body { background:#0c0d11; color:#dde1ec; font-family:'Noto Serif JP',serif; padding:32px; }
    body::after { content:''; position:fixed; inset:0;
      background-image: linear-gradient(#252838 1px,transparent 1px),
        linear-gradient(90deg,#252838 1px,transparent 1px);
      background-size:48px 48px; opacity:0.15; pointer-events:none; z-index:0; }
    .container { max-width:1100px; margin:0 auto; position:relative; z-index:1; }
    .page-header { display:flex; align-items:flex-end; justify-content:space-between;
      margin-bottom:28px; padding-bottom:16px; border-bottom:1px solid #2f3347; }
    .page-label { font-family:'DM Mono',monospace; font-size:9px; letter-spacing:2.5px;
      text-transform:uppercase; color:#3a3f54; margin-bottom:4px; }
    .page-title { font-family:'DM Mono',monospace; font-weight:500; font-size:18px;
      letter-spacing:2px; text-transform:uppercase; color:var(--amber,#f5a623); }
    .page-title-ja { font-family:'Noto Serif JP',serif; font-weight:300; font-size:11px;
      color:#7a8399; margin-top:4px; }
    .page-header-back { font-family:'DM Mono',monospace; font-size:10px; color:#7a8399;
      letter-spacing:1.5px; text-decoration:none; }
    .page-header-back::before { content:'← '; }
    .page-header-back:hover { color:#dde1ec; }
    select, input[type=date], input[type=text] {
      background:#1b1e2b; border:1px solid #2f3347; color:#dde1ec;
      padding:8px 12px; font-family:'Noto Serif JP',serif; font-size:13px; }
    .btn { font-family:'DM Mono',monospace; font-size:11px; letter-spacing:2px;
      text-transform:uppercase; padding:10px 24px; border:none; cursor:pointer; }
    .btn-primary { background:#5b8ff9; color:#0c0d11; }
    .btn-primary:hover { background:#7aaafb; }
    .btn-success { background:#3ecf8e; color:#0c0d11; }
    table { width:100%; border-collapse:collapse; background:#13151e; font-size:12px; margin-top:20px; }
    th { background:#1b1e2b; color:#7a8399; font-family:'DM Mono',monospace; font-size:9px;
      letter-spacing:1.5px; text-transform:uppercase; padding:10px 12px;
      border-bottom:1px solid #2f3347; white-space:nowrap; }
    td { padding:8px 12px; border-bottom:1px solid #252838; vertical-align:top;
      font-family:'Noto Serif JP',serif; }
    label { font-family:'DM Mono',monospace; font-size:10px; letter-spacing:1.5px;
      text-transform:uppercase; color:#7a8399; display:block; margin-bottom:6px; }
    .filter-bar { background:#13151e; border:1px solid #252838; padding:16px 20px;
      margin-bottom:16px; display:flex; gap:16px; align-items:flex-end; flex-wrap:wrap; }
    a { color:#5b8ff9; }
    h2 { font-family:'DM Mono',monospace; font-size:12px; letter-spacing:2px;
      text-transform:uppercase; color:#7a8399; margin:24px 0 12px; }
  </style>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@300;400;500&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">"""

# previewのstyleタグを置換（既存のstyleがあれば）
import re
if "<style>" in preview_src:
    preview_src = re.sub(r"<style>.*?</style>", preview_dark_style, preview_src, flags=re.DOTALL)
else:
    preview_src = preview_src.replace("</head>", preview_dark_style + "\n</head>")

# previewのh1をページヘッダーに置換
old_h1_pattern = re.compile(r"<h1[^>]*>.*?</h1>", re.DOTALL)
new_header = """<div class="container">
  <div class="page-header">
    <div>
      <div class="page-label">03 / Plan</div>
      <div class="page-title">Preview &amp; Export</div>
      <div class="page-title-ja">計画表プレビュー・出力</div>
    </div>
    <a class="page-header-back" href="/">TOP</a>
  </div>"""

if old_h1_pattern.search(preview_src):
    preview_src = old_h1_pattern.sub(new_header, preview_src, count=1)
    # body直後に<div class="container">が必要な場合の調整
    if "<body>" in preview_src and "<div class=\"container\">" not in preview_src[:preview_src.index(new_header)+50]:
        preview_src = preview_src.replace("<body>", "<body>", 1)

with open(preview_path, "w", encoding="utf-8") as f:
    f.write(preview_src)
print("✅ preview.html にダークテーマを適用しました")

# ━━━ ファイル書き出し ━━━
files = {
    "assignments_list.html": assignments_html,
    "record.html":           record_html,
    "record_list.html":      record_list_html,
}

for fname, content in files.items():
    path = os.path.join(templates, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ {fname} を更新しました")

print("\n✅ デザイン統一完了（3ページ + preview）")