import os

base = r"C:\Users\ynaka\study_planner"
app_path = os.path.join(base, "app.py")

with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

old = '''@app.route("/history/delete/<int:history_id>", methods=["POST"])
def history_delete(history_id):
    reset_assignments = request.form.get("reset_assignments") == "1"
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM plan_history WHERE history_id=?", (history_id,))
    row = c.fetchone()
    if row and reset_assignments:
        student_id = row["student_id"]
        start_date = row["start_date"]
        end_date = row["end_date"]
        # 当該期間の出題予定をリセット
        c.execute("""
            DELETE FROM assignments
            WHERE student_id=?
            AND scheduled_date BETWEEN ? AND ?
        """, (student_id, start_date, end_date))
        # 当該期間の授業記録をリセット
        c.execute("""
            DELETE FROM history
            WHERE student_id=?
            AND date BETWEEN ? AND ?
        """, (student_id, start_date, end_date))
        print(f"リセット完了：{student_id} {start_date}〜{end_date}")
    # Excelファイルを削除
    if row:
        import os as _os
        if _os.path.exists(row["excel_path"]):
            _os.remove(row["excel_path"])
    c.execute("DELETE FROM plan_history WHERE history_id=?", (history_id,))
    conn.commit()
    conn.close()
    return redirect("/history")'''

new = '''@app.route("/history/delete/<int:history_id>", methods=["POST"])
def history_delete(history_id):
    reset_assignments = request.form.get("reset_assignments") == "1"
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM plan_history WHERE history_id=?", (history_id,))
    row = c.fetchone()
    if row and reset_assignments:
        student_id = row["student_id"]
        start_date = row["start_date"]
        end_date = row["end_date"]

        # 当該期間の授業記録（historyテーブル）のみ削除
        # ※problemsテーブルは削除しない
        c.execute("""
            DELETE FROM history
            WHERE student_id=?
            AND date BETWEEN ? AND ?
        """, (student_id, start_date, end_date))

        # 当該期間の出題予定（assignmentsテーブル）を削除
        # → 授業記録が消えたので、出題予定も初期状態に戻す
        c.execute("""
            DELETE FROM assignments
            WHERE student_id=?
            AND scheduled_date BETWEEN ? AND ?
        """, (student_id, start_date, end_date))

        # 問題マスタに登録された問題を「予習未定」として出題予定に戻す
        # （assignments に存在しない問題のみ）
        c.execute("""
            INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
            SELECT ?, p.problem_id, ?, '復習'
            FROM problems p
            WHERE p.problem_id IN (
                SELECT DISTINCT problem_id FROM history
                WHERE student_id=?
            )
            AND p.problem_id NOT IN (
                SELECT problem_id FROM assignments WHERE student_id=?
            )
        """, (student_id, start_date, student_id, student_id))

    # Excelファイルを削除（ファイルのみ・DBレコードは残す）
    if row:
        if os.path.exists(row["excel_path"]):
            os.remove(row["excel_path"])

    c.execute("DELETE FROM plan_history WHERE history_id=?", (history_id,))
    conn.commit()
    conn.close()
    return redirect("/history")'''

if old in content:
    content = content.replace(old, new)
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ history_delete関数を修正しました")
else:
    print("❌ 対象箇所が見つかりません")