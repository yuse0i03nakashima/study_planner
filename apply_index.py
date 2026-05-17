import os

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")

html = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Study Planner</title>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@300;400;500;600&family=DM+Mono:wght@300;400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg:           #0c0d11;
      --surface:      #13151e;
      --surface2:     #1b1e2b;
      --border:       #252838;
      --border-light: #2f3347;
      --text:         #dde1ec;
      --text-muted:   #7a8399;
      --text-dim:     #3a3f54;
      --blue:   #5b8ff9;
      --green:  #3ecf8e;
      --amber:  #f5a623;
      --rose:   #f06292;
      --blue-bg:  rgba(91,143,249,0.08);
      --green-bg: rgba(62,207,142,0.08);
      --amber-bg: rgba(245,166,35,0.08);
      --rose-bg:  rgba(240,98,146,0.08);
    }
    *, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
    body {
      font-family: 'Noto Serif JP', serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 56px 32px 80px;
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
      opacity: 0.18;
      pointer-events: none;
      z-index: 0;
    }
    .container { max-width: 860px; margin: 0 auto; position: relative; z-index: 1; }
    .header {
      margin-bottom: 64px;
      padding-bottom: 32px;
      border-bottom: 1px solid var(--border-light);
      display: grid;
      grid-template-columns: 1fr auto;
      align-items: end;
      gap: 32px;
    }
    .logo-block { display: flex; flex-direction: column; gap: 0; }
    .logo-top { display: flex; align-items: flex-end; gap: 0; line-height: 1; margin-bottom: 2px; }
    .logo-abbr { font-family: 'DM Mono', monospace; font-weight: 500; font-size: 52px; letter-spacing: -4px; color: var(--text); line-height: 1; }
    .logo-bracket { font-family: 'DM Mono', monospace; font-size: 38px; font-weight: 300; color: var(--border-light); line-height: 1; margin: 0 4px; align-self: center; }
    .logo-fullname {
      font-family: 'DM Mono', monospace; font-weight: 400; font-size: 13px;
      letter-spacing: 6px; text-transform: uppercase; color: var(--text);
      margin-top: 6px; display: flex; align-items: center; gap: 12px;
    }
    .logo-fullname .dot { width: 4px; height: 4px; background: var(--blue); display: inline-block; box-shadow: 0 0 6px var(--blue); }
    .logo-sub {
      font-family: 'DM Mono', monospace; font-weight: 300; font-size: 9px;
      letter-spacing: 3px; text-transform: uppercase; color: var(--text-muted);
      margin-top: 10px; display: flex; align-items: center; gap: 10px;
    }
    .logo-sub::before { content: ''; display: block; width: 20px; height: 1px; background: var(--border-light); }
    .header-meta { text-align: right; }
    .header-meta .date { font-family: 'DM Mono', monospace; font-size: 10px; color: var(--text-muted); letter-spacing: 1.5px; }
    .status { display: flex; align-items: center; gap: 6px; margin-top: 6px; justify-content: flex-end; }
    .status-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--green); box-shadow: 0 0 6px var(--green); animation: pulse 2.5s ease-in-out infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
    .status span { font-family: 'DM Mono', monospace; font-size: 9.5px; color: var(--green); letter-spacing: 1px; }
    .category { margin-bottom: 40px; animation: fadeUp 0.4s ease both; }
    .category:nth-child(1) { animation-delay: 0.05s; }
    .category:nth-child(2) { animation-delay: 0.12s; }
    .category:nth-child(3) { animation-delay: 0.19s; }
    .category:nth-child(4) { animation-delay: 0.26s; }
    @keyframes fadeUp { from { opacity:0; transform:translateY(14px); } to { opacity:1; transform:translateY(0); } }
    .cat-header { display: flex; align-items: baseline; gap: 12px; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
    .cat-num { font-family: 'DM Mono', monospace; font-size: 10px; color: var(--text-dim); flex-shrink: 0; letter-spacing: 1px; }
    .cat-en { font-family: 'DM Mono', monospace; font-weight: 500; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; }
    .cat-ja { font-family: 'Noto Serif JP', serif; font-size: 11px; font-weight: 300; color: var(--text-muted); letter-spacing: 1px; }
    .cat-rule { flex: 1; height: 1px; background: linear-gradient(to right, var(--border-light), transparent); align-self: center; }
    .menu-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 6px; }
    .menu-item {
      display: flex; align-items: center; gap: 14px; padding: 14px 16px;
      background: var(--surface); border: 1px solid var(--border);
      border-left-width: 2px; text-decoration: none; color: var(--text);
      transition: all 0.16s ease; cursor: pointer;
    }
    .menu-item:hover { background: var(--surface2); transform: translateX(3px); }
    .menu-icon { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; position: relative; }
    .menu-icon::before { content: ''; position: absolute; inset: 0; border-top: 1px solid currentColor; border-left: 1px solid currentColor; opacity: 0.25; }
    .menu-icon::after { content: ''; position: absolute; inset: 0; border-bottom: 1px solid currentColor; border-right: 1px solid currentColor; opacity: 0.25; }
    .menu-icon svg { width: 16px; height: 16px; stroke-width: 1.5; }
    .menu-text { flex: 1; min-width: 0; }
    .menu-en { font-family: 'DM Mono', monospace; font-weight: 500; font-size: 12px; letter-spacing: 1.5px; text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .menu-ja { font-family: 'Noto Serif JP', serif; font-size: 10.5px; font-weight: 300; color: var(--text-muted); margin-top: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; letter-spacing: 0.3px; }
    .menu-arrow { font-family: 'DM Mono', monospace; font-size: 11px; color: var(--text-dim); flex-shrink: 0; transition: color 0.16s, transform 0.16s; }
    .menu-item:hover .menu-arrow { transform: translateX(3px); }
    .master   .cat-en    { color: var(--blue); }
    .master   .menu-item { border-left-color: var(--blue); }
    .master   .menu-item:hover { border-color: rgba(91,143,249,0.3); border-left-color: var(--blue); box-shadow: 0 2px 12px rgba(91,143,249,0.08); }
    .master   .menu-item:hover .menu-arrow { color: var(--blue); }
    .master   .menu-icon { color: var(--blue); background: var(--blue-bg); }
    .schedule .cat-en    { color: var(--green); }
    .schedule .menu-item { border-left-color: var(--green); }
    .schedule .menu-item:hover { border-color: rgba(62,207,142,0.3); border-left-color: var(--green); box-shadow: 0 2px 12px rgba(62,207,142,0.08); }
    .schedule .menu-item:hover .menu-arrow { color: var(--green); }
    .schedule .menu-icon { color: var(--green); background: var(--green-bg); }
    .plan     .cat-en    { color: var(--amber); }
    .plan     .menu-item { border-left-color: var(--amber); }
    .plan     .menu-item:hover { border-color: rgba(245,166,35,0.3); border-left-color: var(--amber); box-shadow: 0 2px 12px rgba(245,166,35,0.08); }
    .plan     .menu-item:hover .menu-arrow { color: var(--amber); }
    .plan     .menu-icon { color: var(--amber); background: var(--amber-bg); }
    .record   .cat-en    { color: var(--rose); }
    .record   .menu-item { border-left-color: var(--rose); }
    .record   .menu-item:hover { border-color: rgba(240,98,146,0.3); border-left-color: var(--rose); box-shadow: 0 2px 12px rgba(240,98,146,0.08); }
    .record   .menu-item:hover .menu-arrow { color: var(--rose); }
    .record   .menu-icon { color: var(--rose); background: var(--rose-bg); }
    .footer { margin-top: 64px; padding-top: 20px; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
    .footer p { font-family: 'DM Mono', monospace; font-size: 9px; color: var(--text-dim); letter-spacing: 1.5px; text-transform: uppercase; }
    .footer .ver { font-family: 'DM Mono', monospace; font-size: 10px; color: var(--text-muted); letter-spacing: 2px; }
  </style>
</head>
<body>
<div class="container">

  <header class="header">
    <div class="logo-block">
      <div class="logo-top">
        <span class="logo-bracket">[</span>
        <span class="logo-abbr">SP</span>
        <span class="logo-bracket">]</span>
      </div>
      <div class="logo-fullname">
        <span>STUDY</span>
        <span class="dot"></span>
        <span>PLANNER</span>
      </div>
      <div class="logo-sub">Learning Management System</div>
    </div>
    <div class="header-meta">
      <div class="date" id="today-date"></div>
      <div class="status">
        <div class="status-dot"></div>
        <span>online</span>
      </div>
    </div>
  </header>

  <section class="category master">
    <div class="cat-header">
      <span class="cat-num">01</span>
      <span class="cat-en">Master Data</span>
      <span class="cat-ja">マスタ管理</span>
      <div class="cat-rule"></div>
    </div>
    <div class="menu-grid">
      <a class="menu-item" href="/textbooks">
        <div class="menu-icon">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25"/>
          </svg>
        </div>
        <div class="menu-text">
          <div class="menu-en">Textbooks</div>
          <div class="menu-ja">テキスト・シリーズ・セクション管理</div>
        </div>
        <span class="menu-arrow">&#x2192;</span>
      </a>
      <a class="menu-item" href="/problems">
        <div class="menu-icon">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/>
          </svg>
        </div>
        <div class="menu-text">
          <div class="menu-en">Add Problem</div>
          <div class="menu-ja">問題マスタへの新規登録</div>
        </div>
        <span class="menu-arrow">&#x2192;</span>
      </a>
      <a class="menu-item" href="/problems/list">
        <div class="menu-icon">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z"/>
          </svg>
        </div>
        <div class="menu-text">
          <div class="menu-en">Problem List</div>
          <div class="menu-ja">問題一覧・編集・削除</div>
        </div>
        <span class="menu-arrow">&#x2192;</span>
      </a>
      <a class="menu-item" href="/students">
        <div class="menu-icon">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"/>
          </svg>
        </div>
        <div class="menu-text">
          <div class="menu-en">Students</div>
          <div class="menu-ja">生徒情報・教科・計画モード</div>
        </div>
        <span class="menu-arrow">&#x2192;</span>
      </a>
    </div>
  </section>

  <section class="category schedule">
    <div class="cat-header">
      <span class="cat-num">02</span>
      <span class="cat-en">Schedule</span>
      <span class="cat-ja">スケジュール管理</span>
      <div class="cat-rule"></div>
    </div>
    <div class="menu-grid">
      <a class="menu-item" href="/class_schedule">
        <div class="menu-icon">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5"/>
          </svg>
        </div>
        <div class="menu-text">
          <div class="menu-en">Class Schedule</div>
          <div class="menu-ja">授業曜日・次回授業日の設定</div>
        </div>
        <span class="menu-arrow">&#x2192;</span>
      </a>
      <a class="menu-item" href="/schedule">
        <div class="menu-icon">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        </div>
        <div class="menu-text">
          <div class="menu-en">Study Hours</div>
          <div class="menu-ja">勉強時間登録（全体）</div>
        </div>
        <span class="menu-arrow">&#x2192;</span>
      </a>
      <a class="menu-item" href="/schedule_subject">
        <div class="menu-icon">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"/>
          </svg>
        </div>
        <div class="menu-text">
          <div class="menu-en">Hours per Subject</div>
          <div class="menu-ja">勉強時間登録（教科別）</div>
        </div>
        <span class="menu-arrow">&#x2192;</span>
      </a>
    </div>
  </section>

  <section class="category plan">
    <div class="cat-header">
      <span class="cat-num">03</span>
      <span class="cat-en">Plan</span>
      <span class="cat-ja">計画表</span>
      <div class="cat-rule"></div>
    </div>
    <div class="menu-grid">
      <a class="menu-item" href="/preview">
        <div class="menu-icon">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"/>
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
          </svg>
        </div>
        <div class="menu-text">
          <div class="menu-en">Preview &amp; Export</div>
          <div class="menu-ja">計画表プレビュー・Excel/PDF出力</div>
        </div>
        <span class="menu-arrow">&#x2192;</span>
      </a>
      <a class="menu-item" href="/history">
        <div class="menu-icon">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z"/>
          </svg>
        </div>
        <div class="menu-text">
          <div class="menu-en">History</div>
          <div class="menu-ja">過去の計画表・履歴リセット</div>
        </div>
        <span class="menu-arrow">&#x2192;</span>
      </a>
    </div>
  </section>

  <section class="category record">
    <div class="cat-header">
      <span class="cat-num">04</span>
      <span class="cat-en">Records</span>
      <span class="cat-ja">記録・修正</span>
      <div class="cat-rule"></div>
    </div>
    <div class="menu-grid">
      <a class="menu-item" href="/record">
        <div class="menu-icon">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"/>
          </svg>
        </div>
        <div class="menu-text">
          <div class="menu-en">Add Record</div>
          <div class="menu-ja">授業記録入力・正誤の記録</div>
        </div>
        <span class="menu-arrow">&#x2192;</span>
      </a>
      <a class="menu-item" href="/record/list">
        <div class="menu-icon">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M11.42 15.17L17.25 21A2.652 2.652 0 0021 17.25l-5.877-5.877M11.42 15.17l2.496-3.03c.317-.384.74-.626 1.208-.766M11.42 15.17l-4.655 5.653a2.548 2.548 0 11-3.586-3.586l5.653-4.655m5.585-.367l-3.027 2.496"/>
          </svg>
        </div>
        <div class="menu-text">
          <div class="menu-en">Edit Records</div>
          <div class="menu-ja">授業記録修正・習熟度の変更</div>
        </div>
        <span class="menu-arrow">&#x2192;</span>
      </a>
      <a class="menu-item" href="/assignments/list">
        <div class="menu-icon">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z"/>
          </svg>
        </div>
        <div class="menu-text">
          <div class="menu-en">Assignments</div>
          <div class="menu-ja">出題予定管理・一括編集</div>
        </div>
        <span class="menu-arrow">&#x2192;</span>
      </a>
    </div>
  </section>

  <footer class="footer">
    <p>Study Planner &middot; Learning Management System</p>
    <span class="ver">v2.0</span>
  </footer>

</div>
<script>
  const d = new Date();
  const days = ['SUN','MON','TUE','WED','THU','FRI','SAT'];
  document.getElementById('today-date').textContent =
    d.getFullYear() + '.' +
    String(d.getMonth()+1).padStart(2,'0') + '.' +
    String(d.getDate()).padStart(2,'0') + ' ' +
    days[d.getDay()];
</script>
</body>
</html>"""

with open(os.path.join(templates, "index.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("✅ index.html を更新しました")