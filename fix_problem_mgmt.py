import os

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")

# ─── mcp_server.pyのupdate_review_valueをupdate_problemに拡張 ───
mcp_path = os.path.join(base, "mcp_server.py")
with open(mcp_path, "r", encoding="utf-8") as f:
    mcp_content = f.read()

old_tool = '''        Tool(
            name="update_review_value",
            description="問題の復習価値を更新する",
            inputSchema={
                "type": "object",
                "properties": {
                    "problem_id": {"type": "integer", "description": "問題ID"},
                    "review_value": {"type": "integer", "description": "新しい復習価値（1〜5）"}
                },
                "required": ["problem_id", "review_value"]
            }
        ),'''

new_tool = '''        Tool(
            name="update_review_value",
            description="問題の復習価値を更新する",
            inputSchema={
                "type": "object",
                "properties": {
                    "problem_id": {"type": "integer", "description": "問題ID"},
                    "review_value": {"type": "integer", "description": "新しい復習価値（1〜5）"}
                },
                "required": ["problem_id", "review_value"]
            }
        ),
        Tool(
            name="update_problem",
            description="問題マスタの情報を更新する。問題番号・難易度・重要度・復習価値・所要時間・学習指示を変更できる。",
            inputSchema={
                "type": "object",
                "properties": {
                    "problem_id": {"type": "integer", "description": "問題ID"},
                    "problem_number": {"type": "string", "description": "問題番号・名称（任意）"},
                    "importance": {"type": "integer", "description": "重要度（1〜5）（任意）"},
                    "difficulty": {"type": "integer", "description": "難易度（1〜5）（任意）"},
                    "review_value": {"type": "integer", "description": "復習価値（1〜5）（任意）"},
                    "estimated_minutes": {"type": "integer", "description": "所要時間（分・5分単位）（任意）"},
                    "instruction": {"type": "string", "description": "学習指示（任意）"}
                },
                "required": ["problem_id"]
            }
        ),'''

mcp_content = mcp_content.replace(old_tool, new_tool)

old_impl = '''    elif name == "update_review_value":
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE problems SET review_value=? WHERE problem_id=?",
                  (arguments["review_value"], arguments["problem_id"]))
        conn.commit()
        conn.close()
        return [TextContent(type="text",
            text=f"問題ID {arguments['problem_id']} の復習価値を {arguments['review_value']} に更新しました")]'''

new_impl = '''    elif name == "update_review_value":
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE problems SET review_value=? WHERE problem_id=?",
                  (arguments["review_value"], arguments["problem_id"]))
        conn.commit()
        conn.close()
        return [TextContent(type="text",
            text=f"問題ID {arguments['problem_id']} の復習価値を {arguments['review_value']} に更新しました")]

    elif name == "update_problem":
        problem_id = arguments["problem_id"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM problems WHERE problem_id=?", (problem_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return [TextContent(type="text", text=f"問題ID {problem_id} が見つかりません")]
        fields = []
        values = []
        for key in ["problem_number", "importance", "difficulty",
                    "review_value", "estimated_minutes", "instruction"]:
            if key in arguments and arguments[key] is not None:
                fields.append(f"{key}=?")
                values.append(arguments[key])
        if not fields:
            conn.close()
            return [TextContent(type="text", text="更新する項目がありません")]
        values.append(problem_id)
        c.execute(f"UPDATE problems SET {', '.join(fields)} WHERE problem_id=?", values)
        conn.commit()
        conn.close()
        updated = ", ".join(fields)
        return [TextContent(type="text", text=f"問題ID {problem_id} を更新しました（{updated}）")]'''

mcp_content = mcp_content.replace(old_impl, new_impl)

with open(mcp_path, "w", encoding="utf-8") as f:
    f.write(mcp_content)
print("✅ mcp_server.py を更新しました")

# ─── app.pyに問題一覧ページのルートを追加 ──────────────
app_path = os.path.join(base, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

problem_list_route = '''
@app.route("/problems/list")
def problems_list():
    conn = get_connection()
    c = conn.cursor()
    student_id = request.args.get("student_id", "")
    subject = request.args.get("subject", "")
    keyword = request.args.get("keyword", "")

    query = "SELECT * FROM problems WHERE 1=1"
    params = []

    if student_id:
        query = """SELECT DISTINCT p.* FROM problems p
                   JOIN assignments a ON p.problem_id = a.problem_id
                   WHERE a.student_id = ?"""
        params.append(student_id)
        if subject:
            query += " AND p.subject=?"
            params.append(subject)
        if keyword:
            query += " AND (p.textbook LIKE ? OR p.problem_number LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
    else:
        if subject:
            query += " AND subject=?"
            params.append(subject)
        if keyword:
            query += " AND (textbook LIKE ? OR problem_number LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])

    query += " ORDER BY problem_id DESC"
    c.execute(query, params)
    problems = c.fetchall()

    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()

    c.execute("SELECT DISTINCT subject FROM problems ORDER BY subject")
    subjects = [row["subject"] for row in c.fetchall()]
    conn.close()

    return render_template("problems_list.html",
                           problems=problems,
                           students=students,
                           subjects=subjects,
                           selected_student=student_id,
                           selected_subject=subject,
                           keyword=keyword)

'''

if "/problems/list" not in app_content:
    idx = app_content.rfind("if __name__")
    app_content = app_content[:idx] + problem_list_route + app_content[idx:]
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app_content)
    print("✅ app.py に問題一覧ルートを追加しました")
else:
    print("ℹ️ 問題一覧ルートはすでに存在します")

# ─── problems_list.html を新規作成 ─────────────────────
problems_list_html = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>問題一覧</title>
  <style>
    body { font-family: sans-serif; max-width: 1100px; margin: 40px auto; background: #f5f7fa; }
    h1 { color: #2c3e50; }
    .filter-box { background: white; padding: 16px 24px; border-radius: 8px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end; }
    .filter-box label { font-weight: bold; font-size: 13px; display: block; margin-bottom: 4px; }
    .filter-box select, .filter-box input[type="text"] { padding: 7px; border: 1px solid #ccc; border-radius: 4px; font-size: 14px; }
    .filter-box button { padding: 8px 20px; background: #4472C4; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
    .filter-box button:hover { background: #2c5fa8; }
    .count { color: #555; font-size: 13px; margin-bottom: 8px; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); font-size: 12px; }
    th { background: #4472C4; color: white; padding: 8px; white-space: nowrap; }
    td { padding: 6px 8px; border-bottom: 1px solid #eee; text-align: center; vertical-align: top; }
    td.left { text-align: left; }
    .btn-edit { padding: 3px 10px; background: #4472C4; color: white; border-radius: 4px; text-decoration: none; font-size: 11px; margin-right: 2px; }
    .btn-edit:hover { background: #2c5fa8; }
    .btn-del { padding: 3px 10px; background: #e74c3c; color: white; border: none; border-radius: 4px; font-size: 11px; cursor: pointer; }
    .btn-del:hover { background: #c0392b; }
    a.back { color: #4472C4; }
  </style>
</head>
<body>
  <h1>問題一覧・編集</h1>

  <div class="filter-box">
    <form method="GET" style="display:flex; gap:12px; flex-wrap:wrap; align-items:flex-end;">
      <div>
        <label>生徒で絞り込み</label>
        <select name="student_id" onchange="this.form.submit()">
          <option value="">全問題</option>
          {% for s in students %}
          <option value="{{ s.student_id }}"
            {% if s.student_id == selected_student %}selected{% endif %}>
            {{ s.name }}
          </option>
          {% endfor %}
        </select>
      </div>
      <div>
        <label>教科で絞り込み</label>
        <select name="subject" onchange="this.form.submit()">
          <option value="">全教科</option>
          {% for sub in subjects %}
          <option value="{{ sub }}"
            {% if sub == selected_subject %}selected{% endif %}>
            {{ sub }}
          </option>
          {% endfor %}
        </select>
      </div>
      <div>
        <label>キーワード検索</label>
        <input type="text" name="keyword" value="{{ keyword }}" placeholder="テキスト名・問題番号">
      </div>
      <button type="submit">検索</button>
    </form>
  </div>

  <p class="count">{{ problems | length }} 件</p>

  <table>
    <tr>
      <th>ID</th><th>教科</th><th>テキスト名</th><th>問題番号</th>
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
      <td class="left" style="max-width:200px; font-size:11px;">{{ p.instruction or "―" }}</td>
      <td style="white-space:nowrap;">
        <a class="btn-edit" href="/problems/edit/{{ p.problem_id }}">編集</a>
        <button class="btn-del"
          onclick="deleteProblem({{ p.problem_id }}, this)">削除</button>
      </td>
    </tr>
    {% endfor %}
  </table>

  <p><a class="back" href="/problems">← 問題マスタ登録に戻る</a>　<a class="back" href="/">← トップに戻る</a></p>

  <script>
    async function deleteProblem(problemId, btn) {
      if (!confirm('問題ID ' + problemId + ' を削除しますか？関連する授業記録・出題予定も削除されます。')) return;
      try {
        const res = await fetch('/problems/delete/' + problemId, {method: 'POST'});
        if (res.ok) {
          const row = document.getElementById('row-' + problemId);
          if (row) row.remove();
        } else {
          alert('削除に失敗しました。');
        }
      } catch(e) {
        alert('削除に失敗しました: ' + e);
      }
    }
  </script>
</body>
</html>"""

with open(os.path.join(templates, "problems_list.html"), "w", encoding="utf-8") as f:
    f.write(problems_list_html)
print("✅ problems_list.html を作成しました")

# ─── index.htmlに問題一覧リンクを追加 ──────────────────
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
      background: #7f8c8d; font-size: 15px; padding: 12px 24px; margin: -8px 0 16px 0;
    }
    .menu a.sub:hover { background: #636e72; }
  </style>
</head>
<body>
  <h1>📚 学習計画管理システム</h1>
  <div class="menu">
    <a href="/problems">① 問題マスタ登録</a>
    <a href="/problems/list" class="sub">　└ 問題一覧・編集・削除</a>
    <a href="/record">② 授業記録入力</a>
    <a href="/record/list">③ 授業記録修正</a>
    <a href="/preview">④ 計画表プレビュー・出力</a>
    <a href="/schedule">⑤ 勉強時間登録</a>
    <a href="/students">⑥ 生徒管理</a>
    <a href="/history">⑦ 過去の計画表</a>
  </div>
</body>
</html>"""

with open(os.path.join(templates, "index.html"), "w", encoding="utf-8") as f:
    f.write(index_html)
print("✅ index.html を更新しました")
print("✅ 全て完了")