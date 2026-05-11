import os

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")

# ─── class_schedule.html ──────────────────────────────
class_schedule_html = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>授業スケジュール管理</title>
  <style>
    body { font-family: sans-serif; max-width: 700px; margin: 40px auto; background: #f5f7fa; }
    h1 { color: #2c3e50; }
    .form-box { background: white; padding: 24px; border-radius: 8px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    h2 { color: #2c3e50; margin-top: 0; font-size: 16px; }
    label { display: block; margin-top: 12px; font-weight: bold; }
    select, input[type="date"] { width: 100%; padding: 8px; margin-top: 4px; border: 1px solid #ccc; border-radius: 4px; font-size: 15px; box-sizing: border-box; }
    .dow-checks { display: flex; gap: 12px; margin-top: 8px; flex-wrap: wrap; }
    .dow-checks label { font-weight: normal; display: flex; align-items: center; gap: 4px; font-size: 14px; }
    .dow-checks input { width: auto; }
    .subject-section { background: #f8f9fa; border-radius: 6px; padding: 16px; margin-top: 16px; border-left: 4px solid #4472C4; }
    .subject-section h3 { margin: 0 0 8px 0; color: #4472C4; font-size: 15px; }
    .current-setting { font-size: 13px; color: #555; margin-bottom: 8px; }
    .current-setting span { background: #4472C4; color: white; padding: 2px 8px; border-radius: 4px; margin-right: 4px; font-size: 12px; }
    .override-row { display: grid; grid-template-columns: 1fr auto; gap: 8px; align-items: end; margin-top: 8px; }
    button { margin-top: 12px; padding: 8px 20px; background: #4472C4; color: white; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; }
    button:hover { background: #2c5fa8; }
    .btn-del { background: #e74c3c; }
    .btn-del:hover { background: #c0392b; }
    .btn-small { padding: 6px 14px; font-size: 13px; margin-top: 0; }
    a { color: #4472C4; }
    .hint { font-size: 12px; color: #888; margin-top: 4px; }
  </style>
</head>
<body>
  <h1>⑧ 授業スケジュール管理</h1>

  <div class="form-box">
    <h2>生徒を選択</h2>
    <select onchange="location.href='?student_id='+this.value">
      {% for s in students %}
      <option value="{{ s.student_id }}"
        {% if s.student_id == selected_student %}selected{% endif %}>
        {{ s.name }}
      </option>
      {% endfor %}
    </select>
  </div>

  {% if student_subjects %}
  {% set dow_names = ["月", "火", "水", "木", "金", "土", "日"] %}

  {% for subject in student_subjects %}
  <div class="form-box">
    <h2>{{ subject }}</h2>

    <!-- 現在のベース設定 -->
    <div class="current-setting">
      ベース授業曜日：
      {% if base_schedule.get(subject) %}
        {% for dow in base_schedule.get(subject, []) %}
          <span>{{ dow_names[dow] }}</span>
        {% endfor %}
      {% else %}
        未設定
      {% endif %}
    </div>

    <!-- ベース曜日設定フォーム -->
    <div class="subject-section">
      <h3>授業曜日を設定（毎週固定）</h3>
      <form method="POST">
        <input type="hidden" name="action" value="save_base">
        <input type="hidden" name="student_id" value="{{ selected_student }}">
        <input type="hidden" name="subject" value="{{ subject }}">
        <div class="dow-checks">
          {% for i in range(7) %}
          <label>
            <input type="checkbox" name="dows" value="{{ i }}"
              {% if i in base_schedule.get(subject, []) %}checked{% endif %}>
            {{ dow_names[i] }}
          </label>
          {% endfor %}
        </div>
        <button type="submit">曜日を保存</button>
      </form>
    </div>

    <!-- 次回授業日の上書き -->
    <div class="subject-section" style="border-left-color: #27ae60; margin-top: 12px;">
      <h3>次回授業日を手動指定（都度変更）</h3>
      {% if override_schedule.get(subject) %}
      <div class="current-setting">
        現在の指定：<span style="background:#27ae60;">{{ override_schedule.get(subject) }}</span>
        <form method="POST" style="display:inline;">
          <input type="hidden" name="action" value="delete_override">
          <input type="hidden" name="student_id" value="{{ selected_student }}">
          <input type="hidden" name="subject" value="{{ subject }}">
          <button type="submit" class="btn-del btn-small">解除</button>
        </form>
      </div>
      {% endif %}
      <form method="POST">
        <input type="hidden" name="action" value="save_override">
        <input type="hidden" name="student_id" value="{{ selected_student }}">
        <input type="hidden" name="subject" value="{{ subject }}">
        <div class="override-row">
          <input type="date" name="next_class_date"
            value="{{ override_schedule.get(subject, '') }}">
          <button type="submit" class="btn-small">指定</button>
        </div>
        <p class="hint">ベース曜日より優先されます。計画表出力後は手動で解除してください。</p>
      </form>
    </div>
  </div>
  {% endfor %}
  {% endif %}

  <p><a href="/">← トップに戻る</a></p>
</body>
</html>"""

with open(os.path.join(templates, "class_schedule.html"), "w", encoding="utf-8") as f:
    f.write(class_schedule_html)
print("✅ class_schedule.html を作成しました")

# ─── index.html の更新 ────────────────────────────────
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
    <a href="/record/list">③ 授業記録修正</a>
    <a href="/preview">④ 計画表プレビュー・出力</a>
    <a href="/schedule">⑤ 勉強時間登録</a>
    <a href="/students">⑥ 生徒管理</a>
    <a href="/history">⑦ 過去の計画表</a>
    <a href="/class_schedule">⑧ 授業スケジュール管理</a>
  </div>
</body>
</html>"""

with open(os.path.join(templates, "index.html"), "w", encoding="utf-8") as f:
    f.write(index_html)
print("✅ index.html を更新しました")

# ─── mcp_server.py にツールを追加 ─────────────────────
mcp_path = os.path.join(base, "mcp_server.py")
with open(mcp_path, "r", encoding="utf-8") as f:
    mcp_content = f.read()

new_tools = '''        Tool(
            name="set_class_schedule",
            description="教科ごとの授業曜日（ベース）を登録する。dow: 0=月〜6=日",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"},
                    "subject": {"type": "string", "description": "教科"},
                    "dows": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "授業曜日のリスト（0=月〜6=日）"
                    }
                },
                "required": ["student_id", "subject", "dows"]
            }
        ),
        Tool(
            name="set_next_class_date",
            description="教科ごとの次回授業日を手動指定する（ベース曜日より優先）",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"},
                    "subject": {"type": "string", "description": "教科"},
                    "next_class_date": {"type": "string", "description": "次回授業日（YYYY-MM-DD形式）"}
                },
                "required": ["student_id", "subject", "next_class_date"]
            }
        ),
        Tool(
            name="get_class_schedule",
            description="生徒の授業スケジュール設定を取得する",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "生徒ID"}
                },
                "required": ["student_id"]
            }
        ),'''

old_last_tool = '''        Tool(
            name="generate_pdf_plan",'''

mcp_content = mcp_content.replace(
    old_last_tool,
    new_tools + "\n        Tool(\n            name=\"generate_pdf_plan\","
)

new_impls = '''    elif name == "set_class_schedule":
        student_id = arguments["student_id"]
        subject = arguments["subject"]
        dows = arguments["dows"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM class_schedule_base "
                  "WHERE student_id=? AND subject=?",
                  (student_id, subject))
        for dow in dows:
            c.execute("""
                INSERT OR IGNORE INTO class_schedule_base
                (student_id, subject, dow) VALUES (?, ?, ?)
            """, (student_id, subject, dow))
        conn.commit()
        conn.close()
        dow_names = ["月", "火", "水", "木", "金", "土", "日"]
        dow_str = "・".join([dow_names[d] for d in dows])
        return [TextContent(type="text",
            text=f"{subject}の授業曜日を設定しました（{dow_str}）")]

    elif name == "set_next_class_date":
        student_id = arguments["student_id"]
        subject = arguments["subject"]
        next_date = arguments["next_class_date"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO class_schedule_override
            (student_id, subject, next_class_date)
            VALUES (?, ?, ?)
            ON CONFLICT(student_id, subject)
            DO UPDATE SET next_class_date=?
        """, (student_id, subject, next_date, next_date))
        conn.commit()
        conn.close()
        return [TextContent(type="text",
            text=f"{subject}の次回授業日を{next_date}に設定しました")]

    elif name == "get_class_schedule":
        student_id = arguments["student_id"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT subject, dow FROM class_schedule_base "
                  "WHERE student_id=? ORDER BY subject, dow",
                  (student_id,))
        base_rows = c.fetchall()
        c.execute("SELECT subject, next_class_date FROM class_schedule_override "
                  "WHERE student_id=?", (student_id,))
        override_rows = c.fetchall()
        conn.close()
        dow_names = ["月", "火", "水", "木", "金", "土", "日"]
        base = {}
        for r in base_rows:
            base.setdefault(r["subject"], []).append(dow_names[r["dow"]])
        overrides = {r["subject"]: r["next_class_date"] for r in override_rows}
        result = {
            "base_schedule": {k: "・".join(v) for k, v in base.items()},
            "override_schedule": overrides
        }
        return [TextContent(type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2))]

    '''

old_last_impl = '''    elif name == "generate_excel_plan":'''
mcp_content = mcp_content.replace(
    old_last_impl,
    new_impls + "    elif name == \"generate_excel_plan\":"
)

with open(mcp_path, "w", encoding="utf-8") as f:
    f.write(mcp_content)
print("✅ mcp_server.py を更新しました")

print("✅ Part3 完了")