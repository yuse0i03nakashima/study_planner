import os, subprocess

base = r"C:\Users\ynaka\study_planner"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. problems.html: Recent Problems テーブル
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
prob_path = os.path.join(base, "templates", "problems.html")
with open(prob_path, "r", encoding="utf-8") as f:
    prob = f.read()

# ヘッダー修正（分 → 分/Total）
old_prob_th = "<th>Imp</th><th>Dif</th><th>RV</th><th>分</th><th>学習指示</th><th></th>"
new_prob_th = "<th>Imp</th><th>Dif</th><th>RV</th><th>分</th><th>Total</th><th>学習指示</th><th></th>"
if old_prob_th in prob:
    prob = prob.replace(old_prob_th, new_prob_th)
    print("✅ problems.htmlのヘッダーを修正しました")
else:
    print("❌ problems.htmlのヘッダーが見つかりません")

# Minセルの後にTotal Minセルを追加
old_prob_min = """\
        <!-- 所要時間：数値編集（5分単位） -->
        <td class="editable-cell" data-problem="{{ p.problem_id }}" data-field="estimated_minutes">
          <span class="editable" ondblclick="startNumEdit(this, 5, 120, 5)">{{ p.estimated_minutes }}</span>
        </td>"""
new_prob_min = """\
        <!-- 所要時間：数値編集（5分単位） -->
        <td class="editable-cell" data-problem="{{ p.problem_id }}" data-field="estimated_minutes">
          <span class="editable" ondblclick="startNumEdit(this, 5, 120, 5)">{{ p.estimated_minutes }}</span>
        </td>
        <!-- 総HP：数値編集 -->
        <td class="editable-cell" data-problem="{{ p.problem_id }}" data-field="total_minutes">
          <span class="editable" ondblclick="startNumEdit(this, 5, 999, 5)"
            style="color:{% if p.total_minutes %}var(--green){% else %}var(--text-dim){% endif %};">
            {{ p.total_minutes if p.total_minutes else '—' }}
          </span>
        </td>"""

if old_prob_min in prob:
    prob = prob.replace(old_prob_min, new_prob_min)
    print("✅ problems.htmlにTotal Minセルを追加しました")
else:
    print("❌ problems.htmlのMinセルが見つかりません")

with open(prob_path, "w", encoding="utf-8") as f:
    f.write(prob)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. problems_list.html
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pl_path = os.path.join(base, "templates", "problems_list.html")
with open(pl_path, "r", encoding="utf-8") as f:
    pl = f.read()

# ヘッダー修正
old_pl_th = "<th>Imp</th><th>Dif</th><th>RV</th><th>分</th>"
new_pl_th = "<th>Imp</th><th>Dif</th><th>RV</th><th>分</th><th>Total</th>"
if old_pl_th in pl:
    pl = pl.replace(old_pl_th, new_pl_th, 1)
    print("✅ problems_list.htmlのヘッダーを修正しました")
else:
    print("❌ problems_list.htmlのヘッダーが見つかりません")

# Minセルの後にTotal Minセルを追加
old_pl_min = """\
      <td class="editable-cell" data-problem="{{ p.problem_id }}" data-field="estimated_minutes">
        <span class="editable" ondblclick="startNumEdit(this, 5, 120, 5)">{{ p.estimated_minutes }}</span>
      </td>"""
new_pl_min = """\
      <td class="editable-cell" data-problem="{{ p.problem_id }}" data-field="estimated_minutes">
        <span class="editable" ondblclick="startNumEdit(this, 5, 120, 5)">{{ p.estimated_minutes }}</span>
      </td>
      <td class="editable-cell" data-problem="{{ p.problem_id }}" data-field="total_minutes">
        <span class="editable" ondblclick="startNumEdit(this, 5, 999, 5)"
          style="color:{% if p.total_minutes %}var(--green){% else %}var(--text-dim){% endif %};">
          {{ p.total_minutes if p.total_minutes else '—' }}
        </span>
      </td>"""

if old_pl_min in pl:
    pl = pl.replace(old_pl_min, new_pl_min)
    print("✅ problems_list.htmlにTotal Minセルを追加しました")
else:
    print("❌ problems_list.htmlのMinセルが見つかりません")

with open(pl_path, "w", encoding="utf-8") as f:
    f.write(pl)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. assignments_list.html: 構造を確認してから修正
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
asgn_path = os.path.join(base, "templates", "assignments_list.html")
with open(asgn_path, "r", encoding="utf-8") as f:
    asgn_lines = f.readlines()

print("\n=== assignments_list.html: 205〜230行目 ===")
for i in range(204, min(230, len(asgn_lines))):
    print(f"  {i+1}: {asgn_lines[i].rstrip()}")

# app.pyのassignments_listルートのSELECT文を確認
app_path = os.path.join(base, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    app_lines = f.readlines()

print("\n=== app.py: assignments_list SELECT文 ===")
in_route = False
for i, line in enumerate(app_lines, 1):
    if "assignments_list" in line or "def assignments" in line:
        in_route = True
    if in_route and ("SELECT" in line or "estimated_minutes" in line
                     or "total_minutes" in line):
        print(f"  {i}: {line.rstrip()}")
    if in_route and i > 1200:
        break

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. app.pyのassignments SELECT文にtotal_minutesを追加
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with open(app_path, "r", encoding="utf-8") as f:
    app = f.read()

# assignments_listで使われているSELECT文のパターンを検索
import re
matches = list(re.finditer(
    r'p\.importance.*?p\.review_value.*?p\.estimated_minutes',
    app, re.DOTALL
))
print(f"\np.estimated_minutesを含むSELECT文: {len(matches)}件")
for m in matches:
    print(f"  位置{m.start()}: {m.group(0)[:80]}")

# assignments_listのSELECT文（total_minutesが未追加のもの）を修正
old_asgn_sel = "p.importance, p.review_value, p.estimated_minutes\n            FROM assignments a"
new_asgn_sel = "p.importance, p.review_value, p.estimated_minutes, p.total_minutes\n            FROM assignments a"

if old_asgn_sel in app:
    app = app.replace(old_asgn_sel, new_asgn_sel)
    print("✅ assignments_listのSELECTにtotal_minutesを追加しました")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(app)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 構文チェック
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
for p in [app_path]:
    r = subprocess.run(
        [r"C:\Users\ynaka\AppData\Local\Programs\Python\Python312\python.exe",
         "-m", "py_compile", p],
        capture_output=True, text=True
    )
    name = os.path.basename(p)
    print(f"{'✅' if r.returncode==0 else '❌'} {name} {'構文OK' if r.returncode==0 else r.stderr}")

print("\n✅ 完了")