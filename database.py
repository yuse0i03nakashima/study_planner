import sqlite3
from datetime import date, timedelta

DB_PATH = "C:/Users/ynaka/study_planner/study_planner.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            subjects TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS problems (
            problem_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            textbook TEXT NOT NULL,
            problem_number TEXT NOT NULL,
            importance INTEGER NOT NULL DEFAULT 3,
            difficulty INTEGER NOT NULL DEFAULT 3,
            review_value INTEGER NOT NULL DEFAULT 3,
            estimated_minutes INTEGER NOT NULL DEFAULT 15,
            type TEXT NOT NULL DEFAULT "標準",
            instruction TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            problem_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            correct INTEGER NOT NULL,
            mastery INTEGER NOT NULL,
            category TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (problem_id) REFERENCES problems(problem_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            problem_id INTEGER NOT NULL,
            scheduled_date TEXT NOT NULL,
            category TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            FOREIGN KEY (problem_id) REFERENCES problems(problem_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS schedule_base (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            dow INTEGER NOT NULL,
            available_minutes INTEGER NOT NULL DEFAULT 0,
            UNIQUE(student_id, dow),
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS schedule_override (
            override_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            date TEXT NOT NULL,
            available_minutes INTEGER NOT NULL DEFAULT 0,
            UNIQUE(student_id, date),
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS plan_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            generated_date TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            excel_path TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS class_schedule_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            dow INTEGER NOT NULL,
            UNIQUE(student_id, subject, dow),
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS class_schedule_override (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            next_class_date TEXT NOT NULL,
            UNIQUE(student_id, subject),
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    """)
    students = [
        ("S001", "神田悠帆", "数学,古典,社会"),
        ("S002", "小山たみ", "数学"),
        ("S003", "齊藤匠海", "数学"),
        ("S004", "長友想典", "数学,英語"),
    ]
    c.executemany("""
        INSERT OR IGNORE INTO students (student_id, name, subjects)
        VALUES (?, ?, ?)
    """, students)
    conn.commit()
    conn.close()


# ─── SRSロジック ───────────────────────────────────────

INTERVAL_WEEKS_COMMON = {1: 1, 2: 3}
INTERVAL_WEEKS_MASTERY3 = {5: 6, 4: 8, 3: 12, 2: 18, 1: 24}

def get_next_date(review_value, mastery, last_date_str):
    last_date = date.fromisoformat(last_date_str)
    if mastery <= 2:
        weeks = INTERVAL_WEEKS_COMMON.get(mastery, 1)
    else:
        weeks = INTERVAL_WEEKS_MASTERY3.get(review_value, 12)
    return last_date + timedelta(weeks=weeks)

def calc_new_mastery(student_id, problem_id, correct, today_str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT date, correct, mastery FROM history
        WHERE student_id = ? AND problem_id = ?
        ORDER BY date DESC
    """, (student_id, problem_id))
    rows = c.fetchall()
    conn.close()

    current_mastery = rows[0]["mastery"] if rows else 1
    if not correct:
        return max(1, current_mastery - 1)

    today = date.fromisoformat(today_str)

    if current_mastery == 1:
        correct_days = set(r["date"] for r in rows if r["correct"])
        correct_days.add(today_str)
        return 2 if len(correct_days) >= 2 else 1

    if current_mastery == 2:
        recent = [r for r in rows if r["correct"]][:2]
        if len(recent) < 2:
            return 2
        dates = sorted([date.fromisoformat(r["date"]) for r in recent] + [today])
        if (dates[-1] - dates[0]).days >= 7:
            return 3
        return 2

    return current_mastery

def update_assignments_after_record(student_id, problem_id, today_str, new_mastery):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM assignments WHERE student_id=? AND problem_id=?",
              (student_id, problem_id))
    c.execute("SELECT review_value FROM problems WHERE problem_id=?", (problem_id,))
    row = c.fetchone()
    if row:
        review_value = row["review_value"]
        next_date = get_next_date(review_value, new_mastery, today_str)
        category = {1: "復習", 2: "定着"}.get(new_mastery, "再定着")
        c.execute("""
            INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
            VALUES (?, ?, ?, ?)
        """, (student_id, problem_id, next_date.isoformat(), category))
    conn.commit()
    conn.close()


# ─── 授業スケジュール取得 ──────────────────────────────

def get_next_class_date(student_id, subject, start_date_str):
    """教科ごとの次回授業日を取得する（上書き優先）"""
    conn = get_connection()
    c = conn.cursor()

    # 上書き（都度指定）を優先
    c.execute("""
        SELECT next_class_date FROM class_schedule_override
        WHERE student_id=? AND subject=?
    """, (student_id, subject))
    row = c.fetchone()
    if row:
        conn.close()
        return row["next_class_date"]

    # ベース曜日から次回授業日を計算
    c.execute("""
        SELECT dow FROM class_schedule_base
        WHERE student_id=? AND subject=?
        ORDER BY dow
    """, (student_id, subject))
    dows = [r["dow"] for r in c.fetchall()]
    conn.close()

    if not dows:
        return None

    start = date.fromisoformat(start_date_str)
    for i in range(1, 8):
        candidate = start + timedelta(days=i)
        if candidate.weekday() in dows:
            return candidate.isoformat()
    return None


def get_class_dates_in_range(student_id, subject, start_date_str, end_date_str):
    """期間内の授業日を全て取得する"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT dow FROM class_schedule_base
        WHERE student_id=? AND subject=?
    """, (student_id, subject))
    dows = [r["dow"] for r in c.fetchall()]
    conn.close()

    if not dows:
        return []

    start = date.fromisoformat(start_date_str)
    end = date.fromisoformat(end_date_str)
    class_dates = []
    current = start
    while current <= end:
        if current.weekday() in dows:
            class_dates.append(current.isoformat())
        current += timedelta(days=1)
    return class_dates


# ─── 計画表生成（教科×授業日対応版） ─────────────────

def get_plan_v2(student_id, start_date_str, end_date_str):
    """
    新しい計画生成ロジック：
    ・復習は授業直後の最初の日に配置
    ・予習は次回授業日の直前に配置
    ・定着・再定着は残り時間に全体にちりばめる
    """
    conn = get_connection()
    c = conn.cursor()

    # 出題予定を取得
    c.execute("""
        SELECT a.*, p.subject, p.textbook, p.problem_number,
               p.importance, p.difficulty, p.review_value,
               p.estimated_minutes, p.instruction, p.problem_id,
               p.textbook_id, p.order_in_textbook,
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
    """, (student_id, end_date_str))
    rows = c.fetchall()
    conn.close()

    plan = []
    for r in rows:
        mastery = r["mastery"] if r["mastery"] else 1
        plan.append({
            "category": r["category"],
            "subject": r["subject"],
            "textbook": r["textbook"],
            "problem_number": r["problem_number"],
            "importance": r["importance"],
            "difficulty": r["difficulty"],
            "review_value": r["review_value"],
            "estimated_minutes": r["estimated_minutes"],
            "mastery": "★" * mastery,
            "mastery_int": mastery,
            "last_date": r["last_date"] if r["last_date"] else "（初見）",
            "instruction": r["instruction"] if r["instruction"] else "",
            "problem_id": r["problem_id"],
            "textbook_id": r["textbook_id"],
            "order_in_textbook": r["order_in_textbook"] or r["problem_id"],
        })
    return plan


def get_schedule(student_id, start_date_str, end_date_str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT dow, available_minutes FROM schedule_base WHERE student_id=?",
              (student_id,))
    base = {row["dow"]: row["available_minutes"] for row in c.fetchall()}
    c.execute("""
        SELECT date, available_minutes FROM schedule_override
        WHERE student_id=? AND date BETWEEN ? AND ?
    """, (student_id, start_date_str, end_date_str))
    overrides = {row["date"]: row["available_minutes"] for row in c.fetchall()}
    conn.close()

    schedule = {}
    current = date.fromisoformat(start_date_str)
    end = date.fromisoformat(end_date_str)
    while current <= end:
        date_str = current.isoformat()
        schedule[date_str] = overrides.get(date_str, base.get(current.weekday(), 0))
        current += timedelta(days=1)
    return schedule


def save_plan_history(student_id, start_date, end_date, excel_path):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO plan_history
        (student_id, generated_date, start_date, end_date, excel_path)
        VALUES (?, ?, ?, ?, ?)
    """, (student_id, date.today().isoformat(), start_date, end_date, excel_path))
    conn.commit()
    conn.close()

def get_plan_histories(student_id=None):
    conn = get_connection()
    c = conn.cursor()
    if student_id:
        c.execute("""
            SELECT ph.*, s.name FROM plan_history ph
            JOIN students s ON ph.student_id = s.student_id
            WHERE ph.student_id=?
            ORDER BY ph.generated_date DESC
        """, (student_id,))
    else:
        c.execute("""
            SELECT ph.*, s.name FROM plan_history ph
            JOIN students s ON ph.student_id = s.student_id
            ORDER BY ph.generated_date DESC
        """)
    rows = c.fetchall()
    conn.close()
    return rows

def get_plan(student_id, target_date_str):
    """後方互換用：旧get_plan（export等から呼ばれる）"""
    return get_plan_v2(student_id, date.today().isoformat(), target_date_str)

def get_schedule_subject(student_id, subject, start_date_str, end_date_str):
    """教科ごとの勉強時間スケジュールを取得する"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT dow, available_minutes FROM schedule_base_subject
        WHERE student_id=? AND subject=?
    """, (student_id, subject))
    base = {row["dow"]: row["available_minutes"] for row in c.fetchall()}
    c.execute("""
        SELECT date, available_minutes FROM schedule_override_subject
        WHERE student_id=? AND subject=? AND date BETWEEN ? AND ?
    """, (student_id, subject, start_date_str, end_date_str))
    overrides = {row["date"]: row["available_minutes"] for row in c.fetchall()}
    conn.close()

    # 教科別設定がない場合はNoneを返す（全体設定を使う）
    if not base and not overrides:
        return None

    schedule = {}
    current = date.fromisoformat(start_date_str)
    end = date.fromisoformat(end_date_str)
    while current <= end:
        date_str = current.isoformat()
        schedule[date_str] = overrides.get(
            date_str, base.get(current.weekday(), 0))
        current += timedelta(days=1)
    return schedule


def auto_promote_on_launch(from_date, to_date):
    """
    アプリ起動時に呼び出す自動昇格処理。
    from_date〜to_dateの間にscheduled_dateがある問題を
    全生徒対象に正答扱いで昇格させる。
    誤答はadd_recordで別途報告がある場合のみ反映済みのため、
    日付が過ぎた問題は原則として正答とみなす。
    """
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT a.student_id, a.problem_id, a.scheduled_date,
               a.category, a.assignment_id, p.review_value,
               (SELECT mastery FROM history h
                WHERE h.student_id = a.student_id
                AND h.problem_id = a.problem_id
                ORDER BY h.date DESC LIMIT 1) as mastery
        FROM assignments a
        JOIN problems p ON a.problem_id = p.problem_id
        WHERE a.scheduled_date BETWEEN ? AND ?
          AND a.scheduled_date != '2099-12-31'
          AND a.category IN ('予習', '復習', '定着', '再定着')
    """, (from_date, to_date))
    rows = c.fetchall()

    promoted = 0
    for row in rows:
        student_id = row["student_id"]
        problem_id = row["problem_id"]
        scheduled_date = row["scheduled_date"]
        current_mastery = int(row["mastery"]) if row["mastery"] else 1

        # 既にhistoryに記録がある場合はスキップ
        # （add_recordで誤答が報告済みの場合はそちらを優先）
        c.execute("""
            SELECT history_id FROM history
            WHERE student_id=? AND problem_id=? AND date=?
        """, (student_id, problem_id, scheduled_date))
        if c.fetchone():
            continue

        new_mastery = min(current_mastery + 1, 3)

        c.execute("""
            INSERT INTO history
            (student_id, problem_id, date, correct, mastery, category)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, problem_id, scheduled_date,
              1, new_mastery, "自動昇格"))

        review_value = row["review_value"]
        next_date = get_next_date(review_value, new_mastery, scheduled_date)
        category = {1: "復習", 2: "定着"}.get(new_mastery, "再定着")

        c.execute("DELETE FROM assignments WHERE assignment_id=?",
                  (row["assignment_id"],))
        c.execute("""
            INSERT INTO assignments
            (student_id, problem_id, scheduled_date, category)
            VALUES (?, ?, ?, ?)
        """, (student_id, problem_id, next_date.isoformat(), category))
        promoted += 1

    conn.commit()
    conn.close()
    return promoted


def get_last_launch_date():
    """前回起動日を取得する"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM app_state WHERE key='last_launch_date'")
    row = c.fetchone()
    conn.close()
    if row:
        return row["value"]
    return date.today().isoformat()


def update_last_launch_date():
    """起動日を今日で更新する"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO app_state (key, value)
        VALUES ('last_launch_date', ?)
    """, (date.today().isoformat(),))
    conn.commit()
    conn.close()


def auto_promote_past_assignments(student_id):
    """後方互換用：旧関数。auto_promote_on_launchを使うこと。"""
    return 0



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


def calc_new_mastery_v2(student_id, problem_id, score, record_date):
    """
    5段階評価スコアから新しい習熟度を計算する。
    score: 5=完璧, 4=大体合ってる, 3=解き直し必要, 2=復習必要, 1=全く理解なし
    5,4 → 正答扱い（習熟度+1方向）
    3   → 現状維持
    2,1 → 誤答扱い（習熟度-1方向）
    """
    conn = get_connection()
    c = conn.cursor()

    # 現在の習熟度を取得
    c.execute("""
        SELECT mastery FROM history
        WHERE student_id=? AND problem_id=?
        ORDER BY date DESC LIMIT 1
    """, (student_id, problem_id))
    row = c.fetchone()
    current_mastery = row["mastery"] if row else 1

    if score >= 4:
        # 正答扱い：通常のSRSロジックで昇格判定
        conn.close()
        return calc_new_mastery(student_id, problem_id, 1, record_date)
    elif score == 3:
        # 現状維持
        conn.close()
        return current_mastery
    else:
        # 誤答扱い
        conn.close()
        return calc_new_mastery(student_id, problem_id, 0, record_date)


def score_to_correct(score):
    """5段階スコアをcorrect(0/1)に変換する"""
    return 1 if score >= 4 else 0
