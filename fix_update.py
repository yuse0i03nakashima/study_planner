import os

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")

# ─── problems.html ─────────────────────────────────────
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
    .ai-box textarea { height: 100px; }
    .ai-result { margin-top: 12px; background: white; border-radius: 6px; padding: 12px; font-size: 13px; white-space: pre-wrap; display: none; }
    button { margin-top: 16px; padding: 10px 28px; background: #4472C4; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; }
    button:hover { background: #2c5fa8; }
    .btn-ai { background: #8e44ad; font-size: 14px; padding: 8px 20px; margin-top: 8px; }
    .btn-ai:hover { background: #6c3483; }
    .btn-ai-apply { background: #27ae60; font-size: 14px; padding: 8px 20px; margin-top: 8px; display: none; }
    .btn-ai-apply:hover { background: #1e8449; }
    .btn-edit { padding: 4px 10px; background: #4472C4; color: white; border-radius: 4px; text-decoration: none; font-size: 12px; margin-right: 4px; }
    .btn-edit:hover { background: #2c5fa8; }
    .btn-del { padding: 4px 10px; background: #e74c3c; color: white; border: none; border-radius: 4px; font-size: 12px; cursor: pointer; }
    .btn-del:hover { background: #c0392b; }
    table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); font-size: 12px; }
    th { background: #4472C4; color: white; padding: 8px; }
    td { padding: 6px 8px; border-bottom: 1px solid #eee; text-align: center; }
    td.instruction { text-align: left; max-width: 180px; }
    a { color: #4472C4; }
    .loading { color: #888; font-size: 13px; display: none; }
  </style>
</head>
<body>
  <h1>① 問題マスタ登録・編集</h1>

  <!-- AI自動入力ボックス -->
  <div class="ai-box">
    <h3>🤖 AIによる問題情報の自動提案</h3>
    <p style="font-size:13px; color:#555; margin:0 0 8px 0;">問題の説明を入力すると、AIが重要度・難易度・復習価値・所要時間・学習指示を提案します。</p>
    <textarea id="ai-input" placeholder="例：青チャート 例題12 二次方程式の解法。標準的な問題で、解の公式と因数分解の両方を使う。"></textarea>
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
          <input type="text" name="subject" id="f-subject" placeholder="例：数学" required>
        </div>
        <div>
          <label>テキスト名</label>
          <input type="text" name="textbook" id="f-textbook" placeholder="例：青チャート" required>
        </div>
      </div>
      <label>問題番号・名称</label>
      <input type="text" name="problem_number" id="f-problem_number" placeholder="例：例題12" required>
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
          <p class="hint">試験での出題頻度・概念的重要性</p>
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
          <p class="hint">問題の難しさ</p>
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
          <p class="hint">繰り返し解く意義の大きさ</p>
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
      </div>
      <label>学習指示（任意）</label>
      <textarea name="instruction" id="f-instruction" placeholder="例：「ある聖、...と言ひけり。」まで品詞分解を行う。"></textarea>
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
  <table id="problem-table">
    <tr>
      <th>ID</th><th>教科</th><th>テキスト名</th><th>問題番号</th>
      <th>重要度</th><th>難易度</th><th>復習価値</th><th>所要時間</th>
      <th>学習指示</th><th>操作</th>
    </tr>
    {% for p in problems %}
    <tr id="row-{{ p.problem_id }}">
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
        <button class="btn-del"
          onclick="deleteProblem({{ p.problem_id }}, this)">削除</button>
      </td>
    </tr>
    {% endfor %}
  </table>
  <p><a href="/">← トップに戻る</a></p>

  <script>
    let aiData = null;

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
      if (aiData.subject) document.getElementById('f-subject').value = aiData.subject;
      if (aiData.textbook) document.getElementById('f-textbook').value = aiData.textbook;
      if (aiData.problem_number) document.getElementById('f-problem_number').value = aiData.problem_number;
    }

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

# ─── schedule.html ─────────────────────────────────────
schedule_html = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>勉強時間登録</title>
  <style>
    body { font-family: sans-serif; max-width: 700px; margin: 40px auto; background: #f5f7fa; }
    h1 { color: #2c3e50; }
    .form-box { background: white; padding: 24px; border-radius: 8px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    label { display: block; margin-top: 12px; font-weight: bold; }
    select, input[type="date"], input[type="number"] { width: 100%; padding: 8px; margin-top: 4px; border: 1px solid #ccc; border-radius: 4px; font-size: 15px; box-sizing: border-box; }
    .dow-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; margin-top: 12px; }
    .dow-item { text-align: center; }
    .dow-item span { display: block; font-weight: bold; margin-bottom: 4px; }
    .dow-item input[type="number"] { padding: 4px; font-size: 13px; text-align: center; }
    .override-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 12px; }
    button { margin-top: 16px; padding: 10px 28px; background: #4472C4; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; }
    button:hover { background: #2c5fa8; }
    a { color: #4472C4; }
    .hint { font-size: 12px; color: #888; margin-top: 4px; }
  </style>
</head>
<body>
  <h1>⑤ 勉強時間登録</h1>

  <div class="form-box">
    <h2>生徒を選択</h2>
    <select id="student-select" onchange="location.href='?student_id='+this.value">
      {% for s in students %}
      <option value="{{ s.student_id }}"
        {% if s.student_id == selected_student %}selected{% endif %}>
        {{ s.name }}
      </option>
      {% endfor %}
    </select>
  </div>

  <div class="form-box">
    <h2>ベースの曜日別勉強時間</h2>
    <p class="hint">毎週の標準的な勉強可能時間を分単位で登録してください。制限なし。</p>
    <form method="POST">
      <input type="hidden" name="action" value="save_base">
      <input type="hidden" name="student_id" value="{{ selected_student }}">
      <div class="dow-grid">
        {% set dow_names = ["月", "火", "水", "木", "金", "土", "日"] %}
        {% for i in range(7) %}
        <div class="dow-item">
          <span>{{ dow_names[i] }}</span>
          <input type="number" name="dow_{{ i }}" min="0" step="5"
            value="{{ base_schedule.get(i, 0) }}" placeholder="0">
        </div>
        {% endfor %}
      </div>
      <p class="hint">単位：分　例）90 = 1時間30分</p>
      <button type="submit">ベースを保存</button>
    </form>
  </div>

  <div class="form-box">
    <h2>特定の日だけ変更</h2>
    <form method="POST">
      <input type="hidden" name="action" value="save_override">
      <input type="hidden" name="student_id" value="{{ selected_student }}">
      <div class="override-row">
        <div>
          <label>日付</label>
          <input type="date" name="override_date" required>
        </div>
        <div>
          <label>勉強時間（分）</label>
          <input type="number" name="override_minutes" min="0" step="5" placeholder="例：90" required>
        </div>
      </div>
      <button type="submit">上書き保存</button>
    </form>
  </div>

  <p><a href="/">← トップに戻る</a></p>
</body>
</html>"""

with open(os.path.join(templates, "problems.html"), "w", encoding="utf-8") as f:
    f.write(problems_html)
print("✅ problems.html を書き直しました")

with open(os.path.join(templates, "schedule.html"), "w", encoding="utf-8") as f:
    f.write(schedule_html)
print("✅ schedule.html を書き直しました")

# ─── app.pyにAI提案APIを追加 ───────────────────────────
app_path = os.path.join(base, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

ai_route = '''
@app.route("/api/ai_suggest", methods=["POST"])
def ai_suggest():
    import anthropic
    import json as json_module
    data = request.get_json()
    text = data.get("text", "")

    client = anthropic.Anthropic(api_key=open(
        r"C:\\Users\\ynaka\\study_planner\\Claude API key.txt",
        encoding="utf-8").read().strip())

    prompt = f"""以下の問題の説明を読んで、学習管理システムに登録するための情報をJSON形式で提案してください。

問題の説明：
{text}

以下のJSON形式のみで回答してください（説明不要）：
{{
  "subject": "教科名（数学/古典/英語/社会 など）",
  "textbook": "テキスト名",
  "problem_number": "問題番号・名称",
  "importance": 重要度（1〜5の整数）,
  "difficulty": 難易度（1〜5の整数）,
  "review_value": 復習価値（1〜5の整数）,
  "estimated_minutes": 所要時間（5の倍数の整数・分単位）,
  "instruction": "学習指示（具体的な取り組み方。不要なら空文字）"
}}

判断基準：
- 重要度：試験頻出・概念的重要性（5=最重要、1=低）
- 難易度：問題の難しさ（5=最難、1=基礎）
- 復習価値：繰り返し解く意義（5=最高、1=他で代替可能）
- 所要時間：初見で解くのにかかるおよその時間"""

    message = client.messages.create(
        model="claude-sonnet-4-5-20251022",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    text_response = message.content[0].text.strip()
    text_response = text_response.replace("```json", "").replace("```", "").strip()
    result = json_module.loads(text_response)
    return jsonify(result)

'''

if "/api/ai_suggest" not in app_content:
    app_content = app_content.replace(
        "if __name__ == '__main__':",
        ai_route + "if __name__ == '__main__':"
    )
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app_content)
    print("✅ app.py にAI提案APIを追加しました")
else:
    print("ℹ️ AI提案APIはすでに存在します")

# anthropicライブラリのインストール確認用メッセージ
print("✅ 完了")
print("⚠️  anthropicライブラリが必要です。以下を実行してください：")
print("pip install anthropic --break-system-packages")