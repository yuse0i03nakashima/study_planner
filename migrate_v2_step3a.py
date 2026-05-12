import os

base = r"C:\Users\ynaka\study_planner"

# ─── database.pyに代表問題関連関数を追加 ────────────────
db_path = os.path.join(base, "database.py")
with open(db_path, "r", encoding="utf-8") as f:
    db_content = f.read()

new_funcs = '''

def get_same_class_problems(student_id, problem_id):
    """同じ授業日に登録された問題IDを取得する（周辺問題）"""
    conn = get_connection()
    c = conn.cursor()
    # 対象問題の出題日を取得
    c.execute("""
        SELECT scheduled_date FROM assignments
        WHERE student_id=? AND problem_id=?
        ORDER BY assignment_id DESC LIMIT 1
    """, (student_id, problem_id))
    row = c.fetchone()
    if not row:
        conn.close()
        return []
    scheduled_date = row["scheduled_date"]

    # 同じ授業日の問題を取得（対象問題は除く）
    c.execute("""
        SELECT problem_id FROM assignments
        WHERE student_id=? AND scheduled_date=? AND problem_id!=?
    """, (student_id, scheduled_date, problem_id))
    result = [r["problem_id"] for r in c.fetchall()]
    conn.close()
    return result


def is_suppressed(student_id, problem_id):
    """問題が抑制中かどうかを確認する"""
    conn = get_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("""
        SELECT suppressed_until FROM suppression
        WHERE student_id=? AND problem_id=? AND suppressed_until >= ?
    """, (student_id, problem_id, today))
    row = c.fetchone()
    conn.close()
    return row is not None


def set_suppression(student_id, problem_id, suppressed_until, reason=""):
    """問題の抑制を設定する"""
    conn = get_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("""
        INSERT INTO suppression
        (student_id, problem_id, suppressed_until, reason, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(student_id, problem_id)
        DO UPDATE SET suppressed_until=?, reason=?, created_at=?
    """, (student_id, problem_id, suppressed_until, reason, today,
          suppressed_until, reason, today))
    conn.commit()
    conn.close()


def clear_suppression(student_id, problem_id):
    """問題の抑制を解除する"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        DELETE FROM suppression
        WHERE student_id=? AND problem_id=?
    """, (student_id, problem_id))
    conn.commit()
    conn.close()


def process_representative_correct(student_id, problem_id, record_date):
    """
    代表問題（復習価値4以上）の正答処理。
    同じ授業日の周辺問題の習熟度を+1し、抑制を設定する。
    """
    conn = get_connection()
    c = conn.cursor()

    # 代表問題かどうか確認
    c.execute("SELECT review_value FROM problems WHERE problem_id=?",
              (problem_id,))
    p_row = c.fetchone()
    if not p_row or p_row["review_value"] < 4:
        conn.close()
        return 0

    # 代表問題の現在の習熟度と次回出題間隔を取得
    c.execute("""
        SELECT mastery FROM history
        WHERE student_id=? AND problem_id=?
        ORDER BY date DESC LIMIT 1
    """, (student_id, problem_id))
    h_row = c.fetchone()
    current_mastery = h_row["mastery"] if h_row else 1
    review_value = p_row["review_value"]

    # 抑制期間を計算（次回出題間隔の50%）
    next_date_obj = get_next_date(review_value, current_mastery, record_date)
    record_date_obj = date.fromisoformat(record_date)
    interval_days = (next_date_obj - record_date_obj).days
    suppress_days = max(7, interval_days // 2)
    suppressed_until = (record_date_obj +
                        timedelta(days=suppress_days)).isoformat()

    # 周辺問題を取得
    conn.close()
    surrounding_ids = get_same_class_problems(student_id, problem_id)
    promoted = 0

    for sur_id in surrounding_ids:
        conn2 = get_connection()
        c2 = conn2.cursor()

        # 現在の習熟度を取得
        c2.execute("""
            SELECT mastery FROM history
            WHERE student_id=? AND problem_id=?
            ORDER BY date DESC LIMIT 1
        """, (student_id, sur_id))
        sur_row = c2.fetchone()
        sur_mastery = sur_row["mastery"] if sur_row else 1
        new_mastery = min(sur_mastery + 1, 3)

        # 習熟度を更新（historyに記録）
        c2.execute("""
            INSERT INTO history
            (student_id, problem_id, date, correct, mastery, category)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, sur_id, record_date, 1, new_mastery, "代表問題連動"))

        # 出題予定を更新
        c2.execute("SELECT review_value FROM problems WHERE problem_id=?",
                   (sur_id,))
        sur_p = c2.fetchone()
        if sur_p:
            sur_next = get_next_date(sur_p["review_value"], new_mastery,
                                     record_date)
            category = {1: "復習", 2: "定着"}.get(new_mastery, "再定着")
            c2.execute("""
                DELETE FROM assignments
                WHERE student_id=? AND problem_id=?
            """, (student_id, sur_id))
            c2.execute("""
                INSERT INTO assignments
                (student_id, problem_id, scheduled_date, category)
                VALUES (?, ?, ?, ?)
            """, (student_id, sur_id, sur_next.isoformat(), category))

        conn2.commit()
        conn2.close()

        # 抑制を設定
        set_suppression(student_id, sur_id, suppressed_until,
                        f"代表問題(ID:{problem_id})正答による抑制")
        promoted += 1

    return promoted


def process_representative_wrong(student_id, problem_id, record_date):
    """
    代表問題の誤答処理。
    同じ授業日の周辺問題の習熟度を-1し、抑制を解除する。
    """
    conn = get_connection()
    c = conn.cursor()

    # 代表問題かどうか確認
    c.execute("SELECT review_value FROM problems WHERE problem_id=?",
              (problem_id,))
    p_row = c.fetchone()
    if not p_row or p_row["review_value"] < 4:
        conn.close()
        return 0

    conn.close()
    surrounding_ids = get_same_class_problems(student_id, problem_id)

    for sur_id in surrounding_ids:
        conn2 = get_connection()
        c2 = conn2.cursor()

        # 現在の習熟度を取得
        c2.execute("""
            SELECT mastery FROM history
            WHERE student_id=? AND problem_id=?
            ORDER BY date DESC LIMIT 1
        """, (student_id, sur_id))
        sur_row = c2.fetchone()
        sur_mastery = sur_row["mastery"] if sur_row else 1
        new_mastery = max(sur_mastery - 1, 1)

        # 習熟度を更新
        c2.execute("""
            INSERT INTO history
            (student_id, problem_id, date, correct, mastery, category)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, sur_id, record_date, 0, new_mastery, "代表問題連動"))

        # 出題予定を更新
        c2.execute("SELECT review_value FROM problems WHERE problem_id=?",
                   (sur_id,))
        sur_p = c2.fetchone()
        if sur_p:
            sur_next = get_next_date(sur_p["review_value"], new_mastery,
                                     record_date)
            category = {1: "復習", 2: "定着"}.get(new_mastery, "再定着")
            c2.execute("""
                DELETE FROM assignments WHERE student_id=? AND problem_id=?
            """, (student_id, sur_id))
            c2.execute("""
                INSERT INTO assignments
                (student_id, problem_id, scheduled_date, category)
                VALUES (?, ?, ?, ?)
            """, (student_id, sur_id, sur_next.isoformat(), category))

        conn2.commit()
        conn2.close()

        # 抑制を解除
        clear_suppression(student_id, sur_id)

    return len(surrounding_ids)


def get_suppressed_problems(student_id):
    """現在抑制中の問題IDリストを取得する"""
    conn = get_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("""
        SELECT problem_id FROM suppression
        WHERE student_id=? AND suppressed_until >= ?
    """, (student_id, today))
    result = [r["problem_id"] for r in c.fetchall()]
    conn.close()
    return result
'''

if "process_representative_correct" not in db_content:
    db_content = db_content + new_funcs
    with open(db_path, "w", encoding="utf-8") as f:
        f.write(db_content)
    print("✅ database.pyに代表問題関連関数を追加しました")
else:
    print("ℹ️ 代表問題関連関数はすでに存在します")

# ─── add_recordに代表問題処理を組み込む ─────────────────
app_path = os.path.join(base, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    app_content = f.read()

old_add_record = '''    elif name == "add_record":
        from database import calc_new_mastery, update_assignments_after_record
        student_id = arguments["student_id"]
        problem_id = arguments["problem_id"]
        record_date = arguments["record_date"]
        correct = 1 if arguments["correct"] else 0
        new_mastery = calc_new_mastery(student_id, problem_id, correct, record_date)
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO history
            (student_id, problem_id, date, correct, mastery, category)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, problem_id, record_date, correct, new_mastery, "記録"))
        conn.commit()
        conn.close()
        update_assignments_after_record(student_id, problem_id, record_date, new_mastery)
        stars = "★" * new_mastery
        return [TextContent(type="text",
            text=f"授業記録を保存しました（習熟度：{stars}）")]'''

new_add_record = '''    elif name == "add_record":
        from database import (calc_new_mastery, update_assignments_after_record,
                               process_representative_correct,
                               process_representative_wrong)
        student_id = arguments["student_id"]
        problem_id = arguments["problem_id"]
        record_date = arguments["record_date"]
        correct = 1 if arguments["correct"] else 0
        new_mastery = calc_new_mastery(student_id, problem_id, correct, record_date)
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
            INSERT INTO history
            (student_id, problem_id, date, correct, mastery, category)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, problem_id, record_date, correct, new_mastery, "記録"))
        conn.commit()
        conn.close()
        update_assignments_after_record(student_id, problem_id, record_date, new_mastery)
        stars = "★" * new_mastery

        # 代表問題処理（復習価値4以上）
        promoted = 0
        if correct:
            promoted = process_representative_correct(
                student_id, problem_id, record_date)
        else:
            process_representative_wrong(student_id, problem_id, record_date)

        msg = f"授業記録を保存しました（習熟度：{stars}）"
        if promoted > 0:
            msg += f"\\n代表問題として{promoted}問の周辺問題を連動更新しました"
        return [TextContent(type="text", text=msg)]'''

mcp_path = os.path.join(base, "mcp_server.py")
with open(mcp_path, "r", encoding="utf-8") as f:
    mcp_content = f.read()

if old_add_record in mcp_content:
    mcp_content = mcp_content.replace(old_add_record, new_add_record)
    with open(mcp_path, "w", encoding="utf-8") as f:
        f.write(mcp_content)
    print("✅ mcp_server.pyのadd_recordに代表問題処理を追加しました")
else:
    print("❌ mcp_server.pyのadd_record対象箇所が見つかりません")

print("✅ Step3a完了")