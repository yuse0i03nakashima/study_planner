import os

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")

COMMON_HEAD = """\
  <meta charset="UTF-8">
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
      --text-muted:   #9aa3b8;
      --text-dim:     #555d7a;
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
      background: var(--bg); color: var(--text);
      min-height: 100vh; padding: 40px 32px 80px;
      -webkit-font-smoothing: antialiased;
    }
    body::after {
      content: ''; position: fixed; inset: 0;
      background-image:
        linear-gradient(var(--border) 1px, transparent 1px),
        linear-gradient(90deg, var(--border) 1px, transparent 1px);
      background-size: 48px 48px; opacity: 0.15;
      pointer-events: none; z-index: 0;
    }
    .container { max-width:1200px; margin:0 auto; position:relative; z-index:1; }
    .page-header {
      display:flex; align-items:flex-end; justify-content:space-between;
      margin-bottom:28px; padding-bottom:18px;
      border-bottom:1px solid var(--border-light);
    }
    .page-label { font-family:'DM Mono',monospace; font-size:9px;
      letter-spacing:2.5px; text-transform:uppercase; color:var(--text-dim); margin-bottom:4px; }
    .page-title { font-family:'DM Mono',monospace; font-weight:500;
      font-size:18px; letter-spacing:2px; text-transform:uppercase; }
    .page-title-ja { font-family:'Noto Serif JP',serif; font-weight:300;
      font-size:11px; color:var(--text-muted); margin-top:4px; }
    .page-header-back { font-family:'DM Mono',monospace; font-size:10px;
      color:var(--text-muted); letter-spacing:1.5px; text-decoration:none; transition:color 0.15s; }
    .page-header-back::before { content:'← '; }
    .page-header-back:hover { color:var(--text); }
    .card { background:var(--surface); border:1px solid var(--border); padding:24px 28px; margin-bottom:20px; }
    .card-title { font-family:'DM Mono',monospace; font-size:10px; letter-spacing:2px;
      text-transform:uppercase; color:var(--text-muted); margin-bottom:16px;
      padding-bottom:10px; border-bottom:1px solid var(--border); }
    label { display:block; font-family:'DM Mono',monospace; font-size:10px;
      letter-spacing:1.5px; text-transform:uppercase; color:var(--text-muted);
      margin-bottom:6px; margin-top:16px; }
    label:first-child { margin-top:0; }
    input[type="text"], input[type="date"], input[type="number"], select, textarea {
      width:100%; padding:9px 12px; background:var(--surface2);
      border:1px solid var(--border-light); color:var(--text);
      font-family:'Noto Serif JP',serif; font-size:13px; outline:none;
      transition:border-color 0.15s;
    }
    input:focus, select:focus, textarea:focus { border-color:var(--blue); }
    select option { background:var(--surface2); }
    textarea { resize:vertical; min-height:60px; }
    .btn { font-family:'DM Mono',monospace; font-size:11px; letter-spacing:2px;
      text-transform:uppercase; padding:10px 24px; border:none; cursor:pointer;
      transition:all 0.15s; display:inline-flex; align-items:center; gap:8px; }
    .btn-primary { background:var(--blue); color:#0c0d11; }
    .btn-primary:hover { background:#7aaafb; }
    .btn-success { background:var(--green); color:#0c0d11; }
    .btn-success:hover { background:#5eddaa; }
    .btn-danger  { background:var(--red); color:white; }
    .btn-danger:hover { background:#f87171; }
    .btn-ghost { background:transparent; color:var(--text-muted); border:1px solid var(--border-light); }
    .btn-ghost:hover { border-color:var(--text-muted); color:var(--text); }
    .btn-sm { padding:5px 14px; font-size:10px; }
    .data-table { width:100%; border-collapse:collapse; background:var(--surface); font-size:12px; }
    .data-table th { background:var(--surface2); color:var(--text-muted);
      font-family:'DM Mono',monospace; font-size:9px; letter-spacing:1.5px;
      text-transform:uppercase; padding:10px 12px; text-align:center;
      border-bottom:1px solid var(--border-light); white-space:nowrap; }
    .data-table td { padding:9px 12px; border-bottom:1px solid var(--border);
      text-align:center; vertical-align:middle; font-family:'Noto Serif JP',serif; }
    .data-table tr:hover td { background:var(--surface2); }
    .data-table td.left { text-align:left; }
    .badge { font-family:'DM Mono',monospace; font-size:9px; letter-spacing:1px;
      padding:2px 8px; display:inline-block; }
    .badge-予習  { background:var(--blue-bg);  color:var(--blue);  border:1px solid rgba(91,143,249,0.3); }
    .badge-復習  { background:var(--green-bg); color:var(--green); border:1px solid rgba(62,207,142,0.3); }
    .badge-定着  { background:var(--amber-bg); color:var(--amber); border:1px solid rgba(245,166,35,0.3); }
    .badge-再定着 { background:var(--rose-bg);  color:var(--rose);  border:1px solid rgba(240,98,146,0.3); }
    .grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
    .grid-3 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; }
    .filter-bar { background:var(--surface); border:1px solid var(--border);
      padding:16px 20px; margin-bottom:16px;
      display:flex; gap:16px; align-items:flex-end; flex-wrap:wrap; }
    .filter-bar label { margin:0 0 4px 0; }
    .filter-bar select, .filter-bar input { width:auto; }
    .bulk-bar { background:var(--surface2); border:1px solid var(--border-light);
      border-left:2px solid var(--green); padding:12px 20px; margin-bottom:12px;
      display:flex; align-items:center; gap:16px; }
    .bulk-label { font-family:'DM Mono',monospace; font-size:10px;
      letter-spacing:1.5px; text-transform:uppercase; color:var(--text-muted); }
    .meta-text { font-family:'DM Mono',monospace; font-size:10px;
      color:var(--text-dim); letter-spacing:1px; }
    input[type="checkbox"] { accent-color:var(--blue); width:14px; height:14px; }
    .mastery-1 { color:var(--rose); }
    .mastery-2 { color:var(--amber); }
    .mastery-3 { color:var(--green); }
    .fade-in { animation:fadeIn 0.3s ease both; }
    @keyframes fadeIn { from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);} }
    .editable { cursor:pointer; padding:2px 6px; border-radius:2px; transition:background 0.12s; }
    .editable:hover { background:var(--surface3); outline:1px dashed var(--border-light); }
    .editable.editing { display:none; }
    .inline-input { background:var(--surface2); border:1px solid var(--blue);
      color:var(--text); padding:4px 8px; font-size:12px; outline:none; }
    .inline-select { background:var(--surface2); border:1px solid var(--blue);
      color:var(--text); padding:4px 6px; font-size:12px; outline:none; }
    .changed-row td { box-shadow:inset 0 0 0 1px var(--amber); }
    .row-予習  { border-left:2px solid var(--blue); }
    .row-復習  { border-left:2px solid var(--green); }
    .row-定着  { border-left:2px solid var(--amber); }
    .row-再定着 { border-left:2px solid var(--rose); }
  </style>"""


def page_header(num, en, ja, color="var(--text)"):
    return (
        '<div class="container">\n'
        '  <div class="page-header fade-in">\n'
        '    <div>\n'
        '      <div class="page-label">' + num + '</div>\n'
        '      <div class="page-title" style="color:' + color + ';">' + en + '</div>\n'
        '      <div class="page-title-ja">' + ja + '</div>\n'
        '    </div>\n'
        '    <a class="page-header-back" href="/">TOP</a>\n'
        '  </div>'
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. assignments_list.html
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
assignments_html = """\
<!DOCTYPE html>
<html lang="ja">
<head>
""" + COMMON_HEAD + """
  <title>Assignments — Study Planner</title>
</head>
<body>
""" + page_header("04 / Records", "Assignments", "出題予定管理", "var(--rose)") + """

  <div class="filter-bar fade-in">
    <form method="GET" style="display:contents;">
      <div>
        <label>Student</label>
        <select name="student_id" onchange="this.form.submit()" style="min-width:140px;">
          {%- for s in students %}
          <option value="{{ s.student_id }}"
            {%- if s.student_id == selected_student %} selected{%- endif %}>
            {{ s.name }}
          </option>
          {%- endfor %}
        </select>
      </div>
    </form>
    <span class="meta-text" style="margin-left:auto;">{{ assignments|length }} items</span>
  </div>

  <div style="font-family:'DM Mono',monospace;font-size:10px;color:var(--text-muted);
    margin-bottom:8px;letter-spacing:0.5px;">
    ※ Imp・Dif・RV はセルをダブルクリックで編集（問題マスタに反映）
  </div>

  <div class="bulk-bar fade-in">
    <span class="bulk-label">Bulk Edit</span>
    <span class="meta-text">カテゴリ・出題日を変更後にまとめて保存</span>
    <button class="btn btn-success btn-sm" onclick="bulkUpdate()">✓ Apply Changes</button>
    <span id="change-count" class="meta-text"></span>
  </div>

  <div class="fade-in" style="overflow-x:auto;">
  <table class="data-table" id="assignments-table">
    <thead>
      <tr>
        <th style="width:32px;"><input type="checkbox" id="check-all" onchange="toggleAll(this)"></th>
        <th>教科</th>
        <th>テキスト</th>
        <th>問題番号</th>
        <th title="重要度 ダブルクリックで編集">Imp ✎</th>
        <th title="難易度 ダブルクリックで編集">Dif ✎</th>
        <th title="復習価値 ダブルクリックで編集">RV ✎</th>
        <th>習熟度</th>
        <th>カテゴリ</th>
        <th>出題日</th>
        <th>削除</th>
      </tr>
    </thead>
    <tbody>
    {%- for a in assignments %}
    <tr id="row-{{ a.assignment_id }}" class="row-{{ a.category }}">
      <td><input type="checkbox" class="row-check" value="{{ a.assignment_id }}"></td>
      <td class="meta-text">{{ a.subject }}</td>
      <td class="left" style="max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:11px;">
        {{ a.textbook }}
      </td>
      <td class="left" style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:11px;">
        {{ a.problem_number }}
      </td>
      <td class="editable-cell" data-problem="{{ a.problem_id }}" data-field="importance">
        <span class="editable" ondblclick="startEdit(this)">{{ a.importance }}</span>
      </td>
      <td class="editable-cell" data-problem="{{ a.problem_id }}" data-field="difficulty">
        <span class="editable" ondblclick="startEdit(this)">{{ a.difficulty }}</span>
      </td>
      <td class="editable-cell" data-problem="{{ a.problem_id }}" data-field="review_value">
        <span class="editable" ondblclick="startEdit(this)">{{ a.review_value }}</span>
      </td>
      <td>
        {%- set m = a.mastery or 1 %}
        <span class="mastery-{{ m }}">{{ '★' * m }}</span>
      </td>
      <td>
        <select class="edit-field inline-select"
          data-id="{{ a.assignment_id }}" data-field="category"
          style="width:76px;"
          onchange="markChanged(this, {{ a.assignment_id }})">
          {%- for cat in ['予習','復習','定着','再定着'] %}
          <option value="{{ cat }}" {%- if cat == a.category %} selected{%- endif %}>{{ cat }}</option>
          {%- endfor %}
        </select>
      </td>
      <td>
        <input type="date" class="edit-field"
          data-id="{{ a.assignment_id }}" data-field="scheduled_date"
          value="{{ '' if a.scheduled_date == '2099-12-31' else a.scheduled_date }}"
          style="width:130px;"
          onchange="markChanged(this, {{ a.assignment_id }})">
      </td>
      <td>
        <button class="btn btn-danger btn-sm"
          onclick="deleteAssignment({{ a.assignment_id }}, this)">×</button>
      </td>
    </tr>
    {%- endfor %}
    </tbody>
  </table>
  </div>

<script>
const changedRows = new Map();

function markChanged(el, id) {
  const row = document.getElementById('row-' + id);
  const fields = row.querySelectorAll('.edit-field');
  const data = {};
  fields.forEach(f => { data[f.dataset.field] = f.value; });
  changedRows.set(id, data);
  row.classList.add('changed-row');
  document.getElementById('change-count').textContent =
    changedRows.size + ' row(s) pending';
}

async function bulkUpdate() {
  if (changedRows.size === 0) { alert('No changes to apply.'); return; }
  const updates = [];
  changedRows.forEach((data, id) => updates.push({ assignment_id: id, ...data }));
  const res = await fetch('/assignments/bulk_update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ student_id: '{{ selected_student }}', updates })
  });
  if (res.ok) {
    changedRows.forEach((data, id) => {
      const row = document.getElementById('row-' + id);
      if (row) { row.classList.remove('changed-row'); row.className = 'row-' + data.category; }
    });
    changedRows.clear();
    document.getElementById('change-count').textContent = '✓ Saved';
    setTimeout(() => document.getElementById('change-count').textContent = '', 3000);
  } else { alert('Error saving changes.'); }
}

function startEdit(span) {
  const cell = span.closest('.editable-cell');
  const field = cell.dataset.field;
  const problemId = cell.dataset.problem;
  const current = span.textContent.trim();
  span.classList.add('editing');

  const input = document.createElement('input');
  input.type = 'number'; input.min = 1; input.max = 5;
  input.value = current;
  input.className = 'inline-input';
  input.style.width = '52px';
  cell.appendChild(input);
  input.focus(); input.select();

  const finish = async (save) => {
    if (save && input.value !== current) {
      const res = await fetch('/problems/update_field', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ problem_id: problemId, field: field, value: input.value })
      });
      if (res.ok) { span.textContent = input.value; }
      else { alert('Update failed.'); }
    }
    input.remove();
    span.classList.remove('editing');
  };

  input.addEventListener('blur', () => finish(true));
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') finish(true);
    if (e.key === 'Escape') finish(false);
  });
}

function toggleAll(cb) {
  document.querySelectorAll('.row-check').forEach(c => c.checked = cb.checked);
}

async function deleteAssignment(id, btn) {
  if (!confirm('Delete this assignment?')) return;
  const res = await fetch('/assignments/delete/' + id, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: 'student_id={{ selected_student }}'
  });
  if (res.ok || res.redirected) { document.getElementById('row-' + id)?.remove(); }
  else { alert('Delete failed.'); }
}
</script>
</div>
</body>
</html>"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. record_list.html
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
record_list_html = """\
<!DOCTYPE html>
<html lang="ja">
<head>
""" + COMMON_HEAD + """
  <title>Edit Records — Study Planner</title>
</head>
<body>
""" + page_header("04 / Records", "Edit Records", "授業記録修正・習熟度変更", "var(--rose)") + """

  <div class="filter-bar fade-in">
    <form method="GET" style="display:contents;">
      <div>
        <label>Student</label>
        <select name="student_id" onchange="this.form.submit()" style="min-width:140px;">
          {%- for s in students %}
          <option value="{{ s.student_id }}"
            {%- if s.student_id == selected_student %} selected{%- endif %}>
            {{ s.name }}
          </option>
          {%- endfor %}
        </select>
      </div>
    </form>
    <span class="meta-text" style="margin-left:auto;">{{ records|length }} records</span>
  </div>

  <div style="font-family:'DM Mono',monospace;font-size:10px;color:var(--text-muted);
    margin-bottom:8px;letter-spacing:0.5px;">
    ※ 習熟度セルをダブルクリックで直接編集できます
  </div>

  <div class="bulk-bar fade-in">
    <span class="bulk-label">Bulk Edit</span>
    <span class="meta-text">習熟度を変更後にまとめて保存</span>
    <button class="btn btn-success btn-sm" onclick="bulkUpdateMastery()">✓ Apply Mastery</button>
    <span id="mastery-count" class="meta-text"></span>
  </div>

  <div class="fade-in" style="overflow-x:auto;">
  <table class="data-table">
    <thead>
      <tr>
        <th>Date</th><th>教科</th><th>テキスト</th><th>問題番号</th>
        <th>正誤</th><th title="ダブルクリックで編集">習熟度 ✎</th><th>カテゴリ</th>
      </tr>
    </thead>
    <tbody>
    {%- for r in records %}
    <tr id="hrow-{{ r.history_id }}">
      <td class="meta-text" style="white-space:nowrap;">{{ r.date }}</td>
      <td class="meta-text">{{ r.subject }}</td>
      <td class="left" style="font-size:11px;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
        {{ r.textbook }}
      </td>
      <td class="left" style="font-size:11px;max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
        {{ r.problem_number }}
      </td>
      <td>
        {%- if r.correct == 1 %}
        <span style="color:var(--green);font-family:'DM Mono',monospace;font-size:14px;">✓</span>
        {%- else %}
        <span style="color:var(--rose);font-family:'DM Mono',monospace;font-size:14px;">✗</span>
        {%- endif %}
      </td>
      <td class="mastery-cell" data-id="{{ r.history_id }}" data-mastery="{{ r.mastery }}">
        {%- set m = r.mastery %}
        <span class="editable mastery-{{ m }}"
          ondblclick="startMasteryEdit(this, {{ r.history_id }}, {{ m }})">
          {{ '★' * m }}
        </span>
      </td>
      <td>
        <span class="badge badge-{{ r.category or '' }}">{{ r.category or '—' }}</span>
      </td>
    </tr>
    {%- endfor %}
    </tbody>
  </table>
  </div>

<script>
const masteryChanges = new Map();
const STARS = ['', '★', '★★', '★★★'];

function startMasteryEdit(span, historyId, current) {
  const cell = span.closest('.mastery-cell');
  span.classList.add('editing');

  const sel = document.createElement('select');
  sel.className = 'inline-select';
  sel.style.width = '76px';
  [1, 2, 3].forEach(m => {
    const opt = document.createElement('option');
    opt.value = m; opt.textContent = STARS[m];
    if (m === current) opt.selected = true;
    sel.appendChild(opt);
  });
  cell.appendChild(sel);
  sel.focus();

  let finished = false;
  const finish = (save) => {
    if (finished) return; finished = true;
    const newVal = parseInt(sel.value);
    if (save && newVal !== current) {
      masteryChanges.set(historyId, newVal);
      span.textContent = STARS[newVal];
      span.className = 'editable mastery-' + newVal;
      span.ondblclick = () => startMasteryEdit(span, historyId, newVal);
      document.getElementById('hrow-' + historyId)?.classList.add('changed-row');
      document.getElementById('mastery-count').textContent =
        masteryChanges.size + ' row(s) pending';
    }
    sel.remove();
    span.classList.remove('editing');
  };

  sel.addEventListener('change', () => finish(true));
  sel.addEventListener('blur', () => setTimeout(() => finish(true), 100));
  sel.addEventListener('keydown', e => {
    if (e.key === 'Enter') finish(true);
    if (e.key === 'Escape') finish(false);
  });
}

async function bulkUpdateMastery() {
  if (masteryChanges.size === 0) { alert('No changes to apply.'); return; }
  const updates = [];
  masteryChanges.forEach((mastery, id) => updates.push({ history_id: id, mastery }));
  const res = await fetch('/mastery/bulk_update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ updates })
  });
  if (res.ok) {
    masteryChanges.forEach((_, id) => {
      document.getElementById('hrow-' + id)?.classList.remove('changed-row');
    });
    masteryChanges.clear();
    document.getElementById('mastery-count').textContent = '✓ Saved';
    setTimeout(() => document.getElementById('mastery-count').textContent = '', 3000);
  } else { alert('Error saving changes.'); }
}
</script>
</div>
</body>
</html>"""

# ━━━ ファイル書き出し ━━━
files = {
    "assignments_list.html": assignments_html,
    "record_list.html":      record_list_html,
}
for fname, content in files.items():
    path = os.path.join(templates, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ {fname} を更新しました")

print("✅ Step A 完了")