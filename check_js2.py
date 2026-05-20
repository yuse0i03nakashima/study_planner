import os, re, subprocess

base = r"C:\Users\ynaka\study_planner"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. app.py: update_field関数本体を確認・修正
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
app_path = os.path.join(base, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    app_lines = f.readlines()

print("=== app.py 1154〜1185行目 ===")
for i in range(1153, min(1185, len(app_lines))):
    print(f"  {i+1}: {app_lines[i].rstrip()}")

with open(app_path, "r", encoding="utf-8") as f:
    app = f.read()

# update_field関数でtotal_minutesをNULL対応に修正
# c.execute UPDATE文の直前にtotal_minutes特別処理を追加
old_execute = '''\
    c.execute(f"UPDATE problems SET {field}=? WHERE problem_id=?",
              (value, problem_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})'''

new_execute = '''\
    # total_minutesは空/nullをNULLに、数値は整数に変換
    if field == "total_minutes":
        if value is None or value == "" or value == "—":
            value = None
        else:
            try:
                value = int(value)
            except (ValueError, TypeError):
                value = None
    c.execute(f"UPDATE problems SET {field}=? WHERE problem_id=?",
              (value, problem_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})'''

if old_execute in app:
    app = app.replace(old_execute, new_execute, 1)
    print("✅ app.py: total_minutesのNULL対応を追加しました")
else:
    print("❌ app.py: UPDATE文が見つかりません")
    for i, line in enumerate(app.splitlines(), 1):
        if "UPDATE problems SET" in line:
            print(f"  {i}: {line}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. app.py: assignments_listのSELECT文にtotal_minutesを追加
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 783行目付近のSELECT文
print("\n=== app.py 780〜800行目 ===")
for i in range(779, min(800, len(app_lines))):
    print(f"  {i+1}: {app_lines[i].rstrip()}")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(app)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. problems.html: JSのfetch部分を確認して修正
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
for tmpl_name in ["problems.html", "problems_list.html"]:
    tmpl_path = os.path.join(base, "templates", tmpl_name)
    with open(tmpl_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"\n=== {tmpl_name}: fetch/finish/res.ok周辺 ===")
    for i, line in enumerate(lines, 1):
        if any(kw in line for kw in [
            "fetch(", "body: JSON", "res.ok", "span.textContent =",
            "showToast('✓"
        ]):
            # 前後も表示
            start = max(0, i-2)
            end = min(len(lines), i+3)
            for j in range(start, end):
                print(f"  {j+1}: {lines[j].rstrip()}")
            print()
            break