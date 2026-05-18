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
    .container { max-width:1000px; margin:0 auto; position:relative; z-index:1; }
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
    .card { background:var(--surface); border:1px solid var(--border);
      padding:24px 28px; margin-bottom:20px; }
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
      transition:border-color 0.15s; }
    input:focus, select:focus, textarea:focus { border-color:var(--blue); }
    select option { background:var(--surface2); }
    .btn { font-family:'DM Mono',monospace; font-size:11px; letter-spacing:2px;
      text-transform:uppercase; padding:10px 24px; border:none; cursor:pointer;
      transition:all 0.15s; display:inline-flex; align-items:center; gap:8px; }
    .btn-primary { background:var(--blue); color:#0c0d11; }
    .btn-primary:hover { background:#7aaafb; }
    .btn-danger  { background:var(--red); color:white; }
    .btn-danger:hover  { background:#f87171; }
    .btn-ghost { background:transparent; color:var(--text-muted);
      border:1px solid var(--border-light); }
    .btn-ghost:hover { border-color:var(--text-muted); color:var(--text); }
    .btn-sm { padding:5px 14px; font-size:10px; }
    .btn-warn { background:var(--amber-bg); color:var(--amber);
      border:1px solid rgba(245,166,35,0.3); }
    .btn-warn:hover { background:rgba(245,166,35,0.2); }
    .data-table { width:100%; border-collapse:collapse; background:var(--surface); font-size:12px; }
    .data-table th { background:var(--surface2); color:var(--text-muted);
      font-family:'DM Mono',monospace; font-size:9px; letter-spacing:1.5px;
      text-transform:uppercase; padding:10px 12px; text-align:center;
      border-bottom:1px solid var(--border-light); white-space:nowrap; }
    .data-table td { padding:9px 12px; border-bottom:1px solid var(--border);
      text-align:center; vertical-align:middle; }
    .data-table tr:hover td { background:var(--surface2); }
    .data-table td.left { text-align:left; font-family:'Noto Serif JP',serif; }
    .grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
    .grid-3 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; }
    .grid-4 { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }
    .grid-7 { display:grid; grid-template-columns:repeat(7,1fr); gap:10px; }
    .meta-text { font-family:'DM Mono',monospace; font-size:10px;
      color:var(--text-dim); letter-spacing:1px; }
    .hint { font-family:'DM Mono',monospace; font-size:9px; color:var(--text-dim);
      margin-top:5px; letter-spacing:0.5px; }
    .alert { font-family:'DM Mono',monospace; font-size:11px; letter-spacing:1px;
      padding:10px 16px; margin-bottom:16px; border-left:2px solid; }
    .alert-success { background:var(--green-bg); color:var(--green); border-color:var(--green); }
    .alert-error   { background:rgba(239,68,68,0.08); color:#f87171; border-color:var(--red); }
    .fade-in { animation:fadeIn 0.3s ease both; }
    @keyframes fadeIn { from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);} }
    a { color:var(--blue); text-decoration:none; }
    input[type="checkbox"] { accent-color:var(--blue); width:14px; height:14px; }
    /* 曜日チェックボックス */
    .dow-grid { display:grid; grid-template-columns:repeat(7,1fr); gap:8px; margin-top:8px; }
    .dow-btn { display:flex; flex-direction:column; align-items:center; padding:10px 6px;
      background:var(--surface2); border:1px solid var(--border-light); cursor:pointer;
      transition:all 0.15s; user-select:none; }
    .dow-btn:has(input:checked) { background:var(--blue-bg); border-color:rgba(91,143,249,0.4); }
    .dow-btn span { font-family:'DM Mono',monospace; font-size:11px; color:var(--text-muted);
      margin-top:4px; }
    .dow-btn:has(input:checked) span { color:var(--blue); }
    .dow-btn input { accent-color:var(--blue); }
    /* 時間入力グリッド */
    .time-grid { display:grid; grid-template-columns:repeat(7,1fr); gap:8px; margin-top:8px; }
    .time-cell { display:flex; flex-direction:column; align-items:center; gap:6px; }
    .time-cell .day-label { font-family:'DM Mono',monospace; font-size:10px;
      color:var(--text-muted); letter-spacing:1px; }
    .time-cell input { text-align:center; padding:8px 4px; }
    #toast { position:fixed; bottom:32px; left:50%; transform:translateX(-50%) translateY(20px);
      background:var(--surface2); border:1px solid var(--border-light); color:var(--text);
      font-family:'DM Mono',monospace; font-size:11px; letter-spacing:1px;
      padding:12px 24px; opacity:0; transition:all 0.3s ease; pointer-events:none; z-index:9999; }
    #toast.show { opacity:1; transform:translateX(-50%) translateY(0); }
    #toast.success { border-left:2px solid var(--green); color:var(--green); }
    #toast.info    { border-left:2px solid var(--blue);  color:var(--blue); }
    #toast.warn    { border-left:2px solid var(--amber); color:var(--amber); }"""

FONTS = '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@300;400;500;600&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">'

TOAST_JS = """\
<div id="toast"></div>
<script>
function showToast(msg, type='success') {
  const t = document.getElementById('toast');
  t.textContent = msg; t.className = 'show ' + type;
  setTimeout(() => { t.className = ''; }, 3000);
}
</script>"""

def ph(num, en, ja, color="var(--green)"):
    return (
        '  <div class="page-header fade-in">\n'
        '    <div>\n'
        f'      <div class="page-label">{num}</div>\n'
        f'      <div class="page-title" style="color:{color};">{en}</div>\n'
        f'      <div class="page-title-ja">{ja}</div>\n'
        '    </div>\n'
        '    <a class="page-header-back" href="/">TOP</a>\n'
        '  </div>'
    )

DAYS_JA = ["月", "火", "水", "木", "金", "土", "日"]
DAYS_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAYS_VAL = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. class_schedule.html（授業スケジュール）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class_schedule_html = """\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  """ + FONTS + """
  <title>Class Schedule — Study Planner</title>
  <style>
""" + COMMON_CSS + """
  </style>
</head>
<body>
<div class="container">
""" + ph("02 / Schedule", "Class Schedule", "授業スケジュール管理") + """

  {% with messages = get_flashed_messages(with_categories=true) %}
  {% for cat, msg in messages %}
  <div class="alert alert-{{ 'success' if cat == 'success' else 'error' }} fade-in">{{ msg }}</div>
  {% endfor %}
  {% endwith %}

  {% for student in students %}
  <div class="card fade-in">
    <div class="card-title">{{ student.name }} — {{ student.student_id }}</div>

    {% for subject in student.subjects.split(',') %}
    {% set subj = subject.strip() %}
    <div style="margin-bottom:24px;padding-bottom:24px;border-bottom:1px solid var(--border);">
      <div style="font-family:'DM Mono',monospace;font-size:11px;letter-spacing:2px;
        text-transform:uppercase;color:var(--text-muted);margin-bottom:14px;">
        {{ subj }}
      </div>

      <!-- 曜日設定 -->
      <form method="POST" action="/class_schedule/set">
        <input type="hidden" name="student_id" value="{{ student.student_id }}">
        <input type="hidden" name="subject" value="{{ subj }}">
        <label>Class Days</label>
        <div class="dow-grid">
          {% for i in range(7) %}
          {% set dv = ['mon','tue','wed','thu','fri','sat','sun'][i] %}
          {% set de = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][i] %}
          {% set dj = ['月','火','水','木','金','土','日'][i] %}
          <label class="dow-btn" style="margin:0;">
            <input type="checkbox" name="dows" value="{{ dv }}"
              {% if schedule_map.get(student.student_id, {}).get(subj, {}).get(dv) %}checked{% endif %}>
            <span>{{ de }}<br><span style="font-size:10px;color:var(--text-dim);">{{ dj }}</span></span>
          </label>
          {% endfor %}
        </div>
        <div style="margin-top:14px;">
          <button type="submit" class="btn btn-primary btn-sm">Save Days →</button>
        </div>
      </form>

      <!-- 次回授業日 -->
      <form method="POST" action="/class_schedule/next" style="margin-top:16px;">
        <input type="hidden" name="student_id" value="{{ student.student_id }}">
        <input type="hidden" name="subject" value="{{ subj }}">
        <label>Next Class Date</label>
        <div style="display:flex;gap:12px;align-items:flex-end;">
          <div style="flex:1;">
            <input type="date" name="next_class_date"
              value="{{ next_class_map.get(student.student_id, {}).get(subj, '') }}">
          </div>
          <button type="submit" class="btn btn-primary btn-sm" style="white-space:nowrap;">
            Set →
          </button>
        </div>
        <p class="hint">空欄で保存すると次回授業日をリセットします</p>
      </form>
    </div>
    {% endfor %}
  </div>
  {% endfor %}

</div>
</body>
</html>"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. schedule.html（勉強時間・全体）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
schedule_html = """\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  """ + FONTS + """
  <title>Study Hours — Study Planner</title>
  <style>
""" + COMMON_CSS + """
  </style>
</head>
<body>
<div class="container">
""" + ph("02 / Schedule", "Study Hours", "勉強時間登録（全体）") + """

  {% with messages = get_flashed_messages(with_categories=true) %}
  {% for cat, msg in messages %}
  <div class="alert alert-{{ 'success' if cat == 'success' else 'error' }} fade-in">{{ msg }}</div>
  {% endfor %}
  {% endwith %}

  <!-- 生徒選択 -->
  <div class="card fade-in" style="padding:16px 20px;">
    <form method="GET" style="display:flex;gap:16px;align-items:flex-end;">
      <div>
        <label>Student</label>
        <select name="student_id" onchange="this.form.submit()" style="min-width:160px;">
          {% for s in students %}
          <option value="{{ s.student_id }}"
            {% if s.student_id == selected_student %}selected{% endif %}>
            {{ s.name }}
          </option>
          {% endfor %}
        </select>
      </div>
    </form>
  </div>

  <!-- ベーススケジュール（曜日別） -->
  <div class="card fade-in">
    <div class="card-title">Base Schedule — 曜日別デフォルト（分）</div>
    <form method="POST" action="/schedule/base">
      <input type="hidden" name="student_id" value="{{ selected_student }}">
      <div class="time-grid">
        {% set days_en = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'] %}
        {% set days_val = ['mon','tue','wed','thu','fri','sat','sun'] %}
        {% for i in range(7) %}
        <div class="time-cell">
          <span class="day-label">{{ days_en[i] }}</span>
          <input type="number" name="{{ days_val[i] }}" min="0" max="600" step="5"
            value="{{ base_schedule.get(days_val[i], 0) }}"
            style="width:100%;">
        </div>
        {% endfor %}
      </div>
      <div style="margin-top:16px;">
        <button type="submit" class="btn btn-primary btn-sm">Save Base →</button>
      </div>
    </form>
  </div>

  <!-- オーバーライド（日付別） -->
  <div class="card fade-in">
    <div class="card-title">Date Override — 特定日の上書き</div>
    <form method="POST" action="/schedule/override">
      <input type="hidden" name="student_id" value="{{ selected_student }}">
      <div class="grid-3">
        <div>
          <label>Date</label>
          <input type="date" name="override_date">
        </div>
        <div>
          <label>Minutes</label>
          <input type="number" name="override_minutes" min="0" max="600" step="5" value="0">
        </div>
        <div style="display:flex;align-items:flex-end;">
          <button type="submit" class="btn btn-primary btn-sm" style="width:100%;">Add →</button>
        </div>
      </div>
    </form>

    {% if overrides %}
    <div style="margin-top:16px;overflow-x:auto;">
    <table class="data-table">
      <thead>
        <tr><th>Date</th><th>Minutes</th><th></th></tr>
      </thead>
      <tbody>
      {% for ov in overrides %}
      <tr>
        <td class="meta-text">{{ ov.date }}</td>
        <td class="meta-text">{{ ov.minutes }} min</td>
        <td>
          <form method="POST" action="/schedule/override/delete" style="display:inline;">
            <input type="hidden" name="student_id" value="{{ selected_student }}">
            <input type="hidden" name="override_date" value="{{ ov.date }}">
            <button class="btn btn-danger btn-sm">×</button>
          </form>
        </td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
    </div>
    {% endif %}
  </div>

</div>
</body>
</html>"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. schedule_subject.html（教科別勉強時間）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
schedule_subject_html = """\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  """ + FONTS + """
  <title>Hours per Subject — Study Planner</title>
  <style>
""" + COMMON_CSS + """
  </style>
</head>
<body>
<div class="container">
""" + ph("02 / Schedule", "Hours per Subject", "勉強時間登録（教科別）") + """

  {% with messages = get_flashed_messages(with_categories=true) %}
  {% for cat, msg in messages %}
  <div class="alert alert-{{ 'success' if cat == 'success' else 'error' }} fade-in">{{ msg }}</div>
  {% endfor %}
  {% endwith %}

  <!-- 生徒選択 -->
  <div class="card fade-in" style="padding:16px 20px;">
    <form method="GET" style="display:flex;gap:16px;align-items:flex-end;">
      <div>
        <label>Student</label>
        <select name="student_id" onchange="this.form.submit()" style="min-width:160px;">
          {% for s in students %}
          <option value="{{ s.student_id }}"
            {% if s.student_id == selected_student %}selected{% endif %}>
            {{ s.name }}
          </option>
          {% endfor %}
        </select>
      </div>
    </form>
  </div>

  {% for subject in subjects %}
  <div class="card fade-in">
    <div class="card-title">{{ subject }} — 教科別スケジュール</div>

    <!-- ベース -->
    <form method="POST" action="/schedule_subject/base">
      <input type="hidden" name="student_id" value="{{ selected_student }}">
      <input type="hidden" name="subject" value="{{ subject }}">
      <label>Base Schedule — 曜日別（分）</label>
      <div class="time-grid">
        {% set days_en = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'] %}
        {% set days_val = ['mon','tue','wed','thu','fri','sat','sun'] %}
        {% for i in range(7) %}
        <div class="time-cell">
          <span class="day-label">{{ days_en[i] }}</span>
          <input type="number" name="{{ days_val[i] }}" min="0" max="600" step="5"
            value="{{ subject_base.get(selected_student, {}).get(subject, {}).get(days_val[i], 0) }}"
            style="width:100%;">
        </div>
        {% endfor %}
      </div>
      <div style="margin-top:14px;">
        <button type="submit" class="btn btn-primary btn-sm">Save Base →</button>
      </div>
    </form>

    <!-- オーバーライド -->
    <form method="POST" action="/schedule_subject/override" style="margin-top:20px;">
      <input type="hidden" name="student_id" value="{{ selected_student }}">
      <input type="hidden" name="subject" value="{{ subject }}">
      <label>Date Override — 特定日の上書き</label>
      <div class="grid-3">
        <div>
          <label style="margin-top:0;">Date</label>
          <input type="date" name="override_date">
        </div>
        <div>
          <label style="margin-top:0;">Minutes</label>
          <input type="number" name="override_minutes" min="0" max="600" step="5" value="0">
        </div>
        <div style="display:flex;align-items:flex-end;">
          <button type="submit" class="btn btn-primary btn-sm" style="width:100%;">Add →</button>
        </div>
      </div>
    </form>

    {% set ovs = subject_overrides.get(selected_student, {}).get(subject, []) %}
    {% if ovs %}
    <div style="margin-top:14px;overflow-x:auto;">
    <table class="data-table">
      <thead><tr><th>Date</th><th>Minutes</th><th></th></tr></thead>
      <tbody>
      {% for ov in ovs %}
      <tr>
        <td class="meta-text">{{ ov.date }}</td>
        <td class="meta-text">{{ ov.minutes }} min</td>
        <td>
          <form method="POST" action="/schedule_subject/override/delete" style="display:inline;">
            <input type="hidden" name="student_id" value="{{ selected_student }}">
            <input type="hidden" name="subject" value="{{ subject }}">
            <input type="hidden" name="override_date" value="{{ ov.date }}">
            <button class="btn btn-danger btn-sm">×</button>
          </form>
        </td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
    </div>
    {% endif %}
  </div>
  {% endfor %}

</div>
</body>
</html>"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. history.html（過去の計画表）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
history_html = """\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  """ + FONTS + """
  <title>History — Study Planner</title>
  <style>
""" + COMMON_CSS + """
    .file-row { display:flex; align-items:center; gap:12px;
      padding:12px 16px; border-bottom:1px solid var(--border);
      transition:background 0.12s; }
    .file-row:last-child { border-bottom:none; }
    .file-row:hover { background:var(--surface2); }
    .file-icon { font-family:'DM Mono',monospace; font-size:10px; letter-spacing:1px;
      padding:3px 8px; border:1px solid var(--border-light);
      color:var(--text-muted); flex-shrink:0; }
    .file-icon.xlsx { color:var(--green); border-color:rgba(62,207,142,0.3);
      background:var(--green-bg); }
    .file-icon.pdf  { color:var(--rose);  border-color:rgba(240,98,146,0.3);
      background:var(--rose-bg); }
    .file-name { flex:1; font-family:'Noto Serif JP',serif; font-size:13px; }
    .file-date { font-family:'DM Mono',monospace; font-size:10px;
      color:var(--text-dim); letter-spacing:1px; flex-shrink:0; }
    .file-actions { display:flex; gap:8px; flex-shrink:0; }
  </style>
</head>
<body>
<div class="container">
""" + ph("03 / Plan", "History", "過去の計画表・履歴管理", "var(--amber)") + """

  {% with messages = get_flashed_messages(with_categories=true) %}
  {% for cat, msg in messages %}
  <div class="alert alert-{{ 'success' if cat == 'success' else 'error' }} fade-in">{{ msg }}</div>
  {% endfor %}
  {% endwith %}

  <div class="card fade-in">
    <div class="card-title">Archived Plans — {{ archives|length }} files</div>

    {% if archives %}
    <div>
      {% for f in archives %}
      {% set ext = f.filename.split('.')[-1].lower() %}
      <div class="file-row">
        <span class="file-icon {{ ext }}">{{ ext.upper() }}</span>
        <span class="file-name">{{ f.filename }}</span>
        <span class="file-date">{{ f.created_at or '—' }}</span>
        <div class="file-actions">
          <a href="/history/download/{{ f.history_id }}"
            class="btn btn-ghost btn-sm">↓ Download</a>
          <form method="POST" action="/history/delete/{{ f.history_id }}"
            style="display:inline;" onsubmit="return confirm('Delete this file?')">
            <button class="btn btn-danger btn-sm">×</button>
          </form>
          <form method="POST" action="/history/reset/{{ f.history_id }}"
            style="display:inline;"
            onsubmit="return confirm('履歴リセット：授業記録・出題予定も削除されます。続行しますか？')">
            <button class="btn btn-warn btn-sm">Reset</button>
          </form>
        </div>
      </div>
      {% endfor %}
    </div>
    {% else %}
    <div style="font-family:'DM Mono',monospace;font-size:11px;
      color:var(--text-dim);letter-spacing:1px;padding:20px 0;text-align:center;">
      No archived plans yet.
    </div>
    {% endif %}
  </div>

  <div style="margin-top:8px;">
    <a href="/preview" class="btn btn-primary">→ Preview &amp; Export</a>
  </div>

</div>
</body>
</html>"""

# ━━━ ファイル書き出し ━━━
files = {
    "class_schedule.html":   class_schedule_html,
    "schedule.html":         schedule_html,
    "schedule_subject.html": schedule_subject_html,
    "history.html":          history_html,
}
for fname, content in files.items():
    path = os.path.join(templates, fname)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ {fname} を更新しました")

print("\n✅ Schedule・History ページのデザイン統一完了")