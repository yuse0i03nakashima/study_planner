import sqlite3
import os
import logging
from datetime import date, timedelta

log = logging.getLogger('study_planner.database')

DB_PATH = os.environ.get(
    'DB_PATH',
    os.path.join(os.path.dirname(__file__), 'study_planner.db')
)

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # ── 基本テーブル ─────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            subjects TEXT NOT NULL,
            plan_mode TEXT DEFAULT 'all'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS series (
            series_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS textbooks (
            textbook_id INTEGER PRIMARY KEY AUTOINCREMENT,
            series_id INTEGER,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            description TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS textbook_sections (
            section_id INTEGER PRIMARY KEY AUTOINCREMENT,
            textbook_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            order_index INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS student_textbooks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            textbook_id INTEGER NOT NULL,
            UNIQUE(student_id, textbook_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS problems (
            problem_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            textbook TEXT NOT NULL,
            textbook_id INTEGER,
            section_id INTEGER,
            problem_number TEXT NOT NULL,
            importance INTEGER NOT NULL DEFAULT 3,
            difficulty INTEGER NOT NULL DEFAULT 3,
            review_value INTEGER NOT NULL DEFAULT 3,
            estimated_minutes INTEGER NOT NULL DEFAULT 15,
            total_minutes INTEGER,
            order_in_textbook INTEGER DEFAULT 1,
            type TEXT NOT NULL DEFAULT '標準',
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
            score INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            problem_id INTEGER NOT NULL,
            scheduled_date TEXT NOT NULL,
            category TEXT NOT NULL,
            assigned_minutes INTEGER,
            progress_before REAL DEFAULT 0.0,
            progress_after REAL,
            session_index INTEGER DEFAULT 1,
            session_total INTEGER DEFAULT 1
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS suppression (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            problem_id INTEGER NOT NULL,
            suppressed_until TEXT,
            reason TEXT,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS plan_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            generated_date TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            excel_path TEXT NOT NULL DEFAULT '',
            pdf_path TEXT DEFAULT '',
            subject TEXT DEFAULT '',
            confirmed INTEGER DEFAULT 0,
            plan_data TEXT DEFAULT ''
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS class_schedule_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            dow TEXT NOT NULL,
            UNIQUE(student_id, subject, dow)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS class_schedule_override (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            next_class_date TEXT NOT NULL,
            UNIQUE(student_id, subject)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS schedule_base (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            dow INTEGER NOT NULL,
            available_minutes INTEGER NOT NULL DEFAULT 0,
            UNIQUE(student_id, dow)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS schedule_override (
            override_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            date TEXT NOT NULL,
            available_minutes INTEGER NOT NULL DEFAULT 0,
            UNIQUE(student_id, date)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # ── 既存DBへのマイグレーション（カラム追加） ──────────
    migrations = [
        ("students",    "plan_mode TEXT DEFAULT 'all'"),
        ("problems",    "textbook_id INTEGER"),
        ("problems",    "section_id INTEGER"),
        ("problems",    "order_in_textbook INTEGER DEFAULT 1"),
        ("problems",    "total_minutes INTEGER"),
        ("problems",    "representative_of INTEGER"),  # 代表問題の明示指定（周辺→代表）
        ("history",     "score INTEGER"),
        ("assignments", "assigned_minutes INTEGER"),
        ("assignments", "progress_before REAL DEFAULT 0.0"),
        ("assignments", "progress_after REAL"),
        ("assignments", "session_index INTEGER DEFAULT 1"),
        ("assignments", "session_total INTEGER DEFAULT 1"),
        ("plan_history","pdf_path TEXT DEFAULT ''"),
        ("plan_history","subject TEXT DEFAULT ''"),
        ("plan_history","confirmed INTEGER DEFAULT 0"),
        ("plan_history","plan_data TEXT DEFAULT ''"),
    ]
    for table, col_def in migrations:
        try:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise

    # ── 索引（頻出の検索キー） ────────────────────────────
    for name, ddl in [
        ("idx_history_student_problem",
         "history(student_id, problem_id, date)"),
        ("idx_history_student_date", "history(student_id, date)"),
        ("idx_assignments_student_date",
         "assignments(student_id, scheduled_date)"),
        ("idx_assignments_problem", "assignments(problem_id)"),
        ("idx_problems_textbook_section",
         "problems(textbook_id, section_id)"),
    ]:
        c.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {ddl}")
    # セクション名は同一テキスト内で一意（section_name 指定の検索→作成が重複を作らないため）
    try:
        c.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_textbook_sections_name "
                  "ON textbook_sections(textbook_id, name)")
    except sqlite3.IntegrityError as e:
        log.warning("textbook_sections に同名セクションの重複があるため一意索引を作成できません: %s", e)
    conn.commit()
    try:
        conn.execute("PRAGMA journal_mode = WAL")
    except sqlite3.OperationalError:
        pass  # 読み取り専用FS等では無視
    conn.close()


# ─── SRSロジック ───────────────────────────────────────

INTERVAL_WEEKS_COMMON = {1: 1, 2: 3}
INTERVAL_WEEKS_MASTERY3 = {5: 6, 4: 8, 3: 12, 2: 18, 1: 24}
# 習熟度3で正答を重ねるごとに間隔を伸ばす（卒業はさせない。上限で必ず再出題する）
INTERVAL_GROWTH = 1.5
INTERVAL_MAX_WEEKS = 36
# 連続正答として数える履歴種別（自動昇格・連動は数えない）
STREAK_CATEGORIES = ("Record", "Auto", "Manual")


def get_correct_streak_c(c, student_id, problem_id):
    """
    習熟度3のまま正答した直接記録の連続回数（最新行から遡る）。
    score 3（解き直し）は数えず中断もしない。score 2 以下または習熟度3未満の行で打ち切る。
    AutoPromotion / LinkedPromotion の行は無視する。
    """
    c.execute("""
        SELECT correct, mastery, category, score FROM history
        WHERE student_id=? AND problem_id=?
        ORDER BY date DESC, history_id DESC
    """, (student_id, problem_id))
    streak = 0
    for r in c.fetchall():
        if r["category"] not in STREAK_CATEGORIES:
            continue
        score = r["score"] if r["score"] is not None else (4 if r["correct"] else 2)
        if score == 3:
            continue
        if score >= 4 and int(r["mastery"] or 1) >= 3:
            streak += 1
        else:
            break
    return streak


def get_correct_streak(student_id, problem_id):
    conn = get_connection()
    try:
        return get_correct_streak_c(conn.cursor(), student_id, problem_id)
    finally:
        conn.close()


def interval_weeks(review_value, mastery, streak=0):
    """次回出題までの週数。習熟度3は復習価値別の基準週×1.5^(連続正答-1)、上限36週"""
    if mastery <= 2:
        return INTERVAL_WEEKS_COMMON.get(mastery, 1)
    base = INTERVAL_WEEKS_MASTERY3.get(review_value, 12)
    weeks = base * (INTERVAL_GROWTH ** max(0, streak - 1))
    return min(INTERVAL_MAX_WEEKS, int(round(weeks)))


def get_next_date(review_value, mastery, last_date_str, streak=0):
    last_date = date.fromisoformat(last_date_str)
    return last_date + timedelta(weeks=interval_weeks(review_value, mastery, streak))

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
    """記録後の出題予定を再登録する。次回出題日(ISO文字列)を返す（問題が無ければ None）"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM assignments WHERE student_id=? AND problem_id=?",
              (student_id, problem_id))
    c.execute("SELECT review_value FROM problems WHERE problem_id=?", (problem_id,))
    row = c.fetchone()
    next_iso = None
    if row:
        review_value = row["review_value"]
        streak = get_correct_streak_c(c, student_id, problem_id)
        next_date = get_next_date(review_value, new_mastery, today_str, streak)
        category = {1: "Recall", 2: "Drill"}.get(new_mastery, "Reinforce")
        next_iso = next_date.isoformat()
        c.execute("""
            INSERT INTO assignments (student_id, problem_id, scheduled_date, category)
            VALUES (?, ?, ?, ?)
        """, (student_id, problem_id, next_iso, category))
    conn.commit()
    conn.close()
    return next_iso


# ─── 授業スケジュール取得 ──────────────────────────────

DOW_STR_TO_INT = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}

def decode_dows(rows):
    """class_schedule_base.dow は文字列(mon〜sun)保存。整数も許容してweekday()値に揃える"""
    result = set()
    for v in rows:
        if isinstance(v, int):
            if 0 <= v <= 6:
                result.add(v)
        elif v in DOW_STR_TO_INT:
            result.add(DOW_STR_TO_INT[v])
    return result

def get_next_class_date(student_id, subject, start_date_str):
    """教科ごとの次回授業日を取得する（上書き優先。過去日の上書きは失効）"""
    conn = get_connection()
    c = conn.cursor()

    # 上書き（都度指定）を優先。ただしstart_date_strより過去の設定は失効扱い
    c.execute("""
        SELECT next_class_date FROM class_schedule_override
        WHERE student_id=? AND subject=?
    """, (student_id, subject))
    row = c.fetchone()
    if row and row["next_class_date"] and row["next_class_date"] >= start_date_str:
        conn.close()
        return row["next_class_date"]

    # ベース曜日から次回授業日を計算
    c.execute("""
        SELECT dow FROM class_schedule_base
        WHERE student_id=? AND subject=?
        ORDER BY dow
    """, (student_id, subject))
    dows = decode_dows([r["dow"] for r in c.fetchall()])
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
    dows = decode_dows([r["dow"] for r in c.fetchall()])
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

def get_plan_v2(student_id, start_date_str, end_date_str, subject_filter=None):
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
               p.estimated_minutes, p.total_minutes, p.instruction, p.problem_id,
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
            "total_minutes": r["total_minutes"] if r["total_minutes"] else None,
            "mastery": "★" * mastery,
            "mastery_int": mastery,
            "last_date": r["last_date"] if r["last_date"] else "（初見）",
            "instruction": r["instruction"] if r["instruction"] else "",
            "problem_id": r["problem_id"],
            "textbook_id": r["textbook_id"],
            "order_in_textbook": r["order_in_textbook"] or r["problem_id"],
            "scheduled_date": r["scheduled_date"],
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

    dow_map = {0:"mon",1:"tue",2:"wed",3:"thu",4:"fri",5:"sat",6:"sun"}
    schedule = {}
    current = date.fromisoformat(start_date_str)
    end = date.fromisoformat(end_date_str)
    while current <= end:
        date_str = current.isoformat()
        dow_str = dow_map[current.weekday()]
        schedule[date_str] = overrides.get(date_str, base.get(dow_str, 0))
        current += timedelta(days=1)
    return schedule


def save_plan_history(student_id, start_date, end_date, excel_path,
                      pdf_path="", subject="", plan_data=None):
    """
    計画表の出力を記録する。
    同一student_id・subject の前回出力を確定状態にしてからINSERTする。
    """
    import json as _json
    conn = get_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    plan_json = _json.dumps(plan_data, ensure_ascii=False) if plan_data else ""

    # ── 前回出力を確定 ────────────────────────────
    # 同一生徒・教科で、前回のend_date < 今回のstart_date の
    # 未確定レコードを確定状態にする
    c.execute("""
        SELECT history_id, start_date, end_date, plan_data
        FROM plan_history
        WHERE student_id=? AND subject=? AND confirmed=0
        AND end_date < ?
        ORDER BY end_date DESC
    """, (student_id, subject, start_date))
    prev_rows = c.fetchall()
    for row in prev_rows:
        # plan_dataが空の場合はget_plan_v2で計画を生成して保存
        if not row["plan_data"]:
            try:
                prev_plan = get_plan_v2(student_id, row["start_date"], row["end_date"],
                                        subject_filter=subject if subject else None)
                prev_json = _json.dumps(prev_plan, ensure_ascii=False)
            except Exception:
                prev_json = "[]"
            c.execute("UPDATE plan_history SET confirmed=1, plan_data=? WHERE history_id=?",
                      (prev_json, row["history_id"]))
        else:
            c.execute("UPDATE plan_history SET confirmed=1 WHERE history_id=?",
                      (row["history_id"],))

    # ── 新しい出力を記録 ──────────────────────────
    c.execute("""
        INSERT INTO plan_history
        (student_id, generated_date, start_date, end_date,
         excel_path, pdf_path, subject, confirmed, plan_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
    """, (student_id, today, start_date, end_date,
          excel_path, pdf_path, subject, plan_json))
    conn.commit()
    conn.close()

def get_plan_histories(student_id=None, confirmed_only=False):
    conn = get_connection()
    c = conn.cursor()
    where = []
    params = []
    if student_id:
        where.append("ph.student_id=?")
        params.append(student_id)
    if confirmed_only:
        where.append("ph.confirmed=1")
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    c.execute(f"""
        SELECT ph.*, s.name as student_name
        FROM plan_history ph
        JOIN students s ON ph.student_id = s.student_id
        {where_sql}
        ORDER BY ph.generated_date DESC, ph.history_id DESC
    """, params)
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
          AND a.category IN ('New', 'Recall', 'Drill', 'Reinforce')
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
              1, new_mastery, "AutoPromotion"))

        review_value = row["review_value"]
        next_date = get_next_date(review_value, new_mastery, scheduled_date)
        category = {1: "Recall", 2: "Drill"}.get(new_mastery, "Reinforce")

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



# ─── 代表問題の連動（復習価値4以上の問題に正答/誤答したとき周辺問題の出題日を動かす） ───
# 2026-09-30 再設計: 周辺問題の習熟度・history は触らず assignments の日付だけを動かす。
#   正答(score>=4): 周辺の次回日を「自身の次回日と代表の次回日の遅い方」へ送る（短期の重複出題を避ける）
#   誤答(score<=2): 周辺を代表と同じ次回日に Recall で戻す
#   score 3 は何もしない。同じ日に明示記録がある問題は動かさない。
# 周辺問題の定義（優先順）:
#   1. problems.representative_of がこの代表を指す問題（明示指定。復習価値は問わない）
#   2. 代表に section_id があれば、同テキスト・同セクションで復習価値がより低い問題
#   3. section_id が無ければ、同テキストでセクション未設定かつ初回授業日（history の最初の日、
#      無ければ scheduled_date）が同じで復習価値がより低い問題（過去問・テスト直しなど
#      単元概念の無いセットの受け皿）。グループが LINK_FALLBACK_MAX 問を超える場合は連動しない。
#   明示的に別の代表を指している問題は 2・3 の対象から外す。

LINK_EXPLICIT_CATEGORIES = ("Record", "Manual", "Auto")
LINK_FALLBACK_MAX = 12  # 初回授業日フォールバックで連動させる周辺問題数の上限

_ORIGIN_SQL = """COALESCE((SELECT MIN(h.date) FROM history h
                           WHERE h.student_id=a.student_id AND h.problem_id=a.problem_id),
                          a.scheduled_date)"""


def get_linked_problems_c(c, student_id, problem_id):
    """
    代表問題 problem_id に連動する周辺問題（この生徒に出題予定があるもの）を返す。
    戻り値: [{problem_id, problem_number, textbook, assignment_id, scheduled_date, category,
              review_value, link}]  link は "explicit" / "section" / "origin_date"
    授業日未定(2099-12-31)の予定は対象外。
    """
    c.execute("""
        SELECT p.problem_id, p.subject, p.textbook_id, p.section_id, p.review_value,
               (SELECT MIN(h.date) FROM history h
                 WHERE h.student_id=? AND h.problem_id=p.problem_id) AS first_date,
               (SELECT a.scheduled_date FROM assignments a
                 WHERE a.student_id=? AND a.problem_id=p.problem_id
                 ORDER BY a.assignment_id DESC LIMIT 1) AS scheduled_date
        FROM problems p WHERE p.problem_id=?
    """, (student_id, student_id, problem_id))
    rep = c.fetchone()
    if not rep:
        return []
    rep_rv = int(rep["review_value"] or 0)
    base_select = f"""
        SELECT p.problem_id, p.problem_number, p.textbook, p.review_value,
               a.assignment_id, a.scheduled_date, a.category
        FROM assignments a JOIN problems p ON p.problem_id = a.problem_id
        WHERE a.student_id=? AND a.problem_id<>? AND a.scheduled_date<>'2099-12-31'
    """
    found = {}

    def add(rows, link):
        for r in rows:
            if r["problem_id"] not in found:
                d = dict(r)
                d["link"] = link
                found[r["problem_id"]] = d

    # 1. 明示指定
    c.execute(base_select + " AND p.representative_of=?", (student_id, problem_id, problem_id))
    add(c.fetchall(), "explicit")

    if rep["section_id"] is not None:
        # 2. 同セクション
        c.execute(base_select + """
              AND p.textbook_id=? AND p.section_id=? AND p.review_value<?
              AND (p.representative_of IS NULL OR p.representative_of=?)
        """, (student_id, problem_id, rep["textbook_id"], rep["section_id"], rep_rv, problem_id))
        add(c.fetchall(), "section")
    else:
        # 3. 同テキスト・同じ初回授業日（セクション未設定の問題どうし）
        #    一括登録日の問題をまとめて拾うと代表1問に数十問が連動するため、
        #    グループが LINK_FALLBACK_MAX を超える場合は「1回の授業のセット」とみなさず連動しない
        origin = rep["first_date"] or rep["scheduled_date"]
        if origin and origin != "2099-12-31":
            c.execute(base_select + f"""
                  AND p.textbook_id=? AND p.section_id IS NULL AND p.review_value<?
                  AND (p.representative_of IS NULL OR p.representative_of=?)
                  AND {_ORIGIN_SQL} = ?
            """, (student_id, problem_id, rep["textbook_id"], rep_rv, problem_id, origin))
            rows = c.fetchall()
            if len(rows) <= LINK_FALLBACK_MAX:
                add(rows, "origin_date")
            else:
                log.info("代表問題 %s の初回授業日グループが %d 問と大きいため連動しない（上限 %d）",
                         problem_id, len(rows), LINK_FALLBACK_MAX)

    # 重複した出題予定行がある場合は assignment_id の大きい方を採用する
    return sorted(found.values(), key=lambda d: d["problem_id"])


def get_linked_problems(student_id, problem_id):
    conn = get_connection()
    try:
        return get_linked_problems_c(conn.cursor(), student_id, problem_id)
    finally:
        conn.close()


def apply_linked_after_record_c(c, student_id, problem_id, record_date, score, explicit_ids=()):
    """
    記録済みの代表問題について周辺問題の出題予定を動かす（同一カーソル内。commit は呼び出し側）。
    代表の次回日は assignments から読むので、update_assignments_after_record の後に呼ぶこと。
    戻り値: [{problem_id, problem_number, textbook, link, action, old_date, new_date, category}]
      action: "deferred"（正答で後ろへ送った）/ "recalled"（誤答で Recall に戻した）/
              "skipped_explicit"（同日に明示記録があるため対象外）
    """
    score = int(score)
    if score == 3:
        return []
    c.execute("SELECT review_value FROM problems WHERE problem_id=?", (problem_id,))
    p = c.fetchone()
    if not p or int(p["review_value"] or 0) < 4:
        return []
    c.execute("""
        SELECT scheduled_date FROM assignments
        WHERE student_id=? AND problem_id=? ORDER BY assignment_id DESC LIMIT 1
    """, (student_id, problem_id))
    a = c.fetchone()
    if not a or a["scheduled_date"] == "2099-12-31":
        return []
    rep_next = a["scheduled_date"]

    c.execute(f"""
        SELECT DISTINCT problem_id FROM history
        WHERE student_id=? AND date=? AND category IN ({",".join("?" * len(LINK_EXPLICIT_CATEGORIES))})
    """, (student_id, record_date, *LINK_EXPLICIT_CATEGORIES))
    explicit = {int(r["problem_id"]) for r in c.fetchall()} | {int(x) for x in explicit_ids}

    results = []
    for L in get_linked_problems_c(c, student_id, problem_id):
        base = {"problem_id": L["problem_id"], "problem_number": L["problem_number"],
                "textbook": L["textbook"], "link": L["link"],
                "old_date": L["scheduled_date"], "old_category": L["category"]}
        if L["problem_id"] in explicit:
            results.append({**base, "action": "skipped_explicit",
                            "new_date": L["scheduled_date"], "category": L["category"]})
            continue
        if score >= 4:
            new_date = max(L["scheduled_date"], rep_next)
            new_cat = L["category"]
            action = "deferred"
        else:
            new_date = min(L["scheduled_date"], rep_next)
            new_cat = "Recall"
            action = "recalled"
        if new_date == L["scheduled_date"] and new_cat == L["category"]:
            continue
        c.execute("UPDATE assignments SET scheduled_date=?, category=? WHERE assignment_id=?",
                  (new_date, new_cat, L["assignment_id"]))
        results.append({**base, "action": action, "new_date": new_date, "category": new_cat})
    if results:
        log.info("代表問題連動: student=%s rep=%s score=%s → %s",
                 student_id, problem_id, score,
                 [(r["problem_id"], r["action"], r["new_date"]) for r in results])
    return results


def apply_linked_after_record(student_id, problem_id, record_date, score, explicit_ids=()):
    conn = get_connection()
    try:
        results = apply_linked_after_record_c(conn.cursor(), student_id, problem_id,
                                              record_date, score, explicit_ids)
        conn.commit()
        return results
    finally:
        conn.close()


def resolve_section_c(c, textbook_id, section_name):
    """セクション名から section_id を返す。無ければ作成する（order_index は末尾）。戻り値 (section_id, created)"""
    section_name = (section_name or "").strip()
    if not section_name:
        return None, False
    c.execute("SELECT section_id FROM textbook_sections WHERE textbook_id=? AND name=?",
              (textbook_id, section_name))
    row = c.fetchone()
    if row:
        return row["section_id"], False
    c.execute("SELECT MAX(order_index) AS m FROM textbook_sections WHERE textbook_id=?", (textbook_id,))
    max_order = c.fetchone()["m"] or 0
    c.execute("INSERT INTO textbook_sections (textbook_id, name, order_index) VALUES (?,?,?)",
              (textbook_id, section_name, max_order + 1))
    return c.lastrowid, True


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


def get_auto_next_class_date(student_id, subject):
    """
    class_schedule_overrideがあればそれを返す。
    ただし過去日の手動設定は自動失効し、class_schedule_baseの曜日から
    「今日以降の最初の授業日」を自動計算して返す。
    """
    conn = get_connection()
    c = conn.cursor()

    today = date.today()

    # overrideを確認（今日以降のもののみ有効。経過した手動設定は失効）
    c.execute("""
        SELECT next_class_date FROM class_schedule_override
        WHERE student_id=? AND subject=?
    """, (student_id, subject))
    row = c.fetchone()
    if row and row["next_class_date"] and row["next_class_date"] >= today.isoformat():
        conn.close()
        return row["next_class_date"]

    # baseの曜日から計算
    c.execute("""
        SELECT dow FROM class_schedule_base
        WHERE student_id=? AND subject=?
    """, (student_id, subject))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return None

    class_dows = decode_dows([r["dow"] for r in rows])

    for delta in range(1, 14):
        d = today + timedelta(days=delta)
        if d.weekday() in class_dows:
            return d.isoformat()

    return None


def replay_mastery(rows, since_date=None):
    """
    history の行リスト（date ASC, history_id ASC 順）を先頭から再生し、
    各行のあるべき mastery を計算して返す。
    登録時の calc_new_mastery / calc_new_mastery_v2 と同じ状態遷移を
    純粋関数として再現しており、行の削除・修正後の再計算に使う。
    since_date を指定すると、それより前の行は保存済み mastery を正として
    状態だけ引き継ぎ、since_date 以降の行のみ再計算する
    （古いロジックで記録された過去行を書き換えないための最小侵襲モード）。
    rows: [{"history_id", "date", "correct", "mastery", "category", "score"}, ...]
    戻り値: [(history_id, new_mastery), ...]（rows と同順）
    """
    result = []
    m = 1
    prior_correct_dates = []  # correct=1 だった行の日付（再生順）
    for row in rows:
        cat = row["category"]
        row_date = date.fromisoformat(row["date"])
        if since_date is not None and row["date"] < since_date:
            # 再計算対象外: 保存値を状態として引き継ぐ
            new_m = int(row["mastery"])
            if row["correct"]:
                prior_correct_dates.append(row_date)
            m = new_m
            result.append((row["history_id"], new_m))
            continue
        if cat == "Manual":
            # 手動設定はその値を正とする
            new_m = max(1, min(3, int(row["mastery"])))
        elif cat in ("AutoPromotion", "LinkedPromotion"):
            new_m = min(m + 1, 3) if row["correct"] else max(m - 1, 1)
        else:
            score = row["score"] if row["score"] is not None else (4 if row["correct"] else 2)
            if score == 3:
                new_m = m
            elif score <= 2:
                new_m = max(1, m - 1)
            elif m >= 3:
                new_m = 3
            elif m == 1:
                has_prior = any(d < row_date for d in prior_correct_dates)
                new_m = 2 if has_prior else 1
            else:  # m == 2
                last3 = sorted(prior_correct_dates, reverse=True)[:3]
                if len(last3) >= 2:
                    weeks_diff = (row_date - last3[-1]).days // 7
                    new_m = 3 if (len(last3) >= 3 and weeks_diff >= 1) else 2
                else:
                    new_m = 2
        if row["correct"]:
            prior_correct_dates.append(row_date)
        m = new_m
        result.append((row["history_id"], new_m))
    return result


def recalc_mastery_from_history(student_id, problem_id, since_date=None):
    """
    指定問題の history を日付順に再生して mastery カラムを整合させる。
    削除・修正で「最新行の mastery」が壊れた場合の復旧に使う。
    since_date 指定時はそれより前の行を書き換えない（delete_record 用の最小侵襲モード）。
    戻り値: {"rows": 総行数, "changed": 更新行数, "latest_mastery": 最新行のmastery(履歴なしならNone)}
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT history_id, date, correct, mastery, category, score
        FROM history WHERE student_id=? AND problem_id=?
        ORDER BY date, history_id
    """, (student_id, problem_id))
    rows = [dict(r) for r in c.fetchall()]
    if not rows:
        conn.close()
        return {"rows": 0, "changed": 0, "latest_mastery": None}
    replayed = replay_mastery(rows, since_date=since_date)
    changed = 0
    for row, (hid, new_m) in zip(rows, replayed):
        if row["mastery"] != new_m:
            c.execute("UPDATE history SET mastery=? WHERE history_id=?", (new_m, hid))
            changed += 1
    conn.commit()
    conn.close()
    return {"rows": len(rows), "changed": changed, "latest_mastery": replayed[-1][1]}


def auto_record_unreported(student_id, record_date):
    """
    出題予定のうち授業記録がない問題を自動登録する。
    難易度1〜3: score=5（Perfect）
    難易度4〜5: score=4（Good）
    前日以前に出題予定だった問題が対象。
    """
    conn = get_connection()
    c = conn.cursor()

    # 出題予定のうち、record_date以前で授業記録がない問題を取得
    c.execute("""
        SELECT a.assignment_id, a.problem_id, a.scheduled_date,
               p.difficulty
        FROM assignments a
        JOIN problems p ON a.problem_id = p.problem_id
        WHERE a.student_id = ?
          AND a.scheduled_date <= ?
          AND a.scheduled_date != '2099-12-31'
          AND NOT EXISTS (
              SELECT 1 FROM history h
              WHERE h.student_id = a.student_id
                AND h.problem_id = a.problem_id
                AND h.date >= a.scheduled_date
          )
        ORDER BY a.scheduled_date
    """, (student_id, record_date))
    unreported = c.fetchall()
    conn.close()

    results = []
    for row in unreported:
        difficulty = row["difficulty"] or 3
        score = 5 if difficulty <= 3 else 4
        new_mastery = calc_new_mastery_v2(
            student_id, row["problem_id"], score, row["scheduled_date"])

        conn2 = get_connection()
        c2 = conn2.cursor()
        c2.execute("""
            INSERT INTO history
            (student_id, problem_id, date, correct, mastery, category, score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (student_id, row["problem_id"], row["scheduled_date"],
              1, new_mastery, "Auto", score))
        conn2.commit()
        conn2.close()

        update_assignments_after_record(
            student_id, row["problem_id"], row["scheduled_date"], new_mastery)

        results.append({
            "problem_id":    row["problem_id"],
            "scheduled_date": row["scheduled_date"],
            "difficulty":    difficulty,
            "score":         score,
            "new_mastery":   new_mastery,
        })

    return results
