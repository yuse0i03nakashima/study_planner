# Study Planner モバイルアプリ化・製品化 実装計画

> 目標: 既存 Flask+SQLite アプリ（Railway 稼働）を、**他の家庭教師にも配布する製品**として
> **iOS / Android 両ストア**に出す。最優先のモバイル機能は **Add Record**。
> 採用方針: **C案 = モバイル SPA + Capacitor**（既存 Flask を API として再利用）。

---

## 0. 現状（コードベース実態・2026-06 時点）

| 項目 | 実態 | 製品化での課題 |
|---|---|---|
| 認証 | `APP_PASSWORD` 1個の共有パスワード + `session`（`app.py` `require_login()`） | ユーザーテーブル無し＝**完全な単一テナント** |
| マスタデータ | `problems`/`textbooks`/`series`/`textbook_sections` は**グローバル共有**（生徒にも未紐付け） | 複数家庭教師では所有者分離が必要 |
| 生徒キー | `students.student_id` = 人手付与の `TEXT PRIMARY KEY` | テナント間で衝突しうる |
| DB | SQLite 1ファイル（`database.py get_connection()`）、`gunicorn --workers 1` | 同時書込・多worker化で破綻 → Postgres |
| API | JSON 系あり: `/api/problems_for_record`, `/record/bulk_add`, `/api/textbooks_by_student`, `/api/sections_by_textbook`, `/get_assignments`, `/record/list`, `/assignments/list` 等 | 認証はCookie前提・テナント未スコープ |
| セキュリティ | `/api/tool` が `require_login` を素通り（無認証POST） | 公開製品では塞ぐ必要 |
| 補足 | `planner.py` 分離済み（旧課題#1は解決） | — |

**結論: 今回の難所はモバイルではなくバックエンドの「単一テナント → マルチテナント」改修。** 体感で全体の約7割。

---

## 1. 目標アーキテクチャ

```
[ iOS App ]  [ Android App ]      ← Capacitor で1つのWeb(SPA)から両ストア
      \           /
   モバイルSPA(ログイン/Add Record/Assignments/Edit)
            |  HTTPS + JWT
            v
   Flask  /api/v1  (JSON, JWT認証, tutor_idでスコープ)
            |
   PostgreSQL (Railway managed)
            ^
   既存 Web(Jinja, PC管理用) … 当面はsession認証のまま併存
```

- **モバイル**: Capacitor + 軽量SPA（Svelte / Vue / 素JS いずれか。Capacitorは非依存）
- **API**: `/api/v1`、JWT（PyJWT）、全クエリ `WHERE tutor_id = ?`
- **DB**: Postgres へ移行（`get_connection()` を抽象化）
- **Web**: 既存 Jinja は PC 管理用に維持。段階的にSPA寄せも可（今回スコープ外）

---

## 2. 着手前に決める設計判断（要・確定）

| # | 論点 | 選択肢 | 推奨（暫定） |
|---|---|---|---|
| **A** | マスタデータ（textbooks/problems）の所有 | (a) 家庭教師ごとに私有 / (b) 全員共有の公式マスタ | **(a) 私有**。各自が自分の教材・問題・生徒を持つ。全テーブルに `tutor_id` |
| B | `student_id` 衝突 | サロゲートPK化 / `UNIQUE(tutor_id, student_id)` | 既存値を活かし `UNIQUE(tutor_id, student_id)` |
| C | 課金 | 無料 / サブスク / 買い切り | 初版は無料、後で検討（審査・規約に影響） |
| D | Web/モバイル認証 | 二本立て / JWT統一 | 当面 Web=session・Mobile=JWT、将来統一 |

> **A は最重要。** ここが決まらないとデータ分離の設計が始められない。
> （b を選ぶと「教材は共有、生徒/記録/出題のみ私有」となり分離範囲が変わる）

---

## 3. フェーズ別計画

### フェーズ0 — モバイル最適化 Add Record（PWA / 単一テナントのまま）
**目的**: 低リスクで即価値。実機UXとAPIを先に固め、後段でそのまま再利用。
- [ ] `record_bulk.html` をスマホ最適化（viewport、指で押しやすいスコア入力UI）
- [ ] `manifest.json` + Service Worker でインストール可能化（ホーム画面追加）
- [ ] アプリアイコン一式
- [ ] 既存 `/api/problems_for_record` → `/record/bulk_add` をそのまま使用（**Cookie認証のまま・バックエンド改修不要**）
- **検証**: iPhone / Android 実機でホーム追加 → その場で記録できる
- **規模**: 数日 / **リスク**: 低 / **再利用**: 後段SPAの土台

### フェーズ1 — マルチテナント化バックエンド（本丸・最重量）
> ⚠ DB操作前に必ずバックアップ（プロジェクト方針）。`init_db()` の既存マイグレーション方式（`migrations` リストで `ALTER TABLE ADD COLUMN`）に合わせる。

- [ ] **1-1 ユーザーモデル**: `tutors(tutor_id, email UNIQUE, password_hash, created_at)`。`werkzeug.security` でハッシュ化
- [ ] **1-2 認証**: 登録/ログインAPI、JWT発行（PyJWT）、`@jwt_required` デコレータ。Web側は当面 `session` 維持
- [ ] **1-3 データ分離（最大の工事）**: 下記テーブルに `tutor_id` 追加 → **全クエリに `WHERE tutor_id=?`**。既存データは `tutor_id=1`（あなた）に割当
  - 対象: `students, textbooks, series, textbook_sections, problems, student_textbooks, assignments, history, suppression, plan_history, class_schedule_base/override, schedule_base/override`
  - `student_id` は `UNIQUE(tutor_id, student_id)` 化
- [ ] **1-4 セキュリティ**: `/api/tool` を認証必須化 or 本番無効化
- [ ] **1-5 Postgres移行**: `get_connection()` 抽象化、SQL方言差吸収（`?`→`%s`、`AUTOINCREMENT`→`SERIAL`、`INSERT…RETURNING` 等）、Railway Managed Postgres、データ移行スクリプト
- **検証**: 2テナントでデータが**一切混ざらない**こと（自動テストで担保）
- **規模**: 数週間 / **リスク**: 高（テナント混在は致命的）

### フェーズ2 — モバイルSPA + Capacitor
- [ ] **2-1** `/api/v1` 整備（JWT前提。Add Record/Assignments閲覧/Edit Records に必要な分を確定・バージョニング）
- [ ] **2-2** SPA構築: ログイン → 生徒選択 → テキスト/セクション選択 → スコア入力 → 送信。次に Assignments 閲覧、Edit Records
- [ ] **2-3** Capacitor ラップ → iOS / Android ビルド
- [ ] **2-4** ネイティブ機能を1つ（**iOS審査4.2対策**）: プッシュ通知 or **オフライン記録キュー**（電波の弱い家庭で記録→後送信。UX上も実用的で推奨）
- **検証**: 実機ビルドで記録、両OS
- **規模**: 数週間 / **リスク**: 中

### フェーズ3 — ストア配信・法務
- [ ] **3-1** Apple Developer（$99/年）、Google Play（$25 買い切り）登録
- [ ] **3-2** プライバシーポリシー・利用規約
- [ ] **3-3** アプリ内アカウント削除（**Apple必須**）
- [ ] **3-4** 生徒データ（未成年含む）の取扱い・同意・削除導線（個人情報保護法）
- [ ] **3-5** アイコン/スクショ/掲載情報、TestFlight・内部テスト → 審査
- **検証**: 審査通過・配信
- **規模**: 数週間（審査往復含む）/ **リスク**: 中

---

## 4. 技術選定（決定事項）

| 領域 | 採用 | 理由 |
|---|---|---|
| モバイル | Capacitor + 軽量SPA | 1コードベースで両ストア、Flask再利用、学習コスト最小 |
| 認証 | PyJWT + werkzeug ハッシュ。Web=session当面維持 | モバイルはトークン必須、Webは現状維持で影響最小 |
| DB | PostgreSQL（Railway Managed）+ psycopg | 多worker・同時書込・信頼性。SQLiteは製品で破綻 |
| API | `/api/v1`（JWT） | 互換性のためバージョニング |
| Web | 既存 Jinja 維持 | PC管理用。今回は作り替えない |

**不採用**: React Native / Flutter（D案）= 新スタック学習＋2コードベース保守。premium なネイティブUXが要る段階まで保留。

---

## 5. リスクと留意点
- **データ分離漏れ＝テナント混在**（最大リスク）→ 全クエリ監査 + 自動テスト必須
- **SQLite→Postgres のSQL方言差**（raw SQL多数）→ 影響範囲広い。先に `get_connection()` 抽象化
- `gunicorn --workers 1` を製品で増やす → SQLiteだと書込ロック破綻 → **Postgres必須の根拠**
- `/api/tool` 無認証 → 塞ぐ
- **Apple 4.2リジェクト**（薄いWebラッパー不可）→ ネイティブ機能を1つ必ず足す
- オフライン: 授業現場の電波 → オフラインキューはUX・審査の両面で価値

---

## 6. 推奨着手順
1. **フェーズ0**（再利用可・即価値・低リスク）から着手
2. 並行して**設計判断A（マスタ所有モデル）を確定**
3. フェーズ1（バックエンド本丸）→ 2 → 3

## 7. 概算
| フェーズ | 規模 | リスク |
|---|---|---|
| 0 Add Record PWA | 数日 | 低 |
| 1 マルチテナント化 | 数週間 | **高** |
| 2 SPA+Capacitor | 数週間 | 中 |
| 3 ストア配信 | 数週間 | 中 |

ソロ開発で全体 **数週間〜数ヶ月**。山はフェーズ1。
