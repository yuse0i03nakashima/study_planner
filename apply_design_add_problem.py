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
      --purple:#a78bfa; --purple-bg:rgba(167,139,250,0.10);
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
      letter-spacing:2px; text-transform:uppercase; color:var(--blue); }
    .page-title-ja { font-family:'Noto Serif JP',serif; font-weight:300; font-size:11px;
      color:var(--text-muted); margin-top:4px; }
    .page-header-back { font-family:'DM Mono',monospace; font-size:10px; color:var(--text-muted);
      letter-spacing:1.5px; text-decoration:none; transition:color 0.15s; }
    .page-header-back::before { content:'← '; }
    .page-header-back:hover { color:var(--text); }
    .card { background:var(--surface); border:1px solid var(--border);
      padding:24px 28px; margin-bottom:20px; }
    .card-title { font-family:'DM Mono',monospace; font-size:10px; letter-spacing:2px;
      text-transform:uppercase; color:var(--text-muted); margin-bottom:18px;
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
    textarea { resize:vertical; min-height:72px; }
    .btn { font-family:'DM Mono',monospace; font-size:11px; letter-spacing:2px;
      text-transform:uppercase; padding:10px 24px; border:none; cursor:pointer;
      transition:all 0.15s; display:inline-flex; align-items:center; gap:8px; }
    .btn-primary { background:var(--blue); color:#0c0d11; }
    .btn-primary:hover { background:#7aaafb; }
    .btn-purple { background:var(--purple-bg); color:var(--purple);
      border:1px solid rgba(167,139,250,0.3); }
    .btn-purple:hover { background:rgba(167,139,250,0.2); }
    .btn-success { background:var(--green); color:#0c0d11; }
    .btn-success:hover { background:#5eddaa; }
    .btn-danger { background:var(--red); color:white; }
    .btn-danger:hover { background:#f87171; }
    .btn-ghost { background:transparent; color:var(--text-muted);
      border:1px solid var(--border-light); }
    .btn-ghost:hover { border-color:var(--text-muted); color:var(--text); }
    .btn-sm { padding:5px 14px; font-size:10px; }
    .grid-2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
    .grid-3 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; }
    .grid-4 { display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:16px; }
    .hint { font-family:'DM Mono',monospace; font-size:9px; color:var(--text-dim);
      margin-top:5px; letter-spacing:0.5px; }
    .data-table { width:100%; border-collapse:collapse; background:var(--surface); font-size:12px; }
    .data-table th { background:var(--surface2); color:var(--text-muted);
      font-family:'DM Mono',monospace; font-size:9px; letter-spacing:1.5px;
      text-transform:uppercase; padding:10px 12px; text-align:center;
      border-bottom:1px solid var(--border-light); white-space:nowrap; }
    .data-table td { padding:8px 12px; border-bottom:1px solid var(--border);
      text-align:center; vertical-align:middle; }
    .data-table tr:hover td { background:var(--surface2); }
    .data-table td.left { text-align:left; font-family:'Noto Serif JP',serif; }
    .meta-text { font-family:'DM Mono',monospace; font-size:10px;
      color:var(--text-dim); letter-spacing:1px; }
    /* AI提案ボックス */
    .ai-box { background:var(--purple-bg); border:1px solid rgba(167,139,250,0.25);
      padding:20px 24px; margin-bottom:20px; }
    .ai-box-title { font-family:'DM Mono',monospace; font-size:10px; letter-spacing:2px;
      text-transform:uppercase; color:var(--purple); margin-bottom:14px;
      padding-bottom:10px; border-bottom:1px solid rgba(167,139,250,0.2); }
    .ai-result { margin-top:14px; background:var(--surface2);
      border:1px solid var(--border-light); padding:14px 16px;
      font-family:'DM Mono',monospace; font-size:11px; letter-spacing:0.5px;
      white-space:pre-wrap; display:none; color:var(--text-muted); }
    .loading { font-family:'DM Mono',monospace; font-size:10px; color:var(--text-dim);
      letter-spacing:1px; display:none; }
    /* チェックボックス */
    input[type="checkbox"] { accent-color:var(--blue); width:14px; height:14px; }
    .student-checks { display:flex; gap:20px; flex-wrap:wrap; margin-top:8px; }
    .student-checks label { font-weight:normal; display:flex; align-items:center;
      gap:8px; margin:0; text-transform:none; letter-spacing:0; font-size:13px;
      color:var(--text); font-family:'Noto Serif JP',serif; }
    .fade-in { animation:fadeIn 0.3s ease both; }
    @keyframes fadeIn { from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:translateY(0);} }
    #toast { position:fixed; bottom:32px; left:50%; transform:translateX(-50%) translateY(20px);
      background:var(--surface2); border:1px solid var(--border-light); color:var(--text);
      font-family:'DM Mono',monospace; font-size:11px; letter-spacing:1px;
      padding:12px 24px; opacity:0; transition:all 0.3s ease; pointer-events:none; z-index:9999; }
    #toast.show { opacity:1; transform:translateX(-50%) translateY(0); }
    #toast.success { border-left:2px solid var(--green); color:var(--green); }
    #toast.info    { border-left:2px solid var(--blue); color:var(--blue); }
    #toast.warn    { border-left:2px solid var(--amber); color:var(--amber); }
    a { color:var(--blue); text-decoration:none; }"""

problems_html = """\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@300;400;500;600&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
  <title>Add Problem — Study Planner</title>
  <style>
""" + COMMON_CSS + """
  </style>
</head>
<body>
<div class="container">

  <div class="page-header fade-in">
    <div>
      <div class="page-label">01 / Master Data</div>
      <div class="page-title">Add Problem</div>
      <div class="page-title-ja">問題マスタへの新規登録</div>
    </div>
    <a class="page-header-back" href="/">TOP</a>
  </div>

  <!-- AI提案ボックス -->
  <div class="ai-box fade-in">
    <div class="ai-box-title">AI Suggest — 4パラメータ自動提案</div>
    <textarea id="ai-input"
      placeholder="問題の内容・特徴を入力してください&#10;例：体系数学2 代数 大問5 因数分解の応用。難しめ。"></textarea>
    <div style="display:flex;gap:12px;align-items:center;margin-top:12px;">
      <button class="btn btn-purple btn-sm" onclick="askAI()">✦ AI に提案してもらう</button>
      <span class="loading" id="ai-loading">analysing...</span>
    </div>
    <div class="ai-result" id="ai-result"></div>
    <div style="margin-top:12px;display:none;" id="apply-row">
      <button class="btn btn-success btn-sm" onclick="applyAI()">↓ フォームに反映する</button>
    </div>
  </div>

  <!-- 登録フォーム -->
  <div class="card fade-in">
    <div class="card-title">Problem Entry</div>
    <form method="POST" id="problem-form">

      <div class="grid-2">
        <div>
          <label>Subject</label>
          <select name="subject" id="f-subject" onchange="filterTextbooks()">
            {% for subj in all_subjects %}
            <option value="{{ subj }}">{{ subj }}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label>Textbook</label>
          <select name="textbook_id" id="f-textbook_id">
            {% for t in textbooks %}
            <option value="{{ t.textbook_id }}" data-subject="{{ t.subject }}">
              {% if t.series_name %}[{{ t.series_name }}] {% endif %}{{ t.name }}
            </option>
            {% endfor %}
          </select>
          <p class="hint">
            <a href="/textbooks" style="color:var(--blue);">+ New Textbook</a>
          </p>
        </div>
      </div>

      <label>Problem Number / Name</label>
      <input type="text" name="problem_number" id="f-problem_number"
        placeholder="例：大問5（因数分解の応用）" required>

      <div class="grid-4" style="margin-top:0;">
        <div>
          <label>Importance</label>
          <select name="importance" id="f-importance">
            <option value="5">5 — 最重要</option>
            <option value="4">4 — 重要</option>
            <option value="3" selected>3 — 標準</option>
            <option value="2">2 — やや低</option>
            <option value="1">1 — 低</option>
          </select>
        </div>
        <div>
          <label>Difficulty</label>
          <select name="difficulty" id="f-difficulty">
            <option value="5">5 — 最難</option>
            <option value="4">4 — 難</option>
            <option value="3" selected>3 — 標準</option>
            <option value="2">2 — 易</option>
            <option value="1">1 — 基礎</option>
          </select>
        </div>
        <div>
          <label>Review Value</label>
          <select name="review_value" id="f-review_value">
            <option value="5">5 — 最高</option>
            <option value="4">4 — 高</option>
            <option value="3" selected>3 — 標準</option>
            <option value="2">2 — 低</option>
            <option value="1">1 — 最低</option>
          </select>
        </div>
        <div>
          <label>Est. Minutes</label>
          <select name="estimated_minutes" id="f-estimated_minutes">
            {% for m in range(5, 125, 5) %}
            <option value="{{ m }}" {% if m == 15 %}selected{% endif %}>{{ m }} min</option>
            {% endfor %}
          </select>
        </div>
      </div>

      <div class="grid-2" style="margin-top:0;">
        <div>
          <label>Category</label>
          <select name="category" id="f-category">
            <option value="予習" selected>予習</option>
            <option value="復習">復習</option>
            <option value="定着">定着</option>
            <option value="再定着">再定着</option>
          </select>
        </div>
        <div>
          <label>Scheduled Date</label>
          <input type="date" name="scheduled_date">
          <p class="hint">空欄 → 問題マスタのみに登録</p>
        </div>
      </div>

      <label>Instruction</label>
      <textarea name="instruction" id="f-instruction"
        placeholder="例：因数分解の手順を意識して解くこと。"></textarea>

      <label>Students</label>
      <div class="student-checks">
        {% for s in students %}
        <label>
          <input type="checkbox" name="student_ids" value="{{ s.student_id }}">
          {{ s.name }}
        </label>
        {% endfor %}
      </div>

      <div style="margin-top:24px;display:flex;gap:12px;">
        <button type="submit" class="btn btn-primary">Register →</button>
        <a href="/problems/list" class="btn btn-ghost">Problem List</a>
      </div>

    </form>
  </div>

  <!-- 直近50件 -->
  <div class="card fade-in">
    <div class="card-title">Recent Problems — 直近50件</div>
    <div style="overflow-x:auto;">
    <table class="data-table">
      <thead>
        <tr>
          <th>ID</th><th>教科</th><th>テキスト</th><th>問題番号</th>
          <th>Imp</th><th>Dif</th><th>RV</th><th>分</th><th>学習指示</th><th></th>
        </tr>
      </thead>
      <tbody>
      {% for p in problems %}
      <tr id="row-{{ p.problem_id }}">
        <td class="meta-text">{{ p.problem_id }}</td>
        <td class="meta-text">{{ p.subject }}</td>
        <td class="left" style="max-width:130px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:11px;">
          {{ p.textbook }}
        </td>
        <td class="left" style="max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:11px;">
          {{ p.problem_number }}
        </td>
        <td class="meta-text">{{ p.importance }}</td>
        <td class="meta-text">{{ p.difficulty }}</td>
        <td class="meta-text">{{ p.review_value }}</td>
        <td class="meta-text">{{ p.estimated_minutes }}</td>
        <td class="left" style="max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:11px;">
          {{ p.instruction or '—' }}
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
  </div>

  <div id="toast"></div>

</div>
<script>
let aiData = null;

// 教科でテキストを絞り込む
function filterTextbooks() {
  const subject = document.getElementById('f-subject').value;
  const select = document.getElementById('f-textbook_id');
  let first = true;
  for (const opt of select.options) {
    opt.hidden = opt.dataset.subject !== subject;
    if (!opt.hidden && first) { opt.selected = true; first = false; }
  }
}
filterTextbooks();

// AI提案
async function askAI() {
  const input = document.getElementById('ai-input').value.trim();
  if (!input) { showToast('問題の説明を入力してください', 'warn'); return; }
  document.getElementById('ai-loading').style.display = 'inline';
  document.getElementById('ai-result').style.display = 'none';
  document.getElementById('apply-row').style.display = 'none';
  try {
    const res = await fetch('/api/ai_suggest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: input })
    });
    const data = await res.json();
    aiData = data;
    const r = document.getElementById('ai-result');
    r.style.display = 'block';
    r.textContent =
      `importance     : ${data.importance}\n` +
      `difficulty     : ${data.difficulty}\n` +
      `review_value   : ${data.review_value}\n` +
      `est_minutes    : ${data.estimated_minutes} min\n` +
      `instruction    : ${data.instruction || '（なし）'}`;
    document.getElementById('apply-row').style.display = 'block';
  } catch(e) {
    showToast('AI呼び出しに失敗しました', 'warn');
  } finally {
    document.getElementById('ai-loading').style.display = 'none';
  }
}

function applyAI() {
  if (!aiData) return;
  document.getElementById('f-importance').value      = aiData.importance;
  document.getElementById('f-difficulty').value      = aiData.difficulty;
  document.getElementById('f-review_value').value    = aiData.review_value;
  document.getElementById('f-estimated_minutes').value = aiData.estimated_minutes;
  document.getElementById('f-instruction').value     = aiData.instruction || '';
  showToast('↓ フォームに反映しました', 'success');
}

async function deleteProblem(id, btn) {
  if (!confirm('Problem ' + id + ' を削除しますか？')) return;
  const res = await fetch('/problems/delete/' + id, { method: 'POST' });
  if (res.ok) {
    document.getElementById('row-' + id)?.remove();
    showToast('Deleted.', 'success');
  } else { showToast('Delete failed.', 'warn'); }
}

function showToast(msg, type='success') {
  const t = document.getElementById('toast');
  t.textContent = msg; t.className = 'show ' + type;
  setTimeout(() => { t.className = ''; }, 3000);
}
</script>
</body>
</html>"""

path = os.path.join(templates, "problems.html")
with open(path, "w", encoding="utf-8") as f:
    f.write(problems_html)
print("✅ problems.html を更新しました")
print("✅ 完了")