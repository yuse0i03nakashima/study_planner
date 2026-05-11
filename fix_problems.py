import os

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")

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
    input[type="text"], input[type="date"], select, textarea {
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
    button { margin-top: 16px; padding: 10px 28px; background: #4472C4; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; }
    button:hover { background: #2c5fa8; }
    .btn-edit { padding: 4px 10px; background: #4472C4; color: white; border-radius: 4px; text-decoration: none; font-size: 12px; margin-right: 4px; }
    .btn-edit:hover { background: #2c5fa8; }
    .btn-del { padding: 4px 10px; background: #e74c3c; color: white; border: none; border-radius: 4px; font-size: 12px; cursor: pointer; }
    .btn-del:hover { background: #c0392b; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); font-size: 12px; }
    th { background: #4472C4; color: white; padding: 8px; }
    td { padding: 6px 8px; border-bottom: 1px solid #eee; text-align: center; }
    td.instruction { text-align: left; max-width: 180px; }
    a { color: #4472C4; }
  </style>
</head>
<body>
  <h1>① 問題マスタ登録・編集</h1>
  <div class="form-box">
    <form method="POST">
      <div class="row2">
        <div>
          <label>教科</label>
          <input type="text" name="subject" placeholder="例：数学" required>
        </div>
        <div>
          <label>テキスト名</label>
          <input type="text" name="textbook" placeholder="例：青チャート" required>
        </div>
      </div>
      <label>問題番号・名称</label>
      <input type="text" name="problem_number" placeholder="例：例題12" required>
      <div class="row3">
        <div>
          <label>重要度（1〜5）</label>
          <select name="importance">
            <option value="5">5（最重要）</option>
            <option value="4">4（重要）</option>
            <option value="3" selected>3（標準）</option>
            <option value="2">2（やや低）</option>
            <option value="1">1（低）</option>
          </select>
          <p class="hint">試験での出題頻度・概念的重要性</p>
        </div>
        <div>
          <label>難易度（1〜5）</label>
          <select name="difficulty">
            <option value="5">5（最難）</option>
            <option value="4">4（難）</option>
            <option value="3" selected>3（標準）</option>
            <option value="2">2（易）</option>
            <option value="1">1（基礎）</option>
          </select>
          <p class="hint">問題の難しさ</p>
        </div>
        <div>
          <label>復習価値（1〜5）</label>
          <select name="review_value">
            <option value="5">5（最高）</option>
            <option value="4">4（高）</option>
            <option value="3" selected>3（標準）</option>
            <option value="2">2（低）</option>
            <option value="1">1（最低）</option>
          </select>
          <p class="hint">繰り返し解く意義の大きさ</p>
        </div>
      </div>
      <div class="row2">
        <div>
          <label>所要時間（5分単位）</label>
          <select name="estimated_minutes">
            {% for m in range(5, 125, 5) %}
            <option value="{{ m }}" {% if m == 15 %}selected{% endif %}>{{ m }}分</option>
            {% endfor %}
          </select>
        </div>
      </div>
      <label>学習指示（任意）</label>
      <textarea name="instruction" placeholder="例：「ある聖、...と言ひけり。」まで品詞分解を行う。"></textarea>
      <label>出題する生徒（複数選択可）</label>
      <div class="student-checks">
        {% for s in students %}
        <label>
          <input type="checkbox" name="student_ids" value="{{ s.student_id }}">
          {{ s.name }}
        </label>
        {% endfor %}
      </div>
      <label>予習日（次回授業日）</label>
      <input type="date" name="scheduled_date" required>
      <button type="submit">登録する</button>
    </form>
  </div>

  <h2>直近50件</h2>
  <table>
    <tr>
      <th>ID</th><th>教科</th><th>テキスト名</th><th>問題番号</th>
      <th>重要度</th><th>難易度</th><th>復習価値</th><th>所要時間</th>
      <th>学習指示</th><th>操作</th>
    </tr>
    {% for p in problems %}
    <tr>
      <td>{{ p.problem_id }}</td>
      <td>{{ p.subject }}</td>
      <td>{{ p.textbook }}</td>
      <td>{{ p.problem_number }}</td>
      <td>{{ p.importance }}</td>
      <td>{{ p.difficulty }}</td>
      <td>{{ p.review_value }}</td>
      <td>{{ p.estimated_minutes }}分</td>
      <td class="instruction">{{ p.instruction or "―" }}</td>
      <td>
        <a class="btn-edit" href="/problems/edit/{{ p.problem_id }}">編集</a>
        <form method="POST" action="/problems/delete/{{ p.problem_id }}"
              style="display:inline"
              onsubmit="return confirm('問題ID {{ p.problem_id }} を削除しますか？関連する授業記録・出題予定も削除されます。')">
          <button class="btn-del">削除</button>
        </form>
      </td>
    </tr>
    {% endfor %}
  </table>
  <p><a href="/">← トップに戻る</a></p>
</body>
</html>"""

with open(os.path.join(templates, "problems.html"), "w", encoding="utf-8") as f:
    f.write(problems_html)
print("✅ problems.html を書き直しました")