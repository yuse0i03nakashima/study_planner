import os

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")

# ─── 1. mcp_server.pyを更新 ────────────────────────────
mcp_path = os.path.join(base, "mcp_server.py")
with open(mcp_path, "r", encoding="utf-8") as f:
    mcp_content = f.read()

# add_problemのdescriptionとinputSchemaを更新
old_add_problem = '''        Tool(
            name="add_problem",
            description="問題マスタに新しい問題を登録する。student_idsとscheduled_dateは任意。",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "description": "教科"},
                    "textbook": {"type": "string", "description": "テキスト名"},
                    "problem_number": {"type": "string", "description": "問題番号・名称"},
                    "importance": {"type": "integer", "description": "重要度（1〜5）"},
                    "difficulty": {"type": "integer", "description": "難易度（1〜5）"},
                    "review_value": {"type": "integer", "description": "復習価値（1〜5）"},
                    "estimated_minutes": {"type": "integer", "description": "所要時間（分・5分単位）"},
                    "instruction": {"type": "string", "description": "学習指示（任意）"},
                    "student_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "出題する生徒IDのリスト（任意）"
                    },
                    "scheduled_date": {"type": "string", "description": "予習日（YYYY-MM-DD形式・任意）"}
                },
                "required": ["subject", "textbook", "problem_number", "importance",
                             "difficulty", "review_value", "estimated_minutes"]
            }
        ),'''

new_add_problem = '''        Tool(
            name="add_problem",
            description="問題マスタに新しい問題を登録する。student_ids・scheduled_date・categoryは任意。categoryは予習/復習/定着/再定着を指定可能（省略時は予習）。",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "description": "教科"},
                    "textbook": {"type": "string", "description": "テキスト名"},
                    "problem_number": {"type": "string", "description": "問題番号・名称"},
                    "importance": {"type": "integer", "description": "重要度（1〜5）"},
                    "difficulty": {"type": "integer", "description": "難易度（1〜5）"},
                    "review_value": {"type": "integer", "description": "復習価値（1〜5）"},
                    "estimated_minutes": {"type": "integer", "description": "所要時間（分・5分単位）"},
                    "instruction": {"type": "string", "description": "学習指示（任意）"},
                    "student_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "出題する生徒IDのリスト（任意）"
                    },
                    "scheduled_date": {"type": "string", "description": "出題日（YYYY-MM-DD形式・任意）"},
                    "category": {"type": "string", "description": "出題区分：予習/復習/定着/再定着（省略時は予習）"}
                },
                "required": ["subject", "textbook", "problem_number", "importance",
                             "difficulty", "review_value", "estimated_minutes"]
            }
        ),'''

mcp_content = mcp_content.replace(old_add_problem, new_add_problem)

# add_problemの実装を更新（categoryを反映）
old_add_impl = '''        student_ids = arguments.get("student_ids", [])
        scheduled_date = arguments.get("scheduled_date", "")
        if scheduled_date and student_ids:
            for sid in student_ids:
                c.execute("""
                    INSERT INTO assignments
                    (student_id, problem_id, scheduled_date, category)
                    VALUES (?, ?, ?, ?)
                """, (sid, problem_id, scheduled_date, "予習"))'''

new_add_impl = '''        student_ids = arguments.get("student_ids", [])
        scheduled_date = arguments.get("scheduled_date", "")
        category = arguments.get("category", "予習")
        if scheduled_date and student_ids:
            for sid in student_ids:
                c.execute("""
                    INSERT INTO assignments
                    (student_id, problem_id, scheduled_date, category)
                    VALUES (?, ?, ?, ?)
                """, (sid, problem_id, scheduled_date, category))'''

mcp_content = mcp_content.replace(old_add_impl, new_add_impl)

# update_assignment_categoryツールを追加
old_update_assignment = '''        Tool(
            name="update_assignment_date",'''

new_tools = '''        Tool(
            name="update_assignment_category",
            description="出題予定のカテゴリ（予習/復習/定着/再定着）を変更する。誤った計画を修正する際に使用。",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"},
                    "problem_id": {"type": "integer", "description": "問題ID"},
                    "category": {"type": "string", "description": "新しいカテゴリ（予習/復習/定着/再定着）"}
                },
                "required": ["student_id", "problem_id", "category"]
            }
        ),
        Tool(
            name="update_mastery",
            description="生徒の問題に対する習熟度を手動で修正する。誤った記録の修正や手動調整に使用。mastery: 1=要定着、2=定着中、3=定着済",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"},
                    "problem_id": {"type": "integer", "description": "問題ID"},
                    "mastery": {"type": "integer", "description": "新しい習熟度（1〜3）"},
                    "update_assignment": {"type": "boolean", "description": "出題予定のカテゴリも自動更新するか（省略時true）"}
                },
                "required": ["student_id", "problem_id", "mastery"]
            }
        ),
        Tool(
            name="update_assignment_date",'''

mcp_content = mcp_content.replace(old_update_assignment, new_tools)

# update_assignment_categoryとupdate_masteryの実装を追加
old_update_date_impl = '''    elif name == "update_assignment_date":'''

new_impls = '''    elif name == "update_assignment_category":
        student_id = arguments["student_id"]
        problem_id = arguments["problem_id"]
        category = arguments["category"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            UPDATE assignments SET category=?
            WHERE student_id=? AND problem_id=?
        """, (category, student_id, problem_id))
        updated = c.rowcount
        conn.commit()
        conn.close()
        if updated:
            return [TextContent(type="text",
                text=f"問題ID {problem_id} のカテゴリを「{category}」に変更しました")]
        else:
            return [TextContent(type="text",
                text=f"対象の出題予定が見つかりません")]

    elif name == "update_mastery":
        from database import get_next_date
        student_id = arguments["student_id"]
        problem_id = arguments["problem_id"]
        new_mastery = arguments["mastery"]
        update_assignment = arguments.get("update_assignment", True)
        today = date.today().isoformat()

        conn = get_connection()
        c = conn.cursor()

        # historyテーブルの最新レコードを更新
        c.execute("""
            SELECT history_id FROM history
            WHERE student_id=? AND problem_id=?
            ORDER BY date DESC LIMIT 1
        """, (student_id, problem_id))
        row = c.fetchone()
        if row:
            c.execute("UPDATE history SET mastery=? WHERE history_id=?",
                      (new_mastery, row["history_id"]))
        else:
            # 履歴がない場合は新規作成
            c.execute("""
                INSERT INTO history (student_id, problem_id, date, correct, mastery, category)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (student_id, problem_id, today, 1, new_mastery, "手動修正"))

        # 出題予定のカテゴリと日付も更新
        if update_assignment:
            c.execute("SELECT review_value FROM problems WHERE problem_id=?",
                      (problem_id,))
            p_row = c.fetchone()
            if p_row:
                review_value = p_row["review_value"]
                next_date = get_next_date(review_value, new_mastery, today)
                category = {1: "復習", 2: "定着"}.get(new_mastery, "再定着")
                c.execute("DELETE FROM assignments WHERE student_id=? AND problem_id=?",
                          (student_id, problem_id))
                c.execute("""
                    INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
                    VALUES (?, ?, ?, ?)
                """, (student_id, problem_id, next_date.isoformat(), category))

        conn.commit()
        conn.close()
        stars = "★" * new_mastery
        return [TextContent(type="text",
            text=f"問題ID {problem_id} の習熟度を {stars} に修正しました（カテゴリ・次回出題日も更新）")]

    elif name == "update_assignment_date":'''

mcp_content = mcp_content.replace(old_update_date_impl, new_impls)

with open(mcp_path, "w", encoding="utf-8") as f:
    f.write(mcp_content)
print("✅ mcp_server.py を更新しました")

# ─── 2. app.pyを更新 ────────────────────────────────────
app_path = os.path.join(base, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

# problems関数のカテゴリ対応
old_problems_impl = '''        problem_id = c.lastrowid
        student_ids = request.form.getlist("student_ids")
        scheduled_date = request.form.get("scheduled_date", "").strip()
        if scheduled_date and student_ids:
            for sid in student_ids:
                c.execute("""
                    INSERT INTO assignments
                    (student_id, problem_id, scheduled_date, category)
                    VALUES (?, ?, ?, ?)
                """, (sid, problem_id, scheduled_date, "予習"))'''

new_problems_impl = '''        problem_id = c.lastrowid
        student_ids = request.form.getlist("student_ids")
        scheduled_date = request.form.get("scheduled_date", "").strip()
        category = request.form.get("category", "予習")
        if scheduled_date and student_ids:
            for sid in student_ids:
                c.execute("""
                    INSERT INTO assignments
                    (student_id, problem_id, scheduled_date, category)
                    VALUES (?, ?, ?, ?)
                """, (sid, problem_id, scheduled_date, category))'''

app_content = app_content.replace(old_problems_impl, new_problems_impl)

# record/listに習熟度修正機能を追加
mastery_route = '''
@app.route("/mastery/edit/<int:history_id>", methods=["POST"])
def mastery_edit(history_id):
    new_mastery = int(request.form["mastery"])
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT student_id, problem_id, date FROM history "
              "WHERE history_id=?", (history_id,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE history SET mastery=? WHERE history_id=?",
                  (new_mastery, history_id))
        conn.commit()
    conn.close()
    return redirect("/record/list")


@app.route("/assignment/category/<int:student_id_dummy>", methods=["POST"])
def assignment_category_edit():
    pass


@app.route("/assignments/list")
def assignments_list():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()
    student_id = request.args.get(
        "student_id", students[0]["student_id"] if students else None)
    assignments = []
    if student_id:
        c.execute("""
            SELECT a.assignment_id, a.category, a.scheduled_date,
                   p.problem_id, p.subject, p.textbook, p.problem_number,
                   p.importance, p.review_value,
                   (SELECT mastery FROM history h
                    WHERE h.student_id = a.student_id
                    AND h.problem_id = a.problem_id
                    ORDER BY h.date DESC LIMIT 1) as mastery
            FROM assignments a
            JOIN problems p ON a.problem_id = p.problem_id
            WHERE a.student_id = ?
            ORDER BY a.scheduled_date, p.subject
        """, (student_id,))
        assignments = c.fetchall()
    conn.close()
    return render_template("assignments_list.html",
                           students=students,
                           assignments=assignments,
                           selected_student=student_id)


@app.route("/assignments/update", methods=["POST"])
def assignment_update():
    assignment_id = int(request.form["assignment_id"])
    category = request.form.get("category", "")
    scheduled_date = request.form.get("scheduled_date", "")
    conn = get_connection()
    c = conn.cursor()
    if category and scheduled_date:
        c.execute("UPDATE assignments SET category=?, scheduled_date=? "
                  "WHERE assignment_id=?",
                  (category, scheduled_date, assignment_id))
    elif category:
        c.execute("UPDATE assignments SET category=? WHERE assignment_id=?",
                  (category, assignment_id))
    elif scheduled_date:
        c.execute("UPDATE assignments SET scheduled_date=? "
                  "WHERE assignment_id=?",
                  (scheduled_date, assignment_id))
    conn.commit()
    conn.close()
    student_id = request.form.get("student_id", "")
    return redirect(f"/assignments/list?student_id={student_id}")


@app.route("/assignments/delete/<int:assignment_id>", methods=["POST"])
def assignment_delete(assignment_id):
    student_id = request.form.get("student_id", "")
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM assignments WHERE assignment_id=?", (assignment_id,))
    conn.commit()
    conn.close()
    return redirect(f"/assignments/list?student_id={student_id}")

'''

if "/assignments/list" not in app_content:
    idx = app_content.rfind("if __name__")
    app_content = app_content[:idx] + mastery_route + app_content[idx:]

with open(app_path, "w", encoding="utf-8") as f:
    f.write(app_content)
print("✅ app.py を更新しました")

# ─── 3. problems.htmlにカテゴリ選択を追加 ───────────────
problems_html_path = os.path.join(templates, "problems.html")
with open(problems_html_path, "r", encoding="utf-8") as f:
    html = f.read()

old_date = '''      <label>予習日（任意・未定の場合は空欄でよい）</label>
      <input type="date" name="scheduled_date">
      <p style="font-size:12px;color:#888;margin-top:4px;">
        空欄の場合は問題マスタのみに登録されます。後から「問題一覧・編集」で予習日を設定できます。
      </p>
      <button type="submit">登録する</button>'''

new_date = '''      <div class="row2">
        <div>
          <label>出題区分</label>
          <select name="category">
            <option value="予習" selected>予習</option>
            <option value="復習">復習</option>
            <option value="定着">定着</option>
            <option value="再定着">再定着</option>
          </select>
        </div>
        <div>
          <label>出題日（任意・未定の場合は空欄）</label>
          <input type="date" name="scheduled_date">
        </div>
      </div>
      <p style="font-size:12px;color:#888;margin-top:4px;">
        空欄の場合は問題マスタのみに登録されます。後から「出題予定管理」で日付を設定できます。
      </p>
      <button type="submit">登録する</button>'''

html = html.replace(old_date, new_date)
with open(problems_html_path, "w", encoding="utf-8") as f:
    f.write(html)
print("✅ problems.html を更新しました")

# ─── 4. assignments_list.html を新規作成 ────────────────
assignments_list_html = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>出題予定管理</title>
  <style>
    body { font-family: sans-serif; max-width: 1100px; margin: 40px auto; background: #f5f7fa; }
    h1 { color: #2c3e50; }
    .filter-box { background: white; padding: 16px 24px; border-radius: 8px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    select, input[type="date"] { padding: 7px; border: 1px solid #ccc; border-radius: 4px; font-size: 14px; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); font-size: 12px; }
    th { background: #4472C4; color: white; padding: 8px; white-space: nowrap; }
    td { padding: 6px 8px; border-bottom: 1px solid #eee; text-align: center; vertical-align: middle; }
    .cat-予習  { background: #DDEEFF; }
    .cat-復習  { background: #DDFFDD; }
    .cat-定着  { background: #FFFADD; }
    .cat-再定着 { background: #FFE5DD; }
    .btn-save { padding: 3px 10px; background: #4472C4; color: white; border: none; border-radius: 4px; font-size: 11px; cursor: pointer; }
    .btn-del { padding: 3px 10px; background: #e74c3c; color: white; border: none; border-radius: 4px; font-size: 11px; cursor: pointer; }
    a { color: #4472C4; }
    .count { color: #555; font-size: 13px; margin-bottom: 8px; }
  </style>
</head>
<body>
  <h1>⑨ 出題予定管理</h1>

  <div class="filter-box">
    <form method="GET">
      <label style="font-weight:bold;">生徒：</label>
      <select name="student_id" onchange="this.form.submit()">
        {% for s in students %}
        <option value="{{ s.student_id }}"
          {% if s.student_id == selected_student %}selected{% endif %}>
          {{ s.name }}
        </option>
        {% endfor %}
      </select>
    </form>
  </div>

  <p class="count">{{ assignments | length }} 件</p>

  <table>
    <tr>
      <th>教科</th><th>テキスト名</th><th>問題番号</th>
      <th>重要度</th><th>復習価値</th><th>習熟度</th>
      <th>出題区分</th><th>出題日</th><th>操作</th>
    </tr>
    {% for a in assignments %}
    <tr class="cat-{{ a.category }}">
      <td>{{ a.subject }}</td>
      <td>{{ a.textbook }}</td>
      <td>{{ a.problem_number }}</td>
      <td>{{ a.importance }}</td>
      <td>{{ a.review_value }}</td>
      <td>{{ "★" * (a.mastery or 1) }}</td>
      <td>
        <form method="POST" action="/assignments/update" style="display:inline;">
          <input type="hidden" name="assignment_id" value="{{ a.assignment_id }}">
          <input type="hidden" name="student_id" value="{{ selected_student }}">
          <select name="category" style="font-size:11px;padding:2px;">
            {% for cat in ["予習","復習","定着","再定着"] %}
            <option value="{{ cat }}" {% if cat == a.category %}selected{% endif %}>{{ cat }}</option>
            {% endfor %}
          </select>
          <input type="date" name="scheduled_date"
            value="{{ a.scheduled_date }}"
            style="font-size:11px;padding:2px;">
          <button type="submit" class="btn-save">更新</button>
        </form>
      </td>
      <td>{{ a.scheduled_date }}</td>
      <td>
        <form method="POST" action="/assignments/delete/{{ a.assignment_id }}"
              style="display:inline"
              onsubmit="return confirm('この出題予定を削除しますか？')">
          <input type="hidden" name="student_id" value="{{ selected_student }}">
          <button class="btn-del">削除</button>
        </form>
      </td>
    </tr>
    {% endfor %}
  </table>
  <p><a href="/">← トップに戻る</a></p>
</body>
</html>"""

with open(os.path.join(templates, "assignments_list.html"), "w", encoding="utf-8") as f:
    f.write(assignments_list_html)
print("✅ assignments_list.html を作成しました")

# ─── 5. record_list.htmlに習熟度修正を追加 ──────────────
record_list_path = os.path.join(templates, "record_list.html")
with open(record_list_path, "r", encoding="utf-8") as f:
    rl = f.read()

old_mastery_td = '''      <td>{{ "★" * r.mastery }}</td>'''
new_mastery_td = '''      <td>
        <form method="POST" action="/mastery/edit/{{ r.history_id }}"
              style="display:inline;">
          <select name="mastery" style="font-size:11px;padding:2px;width:60px;">
            {% for m in [1,2,3] %}
            <option value="{{ m }}" {% if m == r.mastery %}selected{% endif %}>
              {{ "★" * m }}
            </option>
            {% endfor %}
          </select>
          <button type="submit" style="padding:2px 6px;background:#4472C4;color:white;border:none;border-radius:3px;font-size:10px;cursor:pointer;">修正</button>
        </form>
      </td>'''

if old_mastery_td in rl:
    rl = rl.replace(old_mastery_td, new_mastery_td)
    with open(record_list_path, "w", encoding="utf-8") as f:
        f.write(rl)
    print("✅ record_list.html を更新しました")
else:
    print("❌ record_list.htmlの対象箇所が見つかりません")

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
    <a href="/problems">① 問題マスタ登録</a>
    <a href="/problems/list" class="sub">　└ 問題一覧・編集・削除</a>
    <a href="/record">② 授業記録入力</a>
    <a href="/record/list">③ 授業記録修正・習熟度修正</a>
    <a href="/assignments/list">④ 出題予定管理（カテゴリ・日付変更）</a>
    <a href="/preview">⑤ 計画表プレビュー・出力</a>
    <a href="/schedule">⑥ 勉強時間登録</a>
    <a href="/students">⑦ 生徒管理</a>
    <a href="/history">⑧ 過去の計画表</a>
    <a href="/class_schedule">⑨ 授業スケジュール管理</a>
  </div>
</body>
</html>"""

with open(os.path.join(templates, "index.html"), "w", encoding="utf-8") as f:
    f.write(index_html)
print("✅ index.html を更新しました")
print("✅ 全て完了")