import os

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")

# ─── 1. problem_edit.htmlにカテゴリ選択を追加 ────────────
problem_edit_path = os.path.join(templates, "problem_edit.html")
with open(problem_edit_path, "r", encoding="utf-8") as f:
    content = f.read()

old = '''  <div class="form-box" style="margin-top:24px;">
    <h2 style="font-size:16px;color:#2c3e50;">出題予定の追加</h2>
    <form method="POST" action="/problems/assign/{{ problem.problem_id }}">
      <label>生徒</label>
      <select name="student_id" style="width:100%;padding:8px;border:1px solid #ccc;border-radius:4px;font-size:15px;box-sizing:border-box;">
        {% for s in students %}
        <option value="{{ s.student_id }}">{{ s.name }}</option>
        {% endfor %}
      </select>
      <label>予習日</label>
      <input type="date" name="scheduled_date" style="width:100%;padding:8px;margin-top:4px;border:1px solid #ccc;border-radius:4px;font-size:15px;box-sizing:border-box;" required>
      <button type="submit" style="margin-top:12px;padding:8px 20px;background:#27ae60;color:white;border:none;border-radius:6px;font-size:14px;cursor:pointer;">出題予定に追加</button>
    </form>
  </div>'''

new = '''  <div class="form-box" style="margin-top:24px;">
    <h2 style="font-size:16px;color:#2c3e50;">出題予定の追加</h2>
    <form method="POST" action="/problems/assign/{{ problem.problem_id }}">
      <label>生徒</label>
      <select name="student_id" style="width:100%;padding:8px;border:1px solid #ccc;border-radius:4px;font-size:15px;box-sizing:border-box;">
        {% for s in students %}
        <option value="{{ s.student_id }}">{{ s.name }}</option>
        {% endfor %}
      </select>
      <label>出題区分</label>
      <select name="category" style="width:100%;padding:8px;margin-top:4px;border:1px solid #ccc;border-radius:4px;font-size:15px;box-sizing:border-box;">
        <option value="予習">予習</option>
        <option value="復習">復習</option>
        <option value="定着">定着</option>
        <option value="再定着">再定着</option>
      </select>
      <label>出題日（任意）</label>
      <input type="date" name="scheduled_date" style="width:100%;padding:8px;margin-top:4px;border:1px solid #ccc;border-radius:4px;font-size:15px;box-sizing:border-box;">
      <p style="font-size:12px;color:#888;margin-top:4px;">空欄の場合は出題日未定として登録されます。</p>
      <button type="submit" style="margin-top:12px;padding:8px 20px;background:#27ae60;color:white;border:none;border-radius:6px;font-size:14px;cursor:pointer;">出題予定に追加</button>
    </form>
  </div>'''

if old in content:
    content = content.replace(old, new)
    with open(problem_edit_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ problem_edit.html を修正しました")
else:
    print("❌ problem_edit.htmlの対象箇所が見つかりません")

# ─── 2. app.pyのproblem_assignを修正（カテゴリ・日付任意対応）──
app_path = os.path.join(base, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

old_assign = '''@app.route("/problems/assign/<int:problem_id>", methods=["POST"])
def problem_assign(problem_id):
    student_id = request.form["student_id"]
    scheduled_date = request.form["scheduled_date"]
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
        VALUES (?, ?, ?, ?)
    """, (student_id, problem_id, scheduled_date, "予習"))
    conn.commit()
    conn.close()
    return redirect(f"/problems/edit/{problem_id}")'''

new_assign = '''@app.route("/problems/assign/<int:problem_id>", methods=["POST"])
def problem_assign(problem_id):
    student_id = request.form["student_id"]
    scheduled_date = request.form.get("scheduled_date", "").strip()
    category = request.form.get("category", "予習")
    conn = get_connection()
    c = conn.cursor()
    if scheduled_date:
        c.execute("""
            INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
            VALUES (?, ?, ?, ?)
        """, (student_id, problem_id, scheduled_date, category))
    else:
        # 日付未定の場合は遠い未来日付で仮登録（計画表には出ないが一覧には表示）
        c.execute("""
            INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
            VALUES (?, ?, ?, ?)
        """, (student_id, problem_id, "2099-12-31", category))
    conn.commit()
    conn.close()
    return redirect(f"/problems/edit/{problem_id}")'''

if old_assign in app_content:
    app_content = app_content.replace(old_assign, new_assign)
    print("✅ problem_assign関数を修正しました")
else:
    print("❌ problem_assign関数が見つかりません")

# ─── 3. MCPのadd_assignmentも同様に修正 ─────────────────
mcp_path = os.path.join(base, "mcp_server.py")
with open(mcp_path, "r", encoding="utf-8") as f:
    mcp_content = f.read()

old_mcp_assign = '''    elif name == "add_assignment":
        student_id = arguments["student_id"]
        problem_id = arguments["problem_id"]
        scheduled_date = arguments["scheduled_date"]
        category = arguments.get("category", "予習")
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
            VALUES (?, ?, ?, ?)
        """, (student_id, problem_id, scheduled_date, category))
        conn.commit()
        conn.close()
        return [TextContent(type="text",
            text=f"問題ID {problem_id} を {student_id} の出題予定（{scheduled_date}・{category}）に追加しました")]'''

new_mcp_assign = '''    elif name == "add_assignment":
        student_id = arguments["student_id"]
        problem_id = arguments["problem_id"]
        scheduled_date = arguments.get("scheduled_date", "").strip()
        category = arguments.get("category", "予習")
        if not scheduled_date:
            scheduled_date = "2099-12-31"
        conn = get_connection()
        c = conn.cursor()
        # 既存の出題予定があれば更新、なければ追加
        c.execute("SELECT assignment_id FROM assignments WHERE student_id=? AND problem_id=?",
                  (student_id, problem_id))
        existing = c.fetchone()
        if existing:
            c.execute("""
                UPDATE assignments SET scheduled_date=?, category=?
                WHERE student_id=? AND problem_id=?
            """, (scheduled_date, category, student_id, problem_id))
            msg = f"問題ID {problem_id} の出題予定を更新しました（{scheduled_date}・{category}）"
        else:
            c.execute("""
                INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
                VALUES (?, ?, ?, ?)
            """, (student_id, problem_id, scheduled_date, category))
            msg = f"問題ID {problem_id} を {student_id} の出題予定に追加しました（{scheduled_date}・{category}）"
        conn.commit()
        conn.close()
        return [TextContent(type="text", text=msg)]'''

if old_mcp_assign in mcp_content:
    mcp_content = mcp_content.replace(old_mcp_assign, new_mcp_assign)
    with open(mcp_path, "w", encoding="utf-8") as f:
        f.write(mcp_content)
    print("✅ mcp_server.py を修正しました")
else:
    print("❌ add_assignmentが見つかりません")

# ─── 4. get_plan_v2で2099年の問題を除外する ─────────────
db_path = os.path.join(base, "database.py")
with open(db_path, "r", encoding="utf-8") as f:
    db_content = f.read()

old_query = '''    c.execute("""
        SELECT a.*, p.subject, p.textbook, p.problem_number,
               p.importance, p.difficulty, p.review_value,
               p.estimated_minutes, p.instruction,
               (SELECT mastery FROM history h
                WHERE h.student_id = a.student_id AND h.problem_id = a.problem_id
                ORDER BY h.date DESC LIMIT 1) as mastery,
               (SELECT date FROM history h
                WHERE h.student_id = a.student_id AND h.problem_id = a.problem_id
                ORDER BY h.date DESC LIMIT 1) as last_date
        FROM assignments a
        JOIN problems p ON a.problem_id = p.problem_id
        WHERE a.student_id = ? AND a.scheduled_date <= ?
        ORDER BY p.review_value DESC, p.importance DESC
    """, (student_id, end_date_str))'''

new_query = '''    c.execute("""
        SELECT a.*, p.subject, p.textbook, p.problem_number,
               p.importance, p.difficulty, p.review_value,
               p.estimated_minutes, p.instruction,
               (SELECT mastery FROM history h
                WHERE h.student_id = a.student_id AND h.problem_id = a.problem_id
                ORDER BY h.date DESC LIMIT 1) as mastery,
               (SELECT date FROM history h
                WHERE h.student_id = a.student_id AND h.problem_id = a.problem_id
                ORDER BY h.date DESC LIMIT 1) as last_date
        FROM assignments a
        JOIN problems p ON a.problem_id = p.problem_id
        WHERE a.student_id = ?
          AND a.scheduled_date <= ?
          AND a.scheduled_date != '2099-12-31'
        ORDER BY p.review_value DESC, p.importance DESC
    """, (student_id, end_date_str))'''

if old_query in db_content:
    db_content = db_content.replace(old_query, new_query)
    with open(db_path, "w", encoding="utf-8") as f:
        f.write(db_content)
    print("✅ database.py を修正しました（2099年除外）")
else:
    print("❌ get_plan_v2のクエリが見つかりません")

# ─── 5. assignments_list.htmlで2099年を「未定」と表示 ────
assignments_list_path = os.path.join(templates, "assignments_list.html")
with open(assignments_list_path, "r", encoding="utf-8") as f:
    al_content = f.read()

old_date_td = '''      <td>{{ a.scheduled_date }}</td>'''
new_date_td = '''      <td>{{ "未定" if a.scheduled_date == "2099-12-31" else a.scheduled_date }}</td>'''

if old_date_td in al_content:
    al_content = al_content.replace(old_date_td, new_date_td)
    with open(assignments_list_path, "w", encoding="utf-8") as f:
        f.write(al_content)
    print("✅ assignments_list.html を修正しました")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(app_content)

print("✅ 全て完了")