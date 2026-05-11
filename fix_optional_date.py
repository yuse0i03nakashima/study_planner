import os

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")

# ─── app.pyのproblems関数を修正 ────────────────────────
app_path = os.path.join(base, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

old = '''        problem_id = c.lastrowid
        student_ids = request.form.getlist("student_ids")
        scheduled_date = request.form["scheduled_date"]
        for sid in student_ids:
            c.execute("""
                INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
                VALUES (?, ?, ?, ?)
            """, (sid, problem_id, scheduled_date, "予習"))
        conn.commit()
        conn.close()
        return redirect("/problems")'''

new = '''        problem_id = c.lastrowid
        student_ids = request.form.getlist("student_ids")
        scheduled_date = request.form.get("scheduled_date", "").strip()
        if scheduled_date and student_ids:
            for sid in student_ids:
                c.execute("""
                    INSERT INTO assignments
                    (student_id, problem_id, scheduled_date, category)
                    VALUES (?, ?, ?, ?)
                """, (sid, problem_id, scheduled_date, "予習"))
        conn.commit()
        conn.close()
        return redirect("/problems")'''

if old in app_content:
    app_content = app_content.replace(old, new)
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app_content)
    print("✅ app.py を修正しました")
else:
    print("❌ 対象箇所が見つかりません")

# ─── problems.htmlの予習日を任意に変更 ─────────────────
problems_html_path = os.path.join(templates, "problems.html")
with open(problems_html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

old_html = '''      <label>予習日（次回授業日）</label>
      <input type="date" name="scheduled_date" required>
      <button type="submit">登録する</button>'''

new_html = '''      <label>予習日（任意・未定の場合は空欄でよい）</label>
      <input type="date" name="scheduled_date">
      <p style="font-size:12px;color:#888;margin-top:4px;">
        空欄の場合は問題マスタのみに登録されます。後から「問題一覧・編集」で予習日を設定できます。
      </p>
      <button type="submit">登録する</button>'''

if old_html in html_content:
    html_content = html_content.replace(old_html, new_html)
    with open(problems_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✅ problems.html を修正しました")
else:
    print("❌ problems.htmlの対象箇所が見つかりません")

# ─── MCPのadd_problemも予習日を任意に変更 ──────────────
mcp_path = os.path.join(base, "mcp_server.py")
with open(mcp_path, "r", encoding="utf-8") as f:
    mcp_content = f.read()

old_mcp = '''                "required": ["subject", "textbook", "problem_number", "importance",
                             "difficulty", "review_value", "estimated_minutes",
                             "student_ids", "scheduled_date"]'''

new_mcp = '''                "required": ["subject", "textbook", "problem_number", "importance",
                             "difficulty", "review_value", "estimated_minutes"]'''

if old_mcp in mcp_content:
    mcp_content = mcp_content.replace(old_mcp, new_mcp)

old_mcp2 = '''        problem_id = c.lastrowid
        for sid in arguments["student_ids"]:
            c.execute("""
                INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
                VALUES (?, ?, ?, ?)
            """, (sid, problem_id, arguments["scheduled_date"], "予習"))
        conn.commit()
        conn.close()
        return [TextContent(type="text", text=f"問題を登録しました（problem_id: {problem_id}）")]'''

new_mcp2 = '''        problem_id = c.lastrowid
        student_ids = arguments.get("student_ids", [])
        scheduled_date = arguments.get("scheduled_date", "")
        if scheduled_date and student_ids:
            for sid in student_ids:
                c.execute("""
                    INSERT INTO assignments
                    (student_id, problem_id, scheduled_date, category)
                    VALUES (?, ?, ?, ?)
                """, (sid, problem_id, scheduled_date, "予習"))
        conn.commit()
        conn.close()
        return [TextContent(type="text", text=f"問題を登録しました（problem_id: {problem_id}）")]'''

if old_mcp2 in mcp_content:
    mcp_content = mcp_content.replace(old_mcp2, new_mcp2)
    with open(mcp_path, "w", encoding="utf-8") as f:
        f.write(mcp_content)
    print("✅ mcp_server.py を修正しました")
else:
    print("❌ mcp_server.pyの対象箇所が見つかりません")

# ─── problem_edit.htmlに予習日設定を追加 ───────────────
problem_edit_path = os.path.join(templates, "problem_edit.html")
with open(problem_edit_path, "r", encoding="utf-8") as f:
    edit_content = f.read()

old_edit = '''      <button type="submit">更新する</button>
    </form>
  </div>
  <p><a href="/problems">← 問題マスタ一覧に戻る</a></p>'''

new_edit = '''      <button type="submit">更新する</button>
    </form>
  </div>

  <div class="form-box" style="margin-top:24px;">
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
  </div>

  <p><a href="/problems">← 問題マスタ一覧に戻る</a></p>'''

if old_edit in edit_content:
    edit_content = edit_content.replace(old_edit, new_edit)
    with open(problem_edit_path, "w", encoding="utf-8") as f:
        f.write(edit_content)
    print("✅ problem_edit.html を修正しました")
else:
    print("❌ problem_edit.htmlの対象箇所が見つかりません")

# ─── app.pyにassignルートを追加 ────────────────────────
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

assign_route = '''
@app.route("/problems/assign/<int:problem_id>", methods=["POST"])
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
    return redirect(f"/problems/edit/{problem_id}")

'''

if "/problems/assign/" not in app_content:
    idx = app_content.rfind("if __name__")
    app_content = app_content[:idx] + assign_route + app_content[idx:]
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app_content)
    print("✅ app.py に出題予定追加ルートを追加しました")
else:
    print("ℹ️ 出題予定追加ルートはすでに存在します")

# ─── problem_edit.htmlにstudentsを渡すようapp.pyを修正 ──
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

old_edit_route = '''    c.execute("SELECT * FROM problems WHERE problem_id=?", (problem_id,))
    problem = c.fetchone()
    conn.close()
    return render_template("problem_edit.html", problem=problem)'''

new_edit_route = '''    c.execute("SELECT * FROM problems WHERE problem_id=?", (problem_id,))
    problem = c.fetchone()
    c.execute("SELECT * FROM students ORDER BY student_id")
    students = c.fetchall()
    conn.close()
    return render_template("problem_edit.html", problem=problem, students=students)'''

if old_edit_route in app_content:
    app_content = app_content.replace(old_edit_route, new_edit_route)
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app_content)
    print("✅ app.py のproblem_edit関数を修正しました")
else:
    print("❌ problem_edit関数の対象箇所が見つかりません")

print("✅ 全て完了")