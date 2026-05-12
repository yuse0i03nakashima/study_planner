import os

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")

# ─── 1. textbooks.html（テキスト管理画面）を新規作成 ──
textbooks_html = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>テキスト管理</title>
  <style>
    body { font-family: sans-serif; max-width: 900px; margin: 40px auto; background: #f5f7fa; }
    h1 { color: #2c3e50; }
    .form-box { background: white; padding: 24px; border-radius: 8px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    h2 { color: #2c3e50; margin-top: 0; font-size: 16px; }
    label { display: block; margin-top: 12px; font-weight: bold; }
    input[type="text"], select { width: 100%; padding: 8px; margin-top: 4px; border: 1px solid #ccc; border-radius: 4px; font-size: 15px; box-sizing: border-box; }
    .row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    button { margin-top: 16px; padding: 10px 28px; background: #4472C4; color: white; border: none; border-radius: 6px; font-size: 15px; cursor: pointer; }
    button:hover { background: #2c5fa8; }
    .btn-del { padding: 4px 10px; background: #e74c3c; color: white; border: none; border-radius: 4px; font-size: 12px; cursor: pointer; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 24px; }
    th { background: #4472C4; color: white; padding: 8px; }
    td { padding: 8px; border-bottom: 1px solid #eee; text-align: center; }
    a { color: #4472C4; }
    .section-box { background: #f0f4ff; border-radius: 6px; padding: 12px; margin-top: 8px; }
  </style>
</head>
<body>
  <h1>テキスト管理</h1>

  <!-- シリーズ登録 -->
  <div class="form-box">
    <h2>シリーズ登録</h2>
    <form method="POST" action="/textbooks/series/add">
      <label>シリーズ名</label>
      <input type="text" name="name" placeholder="例：青チャート" required>
      <button type="submit">登録</button>
    </form>
  </div>

  <!-- テキスト登録 -->
  <div class="form-box">
    <h2>テキスト登録</h2>
    <form method="POST" action="/textbooks/add">
      <div class="row2">
        <div>
          <label>シリーズ（任意）</label>
          <select name="series_id">
            <option value="">シリーズなし</option>
            {% for s in series_list %}
            <option value="{{ s.series_id }}">{{ s.name }}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label>教科</label>
          <select name="subject">
            {% for subj in all_subjects %}
            <option value="{{ subj }}">{{ subj }}</option>
            {% endfor %}
          </select>
        </div>
      </div>
      <label>テキスト名</label>
      <input type="text" name="name" placeholder="例：数I+A" required>
      <button type="submit">登録</button>
    </form>
  </div>

  <!-- テキスト一覧 -->
  <h2>テキスト一覧</h2>
  <table>
    <tr>
      <th>ID</th><th>シリーズ</th><th>テキスト名</th><th>教科</th>
      <th>問題数</th><th>使用生徒</th><th>セクション</th><th>操作</th>
    </tr>
    {% for t in textbooks %}
    <tr>
      <td>{{ t.textbook_id }}</td>
      <td>{{ t.series_name or "―" }}</td>
      <td>{{ t.name }}</td>
      <td>{{ t.subject }}</td>
      <td>{{ t.problem_count }}</td>
      <td style="font-size:12px;">{{ t.students }}</td>
      <td>
        <a href="/textbooks/{{ t.textbook_id }}/sections">セクション管理</a>
      </td>
      <td>
        <form method="POST" action="/textbooks/delete/{{ t.textbook_id }}"
              style="display:inline"
              onsubmit="return confirm('削除しますか？')">
          <button class="btn-del">削除</button>
        </form>
      </td>
    </tr>
    {% endfor %}
  </table>

  <!-- シリーズ一覧 -->
  <h2>シリーズ一覧</h2>
  <table>
    <tr><th>ID</th><th>シリーズ名</th><th>テキスト数</th><th>操作</th></tr>
    {% for s in series_list %}
    <tr>
      <td>{{ s.series_id }}</td>
      <td>{{ s.name }}</td>
      <td>{{ s.textbook_count }}</td>
      <td>
        <form method="POST" action="/textbooks/series/delete/{{ s.series_id }}"
              style="display:inline"
              onsubmit="return confirm('削除しますか？')">
          <button class="btn-del">削除</button>
        </form>
      </td>
    </tr>
    {% endfor %}
  </table>

  <p><a href="/">← トップに戻る</a></p>
</body>
</html>"""

with open(os.path.join(templates, "textbooks.html"), "w", encoding="utf-8") as f:
    f.write(textbooks_html)
print("✅ textbooks.html を作成しました")

# ─── 2. sections.html（セクション管理画面）を新規作成 ──
sections_html = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>セクション管理</title>
  <style>
    body { font-family: sans-serif; max-width: 700px; margin: 40px auto; background: #f5f7fa; }
    h1 { color: #2c3e50; }
    .form-box { background: white; padding: 24px; border-radius: 8px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    label { display: block; margin-top: 12px; font-weight: bold; }
    input[type="text"], input[type="number"] { width: 100%; padding: 8px; margin-top: 4px; border: 1px solid #ccc; border-radius: 4px; font-size: 15px; box-sizing: border-box; }
    button { margin-top: 16px; padding: 10px 28px; background: #4472C4; color: white; border: none; border-radius: 6px; font-size: 15px; cursor: pointer; }
    button:hover { background: #2c5fa8; }
    .btn-del { padding: 4px 10px; background: #e74c3c; color: white; border: none; border-radius: 4px; font-size: 12px; cursor: pointer; margin-top: 0; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    th { background: #4472C4; color: white; padding: 8px; }
    td { padding: 8px; border-bottom: 1px solid #eee; text-align: center; }
    a { color: #4472C4; }
  </style>
</head>
<body>
  <h1>「{{ textbook.name }}」セクション管理</h1>
  <p style="color:#555;">シリーズ：{{ textbook.series_name or "なし" }} ／ 教科：{{ textbook.subject }}</p>

  <div class="form-box">
    <h2 style="font-size:16px;">セクションを追加</h2>
    <form method="POST">
      <label>セクション名</label>
      <input type="text" name="name" placeholder="例：第1章 展開と因数分解" required>
      <label>表示順</label>
      <input type="number" name="order_index" value="0" min="0">
      <button type="submit">追加</button>
    </form>
  </div>

  <table>
    <tr><th>順序</th><th>セクション名</th><th>問題数</th><th>操作</th></tr>
    {% for s in sections %}
    <tr>
      <td>{{ s.order_index }}</td>
      <td>{{ s.name }}</td>
      <td>{{ s.problem_count }}</td>
      <td>
        <form method="POST" action="/textbooks/sections/delete/{{ s.section_id }}"
              style="display:inline"
              onsubmit="return confirm('削除しますか？')">
          <button class="btn-del">削除</button>
        </form>
      </td>
    </tr>
    {% endfor %}
  </table>

  <p><a href="/textbooks">← テキスト管理に戻る</a></p>
</body>
</html>"""

with open(os.path.join(templates, "sections.html"), "w", encoding="utf-8") as f:
    f.write(sections_html)
print("✅ sections.html を作成しました")

# ─── 3. problems.htmlを更新（テキストをドロップダウンに）──
problems_html = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>問題マスタ登録</title>
  <style>
    body { font-family: sans-serif; max-width: 900px; margin: 40px auto; background: #f5f7fa; }
    h1 { color: #2c3e50; }
    .form-box { background: white; padding: 24px; border-radius: 8px; margin-bottom: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    label { display: block; margin-top: 12px; font-weight: bold; }
    input[type="text"], input[type="date"], input[type="number"], select, textarea {
      width: 100%; padding: 8px; margin-top: 4px; border: 1px solid #ccc;
      border-radius: 4px; font-size: 15px; box-sizing: border-box;
    }
    textarea { height: 70px; resize: vertical; }
    .row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .row3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
    .hint { font-size: 12px; color: #888; margin-top: 2px; }
    .student-checks { display: flex; gap: 16px; margin-top: 8px; flex-wrap: wrap; }
    .student-checks label { font-weight: normal; display: flex; align-items: center; gap: 6px; }
    .student-checks input { width: auto; }
    .ai-box { background: #f0f4ff; border: 1px solid #4472C4; border-radius: 8px; padding: 16px; margin-bottom: 24px; }
    .ai-box h3 { margin: 0 0 8px 0; color: #2c3e50; font-size: 15px; }
    .ai-box textarea { height: 80px; }
    .ai-result { margin-top: 12px; background: white; border-radius: 6px; padding: 12px; font-size: 13px; white-space: pre-wrap; display: none; }
    button { margin-top: 16px; padding: 10px 28px; background: #4472C4; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; }
    button:hover { background: #2c5fa8; }
    .btn-ai { background: #8e44ad; font-size: 14px; padding: 8px 20px; margin-top: 8px; }
    .btn-ai:hover { background: #6c3483; }
    .btn-ai-apply { background: #27ae60; font-size: 14px; padding: 8px 20px; margin-top: 8px; display: none; }
    .btn-ai-apply:hover { background: #1e8449; }
    .btn-edit { padding: 4px 10px; background: #4472C4; color: white; border-radius: 4px; text-decoration: none; font-size: 12px; margin-right: 4px; }
    .btn-del { padding: 4px 10px; background: #e74c3c; color: white; border: none; border-radius: 4px; font-size: 12px; cursor: pointer; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); font-size: 12px; }
    th { background: #4472C4; color: white; padding: 8px; }
    td { padding: 6px 8px; border-bottom: 1px solid #eee; text-align: center; }
    td.left { text-align: left; }
    a { color: #4472C4; }
    .loading { color: #888; font-size: 13px; display: none; }
    .textbook-new { font-size: 12px; color: #4472C4; margin-top: 4px; display: block; }
  </style>
</head>
<body>
  <h1>① 問題マスタ登録・編集</h1>

  <!-- AI自動入力ボックス -->
  <div class="ai-box">
    <h3>🤖 AIによる問題情報の自動提案</h3>
    <textarea id="ai-input" placeholder="例：体系数学2 代数 大問5 因数分解の応用。難しめの問題。"></textarea>
    <br>
    <button class="btn-ai" onclick="askAI()">AIに提案してもらう</button>
    <span class="loading" id="ai-loading">⏳ 分析中...</span>
    <div class="ai-result" id="ai-result"></div>
    <button class="btn-ai-apply" id="btn-apply" onclick="applyAI()">↓ フォームに反映する</button>
  </div>

  <div class="form-box">
    <form method="POST" id="problem-form">
      <div class="row2">
        <div>
          <label>教科</label>
          <select name="subject" id="f-subject" onchange="filterTextbooks()">
            {% for subj in all_subjects %}
            <option value="{{ subj }}">{{ subj }}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label>テキスト</label>
          <select name="textbook_id" id="f-textbook_id">
            {% for t in textbooks %}
            <option value="{{ t.textbook_id }}"
              data-subject="{{ t.subject }}">
              {% if t.series_name %}[{{ t.series_name }}] {% endif %}{{ t.name }}
            </option>
            {% endfor %}
          </select>
          <a href="/textbooks" class="textbook-new">＋ テキストを新規登録</a>
        </div>
      </div>
      <label>問題番号・名称</label>
      <input type="text" name="problem_number" id="f-problem_number"
             placeholder="例：大問5" required>
      <div class="row3">
        <div>
          <label>重要度（1〜5）</label>
          <select name="importance" id="f-importance">
            <option value="5">5（最重要）</option>
            <option value="4">4（重要）</option>
            <option value="3" selected>3（標準）</option>
            <option value="2">2（やや低）</option>
            <option value="1">1（低）</option>
          </select>
        </div>
        <div>
          <label>難易度（1〜5）</label>
          <select name="difficulty" id="f-difficulty">
            <option value="5">5（最難）</option>
            <option value="4">4（難）</option>
            <option value="3" selected>3（標準）</option>
            <option value="2">2（易）</option>
            <option value="1">1（基礎）</option>
          </select>
        </div>
        <div>
          <label>復習価値（1〜5）</label>
          <select name="review_value" id="f-review_value">
            <option value="5">5（最高）</option>
            <option value="4">4（高）</option>
            <option value="3" selected>3（標準）</option>
            <option value="2">2（低）</option>
            <option value="1">1（最低）</option>
          </select>
        </div>
      </div>
      <div class="row2">
        <div>
          <label>所要時間（5分単位）</label>
          <select name="estimated_minutes" id="f-estimated_minutes">
            {% for m in range(5, 125, 5) %}
            <option value="{{ m }}" {% if m == 15 %}selected{% endif %}>{{ m }}分</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label>出題区分</label>
          <select name="category" id="f-category">
            <option value="予習" selected>予習</option>
            <option value="復習">復習</option>
            <option value="定着">定着</option>
            <option value="再定着">再定着</option>
          </select>
        </div>
      </div>
      <label>学習指示（任意）</label>
      <textarea name="instruction" id="f-instruction"
        placeholder="例：因数分解の手順を意識して解くこと。"></textarea>
      <label>出題する生徒（複数選択可）</label>
      <div class="student-checks">
        {% for s in students %}
        <label>
          <input type="checkbox" name="student_ids" value="{{ s.student_id }}">
          {{ s.name }}
        </label>
        {% endfor %}
      </div>
      <label>出題日（任意・未定の場合は空欄）</label>
      <input type="date" name="scheduled_date">
      <p class="hint">空欄の場合は問題マスタのみに登録されます。</p>
      <button type="submit">登録する</button>
    </form>
  </div>

  <h2>直近50件</h2>
  <table>
    <tr>
      <th>ID</th><th>教科</th><th>テキスト</th><th>問題番号</th>
      <th>重要度</th><th>難易度</th><th>復習価値</th><th>所要時間</th>
      <th>学習指示</th><th>操作</th>
    </tr>
    {% for p in problems %}
    <tr id="row-{{ p.problem_id }}">
      <td>{{ p.problem_id }}</td>
      <td>{{ p.subject }}</td>
      <td class="left">{{ p.textbook }}</td>
      <td>{{ p.problem_number }}</td>
      <td>{{ p.importance }}</td>
      <td>{{ p.difficulty }}</td>
      <td>{{ p.review_value }}</td>
      <td>{{ p.estimated_minutes }}分</td>
      <td class="left" style="max-width:140px;font-size:11px;">{{ p.instruction or "―" }}</td>
      <td>
        <a class="btn-edit" href="/problems/edit/{{ p.problem_id }}">編集</a>
        <button class="btn-del" onclick="deleteProblem({{ p.problem_id }}, this)">削除</button>
      </td>
    </tr>
    {% endfor %}
  </table>
  <p><a href="/">← トップに戻る</a></p>

  <script>
    let aiData = null;

    // 教科でテキストを絞り込む
    function filterTextbooks() {
      const subject = document.getElementById('f-subject').value;
      const select = document.getElementById('f-textbook_id');
      for (let opt of select.options) {
        opt.hidden = opt.dataset.subject !== subject;
      }
      // 最初の表示項目を選択
      for (let opt of select.options) {
        if (!opt.hidden) { opt.selected = true; break; }
      }
    }

    // 初期絞り込み
    filterTextbooks();

    async function askAI() {
      const input = document.getElementById('ai-input').value;
      if (!input.trim()) { alert('問題の説明を入力してください。'); return; }
      document.getElementById('ai-loading').style.display = 'inline';
      document.getElementById('ai-result').style.display = 'none';
      document.getElementById('btn-apply').style.display = 'none';
      try {
        const res = await fetch('/api/ai_suggest', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({text: input})
        });
        const data = await res.json();
        aiData = data;
        const resultDiv = document.getElementById('ai-result');
        resultDiv.style.display = 'block';
        resultDiv.innerHTML =
          `重要度：${data.importance}　難易度：${data.difficulty}　復習価値：${data.review_value}　所要時間：${data.estimated_minutes}分\n学習指示：${data.instruction || '（なし）'}`;
        document.getElementById('btn-apply').style.display = 'inline';
      } catch(e) {
        alert('AIの呼び出しに失敗しました: ' + e);
      } finally {
        document.getElementById('ai-loading').style.display = 'none';
      }
    }

    function applyAI() {
      if (!aiData) return;
      document.getElementById('f-importance').value = aiData.importance;
      document.getElementById('f-difficulty').value = aiData.difficulty;
      document.getElementById('f-review_value').value = aiData.review_value;
      document.getElementById('f-estimated_minutes').value = aiData.estimated_minutes;
      document.getElementById('f-instruction').value = aiData.instruction || '';
    }

    async function deleteProblem(problemId, btn) {
      if (!confirm('問題ID ' + problemId + ' を削除しますか？')) return;
      try {
        const res = await fetch('/problems/delete/' + problemId, {method: 'POST'});
        if (res.ok) {
          const row = document.getElementById('row-' + problemId);
          if (row) row.remove();
        } else { alert('削除に失敗しました。'); }
      } catch(e) { alert('削除に失敗しました: ' + e); }
    }
  </script>
</body>
</html>"""

with open(os.path.join(templates, "problems.html"), "w", encoding="utf-8") as f:
    f.write(problems_html)
print("✅ problems.html を更新しました")

# ─── 4. app.pyにテキスト管理ルートを追加 ────────────────
app_path = os.path.join(base, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

textbook_routes = '''
@app.route("/textbooks")
def textbooks():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT t.textbook_id, t.name, t.subject,
               s.name as series_name,
               COUNT(DISTINCT p.problem_id) as problem_count,
               GROUP_CONCAT(DISTINCT st.name) as students
        FROM textbooks t
        LEFT JOIN series s ON t.series_id = s.series_id
        LEFT JOIN problems p ON t.textbook_id = p.textbook_id
        LEFT JOIN student_textbooks stb ON t.textbook_id = stb.textbook_id
        LEFT JOIN students st ON stb.student_id = st.student_id
        GROUP BY t.textbook_id
        ORDER BY t.subject, s.name, t.name
    """)
    tb_list = c.fetchall()
    c.execute("""
        SELECT s.series_id, s.name,
               COUNT(t.textbook_id) as textbook_count
        FROM series s
        LEFT JOIN textbooks t ON s.series_id = t.series_id
        GROUP BY s.series_id ORDER BY s.name
    """)
    series_list = c.fetchall()
    c.execute("SELECT DISTINCT subject FROM students ORDER BY subject")
    all_subjects_raw = c.fetchall()
    all_subjects = []
    for row in all_subjects_raw:
        for subj in row["subject"].split(","):
            s = subj.strip()
            if s and s not in all_subjects:
                all_subjects.append(s)
    conn.close()
    return render_template("textbooks.html",
                           textbooks=tb_list,
                           series_list=series_list,
                           all_subjects=sorted(all_subjects))


@app.route("/textbooks/series/add", methods=["POST"])
def textbook_series_add():
    name = request.form["name"].strip()
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO series (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()
    return redirect("/textbooks")


@app.route("/textbooks/series/delete/<int:series_id>", methods=["POST"])
def textbook_series_delete(series_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE textbooks SET series_id=NULL WHERE series_id=?", (series_id,))
    c.execute("DELETE FROM series WHERE series_id=?", (series_id,))
    conn.commit()
    conn.close()
    return redirect("/textbooks")


@app.route("/textbooks/add", methods=["POST"])
def textbook_add():
    series_id = request.form.get("series_id") or None
    name = request.form["name"].strip()
    subject = request.form["subject"]
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO textbooks (series_id, name, subject) VALUES (?, ?, ?)
    """, (series_id, name, subject))
    conn.commit()
    conn.close()
    return redirect("/textbooks")


@app.route("/textbooks/delete/<int:textbook_id>", methods=["POST"])
def textbook_delete(textbook_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as cnt FROM problems WHERE textbook_id=?",
              (textbook_id,))
    if c.fetchone()["cnt"] > 0:
        conn.close()
        return "このテキストには問題が登録されているため削除できません。", 400
    c.execute("DELETE FROM student_textbooks WHERE textbook_id=?", (textbook_id,))
    c.execute("DELETE FROM textbooks WHERE textbook_id=?", (textbook_id,))
    conn.commit()
    conn.close()
    return redirect("/textbooks")


@app.route("/textbooks/<int:textbook_id>/sections", methods=["GET", "POST"])
def textbook_sections(textbook_id):
    conn = get_connection()
    c = conn.cursor()
    if request.method == "POST":
        name = request.form["name"].strip()
        order_index = int(request.form.get("order_index", 0))
        c.execute("""
            INSERT INTO textbook_sections (textbook_id, name, order_index)
            VALUES (?, ?, ?)
        """, (textbook_id, name, order_index))
        conn.commit()
        return redirect(f"/textbooks/{textbook_id}/sections")

    c.execute("""
        SELECT t.*, s.name as series_name FROM textbooks t
        LEFT JOIN series s ON t.series_id = s.series_id
        WHERE t.textbook_id=?
    """, (textbook_id,))
    textbook = c.fetchone()
    c.execute("""
        SELECT ts.*, COUNT(p.problem_id) as problem_count
        FROM textbook_sections ts
        LEFT JOIN problems p ON ts.section_id = p.section_id
        WHERE ts.textbook_id=?
        GROUP BY ts.section_id
        ORDER BY ts.order_index, ts.section_id
    """, (textbook_id,))
    sections = c.fetchall()
    conn.close()
    return render_template("sections.html",
                           textbook=textbook, sections=sections)


@app.route("/textbooks/sections/delete/<int:section_id>", methods=["POST"])
def section_delete(section_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT textbook_id FROM textbook_sections WHERE section_id=?",
              (section_id,))
    row = c.fetchone()
    textbook_id = row["textbook_id"] if row else 0
    c.execute("UPDATE problems SET section_id=NULL WHERE section_id=?", (section_id,))
    c.execute("DELETE FROM textbook_sections WHERE section_id=?", (section_id,))
    conn.commit()
    conn.close()
    return redirect(f"/textbooks/{textbook_id}/sections")

'''

if "/textbooks" not in app_content:
    idx = app_content.rfind("if __name__")
    app_content = app_content[:idx] + textbook_routes + app_content[idx:]
    print("✅ app.pyにテキスト管理ルートを追加しました")
else:
    print("ℹ️ テキスト管理ルートはすでに存在します")

# ─── 5. app.pyのproblems関数をtextbook_id対応に更新 ──────
old_problems_get = '''    c.execute("""
        SELECT p.*, p.estimated_minutes
        FROM problems p
        ORDER BY p.problem_id DESC LIMIT 50
    """)'''

new_problems_get = '''    c.execute("""
        SELECT p.*, t.name as textbook_display,
               t.subject as textbook_subject,
               s.name as series_name
        FROM problems p
        LEFT JOIN textbooks t ON p.textbook_id = t.textbook_id
        LEFT JOIN series s ON t.series_id = s.series_id
        ORDER BY p.problem_id DESC LIMIT 50
    """)'''

if old_problems_get in app_content:
    app_content = app_content.replace(old_problems_get, new_problems_get)
    print("✅ problems関数のGETクエリを更新しました")

# problemsのPOST（登録）をtextbook_id対応に
old_problems_post = '''        subject = request.form["subject"]
        textbook = request.form["textbook"]'''

new_problems_post = '''        textbook_id = request.form.get("textbook_id")
        # textbook_idからsubjectとtextbook名を取得
        conn2 = get_connection()
        c2 = conn2.cursor()
        if textbook_id:
            c2.execute("SELECT subject, name FROM textbooks WHERE textbook_id=?",
                       (textbook_id,))
            tb_row = c2.fetchone()
            subject = tb_row["subject"] if tb_row else request.form.get("subject", "")
            textbook = tb_row["name"] if tb_row else ""
        else:
            subject = request.form.get("subject", "")
            textbook = request.form.get("textbook", "")
        conn2.close()'''

if old_problems_post in app_content:
    app_content = app_content.replace(old_problems_post, new_problems_post)
    print("✅ problems関数のPOST処理を更新しました")

# INSERT文にtextbook_idを追加
old_insert = '''        c.execute("""
            INSERT INTO problems
            (subject, textbook, problem_number, importance, difficulty,
             review_value, estimated_minutes, instruction, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            subject, textbook,
            request.form["problem_number"],
            request.form["importance"],
            request.form["difficulty"],
            request.form["review_value"],
            request.form["estimated_minutes"],
            request.form.get("instruction", ""),
            "標準"
        ))'''

new_insert = '''        c.execute("""
            INSERT INTO problems
            (subject, textbook, textbook_id, problem_number, importance, difficulty,
             review_value, estimated_minutes, instruction, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            subject, textbook, textbook_id,
            request.form["problem_number"],
            request.form["importance"],
            request.form["difficulty"],
            request.form["review_value"],
            request.form["estimated_minutes"],
            request.form.get("instruction", ""),
            "標準"
        ))'''

if old_insert in app_content:
    app_content = app_content.replace(old_insert, new_insert)
    print("✅ problems INSERT文を更新しました")

# problems関数のrender_templateにtextbooks・all_subjectsを追加
old_render = '''    return render_template("problems.html",
                           problems=problems,
                           students=students)'''

new_render = '''    # テキスト一覧と教科一覧を取得
    conn3 = get_connection()
    c3 = conn3.cursor()
    c3.execute("""
        SELECT t.textbook_id, t.name, t.subject,
               s.name as series_name
        FROM textbooks t
        LEFT JOIN series s ON t.series_id = s.series_id
        ORDER BY t.subject, s.name, t.name
    """)
    textbooks_list = c3.fetchall()
    c3.execute("SELECT DISTINCT subject FROM students ORDER BY subject")
    all_subjects_raw = c3.fetchall()
    conn3.close()
    all_subjects = []
    for row in all_subjects_raw:
        for subj in row["subject"].split(","):
            s = subj.strip()
            if s and s not in all_subjects:
                all_subjects.append(s)
    return render_template("problems.html",
                           problems=problems,
                           students=students,
                           textbooks=textbooks_list,
                           all_subjects=sorted(all_subjects))'''

if old_render in app_content:
    app_content = app_content.replace(old_render, new_render)
    print("✅ problems render_templateを更新しました")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(app_content)

# ─── 6. index.htmlを更新 ────────────────────────────────
index_html = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>学習計画管理システム</title>
  <style>
    body { font-family: sans-serif; max-width: 600px; margin: 60px auto; background: #f5f7fa; }
    h1 { color: #2c3e50; }
    .menu a {
      display: block; margin: 16px 0; padding: 18px 24px;
      background: #4472C4; color: white; text-decoration: none;
      border-radius: 8px; font-size: 18px;
    }
    .menu a:hover { background: #2c5fa8; }
    .menu a.sub {
      background: #7f8c8d; font-size: 15px;
      padding: 12px 24px; margin: -8px 0 16px 0;
    }
    .menu a.sub:hover { background: #636e72; }
  </style>
</head>
<body>
  <h1>📚 学習計画管理システム</h1>
  <div class="menu">
    <a href="/textbooks">⓪ テキスト管理</a>
    <a href="/problems">① 問題マスタ登録</a>
    <a href="/problems/list" class="sub">　└ 問題一覧・編集・削除</a>
    <a href="/record">② 授業記録入力</a>
    <a href="/record/list">③ 授業記録修正・習熟度修正</a>
    <a href="/assignments/list">④ 出題予定管理</a>
    <a href="/preview">⑤ 計画表プレビュー・出力</a>
    <a href="/schedule">⑥ 勉強時間登録（全体）</a>
    <a href="/schedule_subject">⑦ 勉強時間登録（教科別）</a>
    <a href="/students">⑧ 生徒管理</a>
    <a href="/history">⑨ 過去の計画表</a>
    <a href="/class_schedule">⑩ 授業スケジュール管理</a>
  </div>
</body>
</html>"""

with open(os.path.join(templates, "index.html"), "w", encoding="utf-8") as f:
    f.write(index_html)
print("✅ index.html を更新しました")
print("✅ Step2完了")