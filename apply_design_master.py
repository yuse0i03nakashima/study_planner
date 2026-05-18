import os

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")

COMMON_CSS = """\
    :root {
      --bg:#0c0d11; --surface:#13151e; --surface2:#1b1e2b; --surface3:#222536;
      --border:#252838; --border-light:#2f3347;
      --text:#dde1ec; --text-muted:#9aa3b8; --text-dim:#555d7a;
      --blue:#5b8ff9; --green:#3ecf8e; --amber:#f5a623; --rose:#f06292; --red:#ef4444;
      --blue-bg:rgba(91,143,249,0.10); --green-bg:rgba(62,207,142,0.10);
      --amber-bg:rgba(245,166,35,0.10); --rose-bg:rgba(240,98,146,0.10);
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
      letter-spacing:2px; text-transform:uppercase; }
    .page-title-ja { font-family:'Noto Serif JP',serif; font-weight:300; font-size:11px;
      color:var(--text-muted); margin-top:4px; }
    .page-header-back { font-family:'DM Mono',monospace; font-size:10px; color:var(--text-muted);
      letter-spacing:1.5px; text-decoration:none; transition:color 0.15s; }
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
      font-family:'Noto Serif JP',serif; font-size:13px; outline:none; transition:border-color 0.15s; }
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
    .btn-danger:hover  { background:#f87171; }
    .btn-ghost { background:transparent; color:var(--text-muted); border:1px solid var(--border-light); }
    .btn-ghost:hover { border-color:var(--text-muted); color:var(--text); }
    .btn-sm { padding:5px 14px; font-size:10px; }
    .data-table { width:100%; border-collapse:collapse; background:var(--surface); font-size:12px; }
    .data-table th { background:var(--surface2); color:var(--text-muted); font-family:'DM Mono',monospace;
      font-size:9px; letter-spacing:1.5px; text-transform:uppercase; padding:10px 12px;
      text-align:center; border-bottom:1px solid var(--border-light); white-space:nowrap; }
    .data-table td { padding:9px 12px; border-bottom:1px solid var(--border);
      text-align:center; vertical-align:middle; }
    .data-table tr:hover td { background:var(--surface2); }
    .data-table td.left { text-align:left; font-family:'Noto Serif JP',serif; }
    .grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
    .grid-3 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; }
    .grid-4 { display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:16px; }
    .meta-text { font-family:'DM Mono',monospace; font-size:10px; color:var(--text-dim); letter-spacing:1px; }
    input[type="checkbox"] { accent-color:var(--blue); width:14px; height:14px; }
    .badge { font-family:'DM Mono',monospace; font-size:9px; letter-spacing:1px; padding:2px 8px; display:inline-block; }
    .hint { font-family:'DM Mono',monospace; font-size:9px; color:var(--text-dim); margin-top:5px; letter-spacing:0.5px; }
    .fade-in { animation:fadeIn 0.3s ease both; }
    @keyframes fadeIn { from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);} }
    a { color:var(--blue); text-decoration:none; }
    a:hover { text-decoration:underline; }
    .alert { font-family:'DM Mono',monospace; font-size:11px; letter-spacing:1px;
      padding:10px 16px; margin-bottom:16px; border-left:2px solid; }
    .alert-success { background:var(--green-bg); color:var(--green); border-color:var(--green); }
    .alert-error   { background:rgba(239,68,68,0.08); color:#f87171; border-color:var(--red); }
    #toast { position:fixed; bottom:32px; left:50%; transform:translateX(-50%) translateY(20px);
      background:var(--surface2); border:1px solid var(--border-light); color:var(--text);
      font-family:'DM Mono',monospace; font-size:11px; letter-spacing:1px;
      padding:12px 24px; opacity:0; transition:all 0.3s ease; pointer-events:none; z-index:9999; }
    #toast.show { opacity:1; transform:translateX(-50%) translateY(0); }
    #toast.success { border-left:2px solid var(--green); color:var(--green); }
    #toast.info    { border-left:2px solid var(--blue);  color:var(--blue); }
    #toast.warn    { border-left:2px solid var(--amber); color:var(--amber); }"""

COMMON_FONTS = '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@300;400;500;600&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">'

TOAST_JS = """\
<div id="toast"></div>
<script>
function showToast(msg, type='success') {
  const t = document.getElementById('toast');
  t.textContent = msg; t.className = 'show ' + type;
  setTimeout(() => { t.className = ''; }, 3000);
}
</script>"""

def page_header(num, en, ja, color="var(--blue)"):
    return (
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
# 1. textbooks.html
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
textbooks_html = """\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  """ + COMMON_FONTS + """
  <title>Textbooks — Study Planner</title>
  <style>
""" + COMMON_CSS + """
  </style>
</head>
<body>
<div class="container">
""" + page_header("01 / Master Data", "Textbooks", "テキスト・シリーズ・セクション管理") + """

  <!-- シリーズ登録 -->
  <div class="card fade-in">
    <div class="card-title">Add Series</div>
    <form method="POST" action="/textbooks/series/add" style="display:flex;gap:16px;align-items:flex-end;">
      <div style="flex:1;">
        <label>Series Name</label>
        <input type="text" name="name" placeholder="例：青チャート" required>
      </div>
      <button type="submit" class="btn btn-primary" style="margin-top:0;">Add →</button>
    </form>
  </div>

  <!-- テキスト登録 -->
  <div class="card fade-in">
    <div class="card-title">Add Textbook</div>
    <form method="POST" action="/textbooks/add">
      <div class="grid-3">
        <div>
          <label>Series</label>
          <select name="series_id">
            <option value="">— なし —</option>
            {% for s in series_list %}
            <option value="{{ s.series_id }}">{{ s.name }}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label>Subject</label>
          <select name="subject">
            {% for subj in all_subjects %}
            <option value="{{ subj }}">{{ subj }}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label>Textbook Name</label>
          <input type="text" name="name" placeholder="例：数I+A" required>
        </div>
      </div>
      <div style="margin-top:16px;">
        <button type="submit" class="btn btn-primary">Add →</button>
      </div>
    </form>
  </div>

  <!-- テキスト一覧 -->
  <div class="card fade-in">
    <div class="card-title">Textbook List</div>
    <div style="overflow-x:auto;">
    <table class="data-table">
      <thead>
        <tr>
          <th>ID</th><th>Series</th><th>Textbook</th><th>Subject</th>
          <th>Problems</th><th>Students</th><th>Sections</th><th></th>
        </tr>
      </thead>
      <tbody>
      {% for t in textbooks %}
      <tr>
        <td class="meta-text">{{ t.textbook_id }}</td>
        <td class="meta-text">{{ t.series_name or '—' }}</td>
        <td class="left">{{ t.name }}</td>
        <td class="meta-text">{{ t.subject }}</td>
        <td class="meta-text">{{ t.problem_count }}</td>
        <td class="meta-text" style="font-size:11px;">{{ t.students or '—' }}</td>
        <td>
          <a href="/textbooks/{{ t.textbook_id }}/sections"
            class="btn btn-ghost btn-sm">Sections</a>
        </td>
        <td>
          <form method="POST" action="/textbooks/delete/{{ t.textbook_id }}"
            style="display:inline;"
            onsubmit="return confirm('Delete this textbook?')">
            <button class="btn btn-danger btn-sm">×</button>
          </form>
        </td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
    </div>
  </div>

  <!-- シリーズ一覧 -->
  <div class="card fade-in">
    <div class="card-title">Series List</div>
    <div style="overflow-x:auto;">
    <table class="data-table">
      <thead>
        <tr><th>ID</th><th>Series Name</th><th>Textbooks</th><th></th></tr>
      </thead>
      <tbody>
      {% for s in series_list %}
      <tr>
        <td class="meta-text">{{ s.series_id }}</td>
        <td class="left">{{ s.name }}</td>
        <td class="meta-text">{{ s.textbook_count }}</td>
        <td>
          <form method="POST" action="/textbooks/series/delete/{{ s.series_id }}"
            style="display:inline;"
            onsubmit="return confirm('Delete this series?')">
            <button class="btn btn-danger btn-sm">×</button>
          </form>
        </td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
    </div>
  </div>

</div>
</body>
</html>"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. sections.html
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
sections_html = """\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  """ + COMMON_FONTS + """
  <title>Sections — Study Planner</title>
  <style>
""" + COMMON_CSS + """
  </style>
</head>
<body>
<div class="container">
""" + page_header("01 / Master Data", "Sections", "セクション管理") + """

  <div class="meta-text fade-in" style="margin-bottom:20px;">
    {{ textbook.series_name or '—' }} &rsaquo; {{ textbook.name }}
    <span style="margin-left:12px;color:var(--text-muted);">{{ textbook.subject }}</span>
  </div>

  <div class="card fade-in">
    <div class="card-title">Add Section</div>
    <form method="POST" style="display:flex;gap:16px;align-items:flex-end;">
      <div style="flex:1;">
        <label>Section Name</label>
        <input type="text" name="name" placeholder="例：第1章 展開と因数分解" required>
      </div>
      <div style="width:120px;">
        <label>Order</label>
        <input type="number" name="order_index" value="0" min="0">
      </div>
      <button type="submit" class="btn btn-primary" style="margin-top:0;">Add →</button>
    </form>
  </div>

  <div class="card fade-in">
    <div class="card-title">Section List</div>
    <table class="data-table">
      <thead>
        <tr><th>Order</th><th>Section Name</th><th>Problems</th><th></th></tr>
      </thead>
      <tbody>
      {% for s in sections %}
      <tr>
        <td class="meta-text">{{ s.order_index }}</td>
        <td class="left">{{ s.name }}</td>
        <td class="meta-text">{{ s.problem_count }}</td>
        <td>
          <form method="POST" action="/textbooks/sections/delete/{{ s.section_id }}"
            style="display:inline;"
            onsubmit="return confirm('Delete this section?')">
            <button class="btn btn-danger btn-sm">×</button>
          </form>
        </td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>

  <a href="/textbooks" class="btn btn-ghost">← Back to Textbooks</a>

</div>
</body>
</html>"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. problems_list.html（Problem List）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
problems_list_html = """\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  """ + COMMON_FONTS + """
  <title>Problem List — Study Planner</title>
  <style>
""" + COMMON_CSS + """
    .editable { cursor:pointer; padding:2px 6px; border-radius:2px;
      border:1px dashed transparent; transition:border-color 0.12s, background 0.12s; }
    .editable:hover { border-color:var(--border-light); background:var(--surface3); }
    .editable.editing { display:none; }
    .inline-input { background:var(--surface2); border:1px solid var(--blue);
      color:var(--text); padding:3px 6px; font-size:12px; outline:none; }
    .inline-textarea { background:var(--surface2); border:1px solid var(--blue);
      color:var(--text); padding:4px 8px; font-size:11px; outline:none;
      width:200px; min-height:48px; resize:both; }
  </style>
</head>
<body>
<div class="container">
""" + page_header("01 / Master Data", "Problem List", "問題一覧・編集・削除") + """

  <!-- フィルター -->
  <div class="card fade-in" style="padding:16px 20px;">
    <form method="GET" style="display:flex;gap:16px;align-items:flex-end;flex-wrap:wrap;">
      <div>
        <label>Subject</label>
        <select name="subject" style="width:120px;">
          <option value="">全教科</option>
          {% for subj in all_subjects %}
          <option value="{{ subj }}" {% if subj == selected_subject %}selected{% endif %}>{{ subj }}</option>
          {% endfor %}
        </select>
      </div>
      <div>
        <label>Textbook</label>
        <select name="textbook_id" style="width:180px;">
          <option value="">全テキスト</option>
          {% for t in all_textbooks %}
          <option value="{{ t.textbook_id }}"
            {% if t.textbook_id|string == selected_textbook %}selected{% endif %}>
            {{ t.name }}
          </option>
          {% endfor %}
        </select>
      </div>
      <button type="submit" class="btn btn-ghost btn-sm" style="margin-bottom:0;">Filter</button>
      <span class="meta-text" style="margin-left:auto;align-self:center;">{{ problems|length }} problems</span>
    </form>
  </div>

  <div class="meta-text fade-in" style="margin-bottom:8px;">
    ※ Imp・Dif・RV・所要時間・学習指示はセルをダブルクリックで編集できます
  </div>

  <div class="fade-in" style="overflow-x:auto;">
  <table class="data-table" id="problem-table">
    <thead>
      <tr>
        <th>ID</th><th>教科</th><th>テキスト</th><th>問題番号</th>
        <th>Imp</th><th>Dif</th><th>RV</th><th>分</th>
        <th>学習指示</th><th></th>
      </tr>
    </thead>
    <tbody>
    {% for p in problems %}
    <tr id="prow-{{ p.problem_id }}">
      <td class="meta-text">{{ p.problem_id }}</td>
      <td class="meta-text">{{ p.subject }}</td>
      <td class="left" style="max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:11px;">
        {{ p.textbook }}
      </td>
      <td class="left" style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:11px;">
        {{ p.problem_number }}
      </td>
      <td class="editable-cell" data-problem="{{ p.problem_id }}" data-field="importance">
        <span class="editable" ondblclick="startNumEdit(this)">{{ p.importance }}</span>
      </td>
      <td class="editable-cell" data-problem="{{ p.problem_id }}" data-field="difficulty">
        <span class="editable" ondblclick="startNumEdit(this)">{{ p.difficulty }}</span>
      </td>
      <td class="editable-cell" data-problem="{{ p.problem_id }}" data-field="review_value">
        <span class="editable" ondblclick="startNumEdit(this)">{{ p.review_value }}</span>
      </td>
      <td class="editable-cell" data-problem="{{ p.problem_id }}" data-field="estimated_minutes">
        <span class="editable" ondblclick="startNumEdit(this, 5, 120, 5)">{{ p.estimated_minutes }}</span>
      </td>
      <td class="editable-cell left" data-problem="{{ p.problem_id }}" data-field="instruction"
        style="max-width:180px;">
        <span class="editable" ondblclick="startTextEdit(this)"
          style="font-size:11px;display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:180px;">
          {{ p.instruction or '—' }}
        </span>
      </td>
      <td>
        <button class="btn btn-danger btn-sm"
          onclick="deleteProblem({{ p.problem_id }}, this)">×</button>
      </td>
    </tr>
    {% endfor %}
    </tbody>
  </table>
  </div>

  <div style="margin-top:16px;">
    <a href="/problems" class="btn btn-primary">+ Add Problem</a>
  </div>

""" + TOAST_JS + """
</div>

<script>
function showToast(msg, type='success') {
  const t = document.getElementById('toast');
  t.textContent = msg; t.className = 'show ' + type;
  setTimeout(() => { t.className = ''; }, 3000);
}

function startNumEdit(span, min=1, max=5, step=1) {
  const cell = span.closest('.editable-cell');
  const field = cell.dataset.field;
  const problemId = cell.dataset.problem;
  const current = span.textContent.trim();
  span.classList.add('editing');
  const input = document.createElement('input');
  input.type = 'number'; input.min = min; input.max = max; input.step = step;
  input.value = current; input.className = 'inline-input';
  input.style.width = field === 'estimated_minutes' ? '64px' : '52px';
  cell.appendChild(input);
  input.focus(); input.select();
  let done = false;
  const finish = async (save) => {
    if (done) return; done = true;
    if (save && input.value !== current) {
      const res = await fetch('/problems/update_field', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ problem_id: problemId, field: field, value: input.value })
      });
      if (res.ok) { span.textContent = input.value; showToast('✓ Updated', 'success'); }
      else { showToast('Update failed.', 'warn'); }
    }
    input.remove(); span.classList.remove('editing');
  };
  input.addEventListener('blur', () => finish(true));
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') finish(true);
    if (e.key === 'Escape') finish(false);
  });
}

function startTextEdit(span) {
  const cell = span.closest('.editable-cell');
  const problemId = cell.dataset.problem;
  const current = span.textContent.trim() === '—' ? '' : span.textContent.trim();
  span.classList.add('editing');
  const ta = document.createElement('textarea');
  ta.value = current; ta.className = 'inline-textarea';
  cell.appendChild(ta);
  ta.focus();
  let done = false;
  const finish = async (save) => {
    if (done) return; done = true;
    if (save && ta.value !== current) {
      const res = await fetch('/problems/update_instruction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ problem_id: problemId, instruction: ta.value })
      });
      if (res.ok) {
        span.textContent = ta.value || '—';
        showToast('✓ Updated', 'success');
      } else { showToast('Update failed.', 'warn'); }
    }
    ta.remove(); span.classList.remove('editing');
  };
  ta.addEventListener('blur', () => finish(true));
  ta.addEventListener('keydown', e => {
    if (e.key === 'Escape') finish(false);
  });
}

async function deleteProblem(id, btn) {
  if (!confirm('Delete problem ' + id + '?')) return;
  const res = await fetch('/problems/delete/' + id, { method: 'POST' });
  if (res.ok) {
    document.getElementById('prow-' + id)?.remove();
    showToast('Deleted.', 'success');
  } else { showToast('Delete failed.', 'warn'); }
}
</script>
</body>
</html>"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. students.html
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
students_html = """\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  """ + COMMON_FONTS + """
  <title>Students — Study Planner</title>
  <style>
""" + COMMON_CSS + """
  </style>
</head>
<body>
<div class="container">
""" + page_header("01 / Master Data", "Students", "生徒情報・教科・計画モード") + """

  {% with messages = get_flashed_messages(with_categories=true) %}
  {% for cat, msg in messages %}
  <div class="alert alert-{{ 'success' if cat == 'success' else 'error' }} fade-in">{{ msg }}</div>
  {% endfor %}
  {% endwith %}

  <div class="card fade-in">
    <div class="card-title">Add Student</div>
    <form method="POST" action="/students/add">
      <div class="grid-3">
        <div>
          <label>Student ID</label>
          <input type="text" name="student_id" placeholder="例：S005" required>
        </div>
        <div>
          <label>Name</label>
          <input type="text" name="name" placeholder="例：山田太郎" required>
        </div>
        <div>
          <label>Subjects</label>
          <input type="text" name="subjects" placeholder="例：数学,英語">
        </div>
      </div>
      <div class="grid-2" style="margin-top:0;">
        <div>
          <label>Plan Mode</label>
          <select name="plan_mode">
            <option value="all">all（全教科一括）</option>
            <option value="per_subject">per_subject（教科別）</option>
          </select>
        </div>
      </div>
      <div style="margin-top:16px;">
        <button type="submit" class="btn btn-primary">Add →</button>
      </div>
    </form>
  </div>

  <div class="card fade-in">
    <div class="card-title">Student List</div>
    <table class="data-table">
      <thead>
        <tr>
          <th>ID</th><th>Name</th><th>Subjects</th>
          <th>Plan Mode</th><th>Textbooks</th><th></th>
        </tr>
      </thead>
      <tbody>
      {% for s in students %}
      <tr>
        <td class="meta-text">{{ s.student_id }}</td>
        <td class="left">{{ s.name }}</td>
        <td class="meta-text" style="font-size:11px;">{{ s.subjects }}</td>
        <td>
          <span class="badge" style="
            {% if s.plan_mode == 'all' %}
              background:var(--blue-bg);color:var(--blue);border:1px solid rgba(91,143,249,0.3);
            {% else %}
              background:var(--amber-bg);color:var(--amber);border:1px solid rgba(245,166,35,0.3);
            {% endif %}">
            {{ s.plan_mode }}
          </span>
        </td>
        <td class="meta-text" style="font-size:11px;">{{ s.textbooks or '—' }}</td>
        <td>
          <a href="/students/edit/{{ s.student_id }}"
            class="btn btn-ghost btn-sm">Edit</a>
        </td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>

</div>
</body>
</html>"""

# ━━━ ファイル書き出し ━━━
files = {
    "textbooks.html":      textbooks_html,
    "sections.html":       sections_html,
    "problems_list.html":  problems_list_html,
    "students.html":       students_html,
}
for fname, content in files.items():
    path = os.path.join(templates, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ {fname} を更新しました")

# ━━━ app.pyに不足エンドポイントを追加 ━━━
app_path = os.path.join(base, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    app = f.read()

# instruction更新エンドポイント
instruction_route = '''
@app.route("/problems/update_instruction", methods=["POST"])
def problem_update_instruction():
    data = request.get_json()
    problem_id = data.get("problem_id")
    instruction = data.get("instruction", "")
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE problems SET instruction=? WHERE problem_id=?",
              (instruction, problem_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

'''

# problems_listルートにフィルター対応を追加
old_problems_list = '''@app.route("/problems/list")
def problems_list():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT p.*, t.name as textbook_display
        FROM problems p
        LEFT JOIN textbooks t ON p.textbook_id = t.textbook_id
        ORDER BY p.subject, p.textbook, p.problem_id
    """)
    problems = c.fetchall()
    conn.close()
    return render_template("problems_list.html", problems=problems)'''

new_problems_list = '''@app.route("/problems/list")
def problems_list():
    conn = get_connection()
    c = conn.cursor()
    subject = request.args.get("subject", "")
    textbook_id = request.args.get("textbook_id", "")
    query = """
        SELECT p.*, t.name as textbook_display
        FROM problems p
        LEFT JOIN textbooks t ON p.textbook_id = t.textbook_id
        WHERE 1=1
    """
    params = []
    if subject:
        query += " AND p.subject=?"
        params.append(subject)
    if textbook_id:
        query += " AND p.textbook_id=?"
        params.append(textbook_id)
    query += " ORDER BY p.subject, p.textbook, p.problem_id"
    c.execute(query, params)
    problems = c.fetchall()
    # フィルター用データ
    c.execute("SELECT DISTINCT subject FROM problems ORDER BY subject")
    all_subjects = [r["subject"] for r in c.fetchall()]
    c.execute("SELECT textbook_id, name FROM textbooks ORDER BY subject, name")
    all_textbooks = c.fetchall()
    conn.close()
    return render_template("problems_list.html", problems=problems,
                           all_subjects=all_subjects, all_textbooks=all_textbooks,
                           selected_subject=subject, selected_textbook=textbook_id)'''

changed = False
if "/problems/update_instruction" not in app:
    idx = app.rfind("if __name__")
    app = app[:idx] + instruction_route + app[idx:]
    print("✅ /problems/update_instructionを追加しました")
    changed = True

if old_problems_list in app:
    app = app.replace(old_problems_list, new_problems_list)
    print("✅ problems_listルートにフィルター対応を追加しました")
    changed = True
elif "def problems_list" in app:
    print("ℹ️  problems_listルートはすでに更新済みです")
else:
    print("❌ problems_listルートが見つかりません")

if changed:
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app)

print("\n✅ マスタ管理ページのデザイン統一完了")