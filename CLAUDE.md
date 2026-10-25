# Study Planner 開発引き継ぎ

## システム概要
Flask+SQLiteによる家庭教師向け学習計画管理システム。
家庭教師（ゆうせい）が複数の生徒の学習計画・授業記録・問題管理を行う。

## 環境
- Python: `C:\Users\ynaka\AppData\Local\Programs\Python\Python312\python.exe`
- DB: `C:/Users/ynaka/study_planner/study_planner.db`
- 起動: `python app.py` → http://127.0.0.1:5000
- MCP: Claude Desktop経由でmcp_server.pyに接続済み

## カテゴリ（assignments.category・history.categoryともにDB内は英語で保存）
| 英語 | 意味 |
|------|------|
| New | 予習（初めて扱う問題） |
| Recall | 復習 |
| Drill | 定着 |
| Reinforce | 再定着 |

history.categoryの種別：Record / Auto / Manual / AutoPromotion / LinkedPromotion

## 主要ファイル
| ファイル | 役割 |
|----------|------|
| app.py | Flaskアプリ本体（ルーティング・DB操作） |
| database.py | DB接続（get_connection・DB_PATHのSSOT）・get_plan_v2・SRSロジック |
| planner.py | 計画生成ロジック build_plan_data()・assign_days_v2() |
| excel_export.py | Excel出力（build_plan_dataをplanner.pyからimport） |
| pdf_export.py | PDF出力（build_plan_dataをplanner.pyからimport） |
| tool_handlers.py | MCPツール実装（mcp_server.pyとapp.pyの/api/toolで共用） |
| mcp_server.py | Claude Desktop向けMCPサーバー |
| templates/ | Jinja2テンプレート群（全ページ base.html 継承。雛形は templates/_MIGRATION.md） |
| templates/base.html | 共通レイアウト（head・グローバルナビ・ページヘッダー・Flash→トースト・確認モーダル） |
| static/css/app.css | 共通CSS（デザイントークン・部品・@media）。ページ固有CSSは各テンプレートの {% block style %} |
| static/js/ui.js | showToast() / showConfirm() / form[data-confirm] の共通ハンドラ |

## DBスキーマ（主要テーブル）
- students: student_id, name, subjects
- textbooks: textbook_id, name, subject, series_id
- textbook_sections: section_id, textbook_id, name, order_index
- student_textbooks: student_id, textbook_id
- problems: problem_id, subject, textbook, textbook_id, section_id,
            problem_number, importance, difficulty, review_value,
            estimated_minutes, total_minutes, instruction, order_in_textbook
- assignments: assignment_id, student_id, problem_id, scheduled_date,
               category, session_index, total_sessions
- history: history_id, student_id, problem_id, date, correct,
           mastery, category, score

## 既知の設計上の問題（優先度高）

### 1. 計画生成ロジックの分離（✅解決済み 2026-07以前）
planner.py に build_plan_data()・assign_days_v2() を分離済み。
excel_export.py / pdf_export.py はともに planner.py から import している。

### 2. SRS自動登録が安定しない（✅解決済みとみられる・経過観察中）
仕様：出題予定日を過ぎてadd_recordが呼ばれた際、未記録の問題を
難易度1〜3はscore=5(Perfect)、難易度4〜5はscore=4(Good)で自動登録し、
習熟度・カテゴリを自動更新する。
**現状(2026-07-07検証):** database.py の auto_record_unreported() として実装済み。
add_record(tool_handlers.py:429)から自動発火するほか、専用MCPツール auto_record_session でも実行可。
DBコピー上での機能テストで仕様どおり動作を確認(難易度3→score=5、習熟度更新OK)。
再発した場合の確認箇所: database.py auto_record_unreported / calc_new_mastery_v2。

### 3. Add Recordが反映されない場合がある（✅解決済みとみられる・経過観察中）
関連修正コミット: 21f602c(未チェック行が記録されるバグ)・245c9e9(手動記録でAuto記録を上書き)・
985c4fa(bulk記録の習熟度計算)。calc_new_mastery は現在 tool_handlers.py:41 と database.py:222 にある。
再発した場合はこの2箇所と add_record 処理(tool_handlers.py:417周辺)を確認。

## UI共通化（2026-09-29 実施）
templates を base.html + static/css/app.css + static/js/ui.js に集約した。旧「既知のUI上の問題」4〜6は解消済み。
- **4. Section選択の不安定**: 原因は onchange の3経路混在・古いfetch応答の上書き・プログラム選択で change 非発火・
  登録後 form.reset()。problems.html で change リスナー一本化・リクエスト連番・選択復元で修正。
- **5. ネイティブ confirm()/alert()**: 全廃。削除は `<form data-confirm="...">` か `showConfirm({danger:true})` 経由。
- **6. POST後の先頭復帰**: schedule 系は sessionStorage でスクロール位置を復元。他は fetch 化済み。
- ナビ体系: 01 Master(赤)=/problems,/textbooks / 02 Students(青)=/students,/schedule*,/class_schedule /
  03 Plan(緑)=/preview,/history / 04 Records(橙)=/record*,/assignments。base.html が request.path で現在地を判定。
- 旧ライトテーマの export.html は削除（`/export`→`/preview` リダイレクト、`/export_pdf` は削除。
  旧経路は export 関数の旧シグネチャを呼んでおり常時500だった）。
- `:root { color-scheme: dark }` でネイティブ部品もダーク描画。`--text-dim` は #7b84a3（AA準拠）。

## セキュリティ・運用設定（2026-09-29 実施）
- **本番（環境変数 RAILWAY_ENVIRONMENT あり）では SECRET_KEY と APP_PASSWORD が未設定だと起動時に RuntimeError**。
  Railway の Variables に両方入っていることをデプロイ前に確認する。ローカルは従来どおり未設定でも動く。
- 秘密情報の比較は app.py `_secret_equal()`（hmac.compare_digest）。login の next は `_safe_next()` で相対パスのみ許可。
- Cookie: HttpOnly / SameSite=Lax / 本番のみ Secure。MAX_CONTENT_LENGTH=64MB。
- `/admin/db-restore` は SQLite ヘッダと integrity_check を検証し、既存DBを `.bak_日時` に退避してから差し替える。
- `run_migration` の apply / reassign_ids は confirm=true 必須。実行前に DB を `.bak_日時` にコピーする。
- `/api/tool` の定義を `if __name__` ブロックより前に移動（従来 `python app.py` 起動では404だった）。
- database.py: get_connection に busy_timeout/foreign_keys、init_db で history/assignments/problems に索引作成、WAL 有効化。
  実在生徒のシードデータは削除した（本番DBには影響なし）。
- history.category の書き込みは英語（Record / Manual）に統一（旧 "記録"/"手動修正"。実DBは既に全件英語）。
- ログは logging（print 廃止）。LOG_LEVEL 環境変数で制御。

## 授業報告の記録フロー（2026-08-23 追加）
2026-08-18 の事故（add_record 1回で auto_record_unreported が30件を一括done、
うち4件は授業で扱っていないのに正答記録）を受けてツールを拡張した。

**推奨フロー:**
1. `add_records`（student_id, date, records=[{problem_id, score}, ...]）で
   授業で実際に扱った問題だけを明示スコアで一括記録（1トランザクション・既定でsweepなし）
2. バックログを掃き込みたい場合のみ `auto_record_session` を明示的に呼ぶ
   （または add_records に auto_sweep=true。sweepは最後に1回だけ実行される）
3. 誤記録は `get_history` で history_id を確認 → `delete_record`（confirm=true必須。
   confirmなしはプレビューのみ返す）で取り消し。削除後は mastery を自動再計算し
   出題予定も復元する（履歴が空になったら削除日の日付・category=New で復元）
4. `recalc_mastery` は履歴全体をリプレイして mastery カラムを整合させる修復ツール
   （delete_record は削除日以降だけ再計算する最小侵襲。全体リプレイは古い行も
   書き換わりうるので、明示的に依頼された場合のみ使う）

- `add_record` は後方互換のまま（省略時 auto_sweep=true で従来どおり掃き込み）。
  auto_sweep=false で掃き込み抑止可。
- mastery 再計算ロジック: database.py replay_mastery / recalc_mastery_from_history
- check_connection はリモートの get_server_info（version・tools一覧）を返すようになった。
  デプロイ後の新ツール反映確認に使う。tool_handlers.py の SERVER_VERSION を更新すること。

## 日別配置ロジック v2（2026-09-20 再設計）
planner.py assign_days_v2 を再設計した。設計思想：予復習が大半・週前半=復習系・後半=予習系。

- **復習(Recall)を最初に配置**。scheduled_date が対象教科の授業日なら「授業前日まで」、
  そうでなければ「scheduled_dateまで」を候補窓とする（仕様保証）。窓内に収まらない場合のみ
  scheduled_dateまで→全日の順でフォールバック。候補日の中では**余裕時間（残りキャパ）が
  最大の日**を選び、日別の余裕を均す（2026-09-20 v4: 件数均等だと大キャパ日と小キャパ日が
  同じ問題数になり部活日が厳しくなるため。定着系も同方式）。
- **予習(New)は締切(scheduled_date)ごとにグループ化**し、番号順（テキスト間インターリーブ）を
  保ったまま「後半寄り重み(0.35→1.0)×曜日別キャパ」の水充填(water_fill)で日別クォータを決め、
  日ポインタを単調に進めて割り当てる。→ 同一締切内の番号順は構造的に崩れない。
  予習が大半の週は前半の大キャパ日へ番号の小さい側から自然に溢れ、小キャパ日は比例配分で
  上限に張り付かない。締切が異なる問題間では締切遵守が番号順に優先される（正常動作）。
  予習型/演習型のモード分けは不要（scheduled_date が窓を決めるため両運用に対応）。
- 定着・再定着は従来どおり残り時間に均等分散。ただし全カテゴリ通して1問もない日を
  最優先で埋める（空き日の解消）。
- **空き日カバレッジ（coverage_pass）**: 配置後、キャパがあるのに割当0問の日へ、
  制約（番号順・授業前日・締切・キャパ）を守れる問題を1問移す。
  直接移動（2問以上の日から。新たな空き日を作らない）→ カスケード左詰め
  （空き日以降の問題を番号順を保ったまま1日ずつ詰める）の順で試す。
  課題数が日数より少ない週は埋められないが、**前倒しは行わない**
  （前倒しが必要な場合は講師が問題登録を修正する運用）。埋まらなかった日は
  build_plan_data の戻り値 `empty_days` で明示され、get_plan_days・スナップショットにも含まれる。
- scheduled_date が計画期間より過去（期限超過）の課題は週全体を配置窓として扱う。
- バグ修正: class_schedule_base.dow は文字列(mon〜sun)保存だが、database.py の
  get_class_dates_in_range / get_next_class_date が整数比較しており常に空を返していた
  （decode_dows で両対応に修正。復習の授業前日保証はこの修正で機能する）。
- バグ修正: set_next_class_date の手動設定日は経過後に自動失効し、授業曜日からの未来日へ
  フォールバックする（tool_handlers.py / database.py の get_auto_next_class_date。
  get_class_schedule は失効した設定を expired_override として返す）。

## 計画スナップショット（2026-09-20 追加）
- ブラウザUIから Excel/PDF を出力すると、出力時点の日別配置が plan_history.plan_data に
  days_v1 形式で保存される（app.py /preview → planner.plan_days_snapshot）。
- `get_plan_days` に source パラメータを追加: "snapshot" で保存済み配置（=生徒の手元の計画表）を
  参照。該当スナップショットが無ければ再計算し source="live"・snapshot_found=false を返す。
  homework_watch の取り組み確認は source="snapshot" を推奨。
- `/api/export_plan`（2026-09-21 追加）からの出力でも同じスナップショットが plan_history.plan_data に
  保存される（/preview と同一経路・同一の `_make_snapshot()` 相当処理）。
  homework_watch が参照するため、この保存は省略しないこと。

## 計画表出力API `/api/export_plan`（2026-09-21 追加）
- `POST /api/export_plan`、認証は `/api/tool` と同じ `X-API-Key`（環境変数 `RAILWAY_API_KEY`）。
- JSONボディ: `student_id`(必須) / `start_date`(必須 YYYY-MM-DD) / `end_date`(必須 YYYY-MM-DD) /
  `subject`(任意・空=全教科) / `section_ids`(任意 intリスト) / `format`("excel"既定|"pdf") /
  `theme`("dark"既定|"light")。
- 成功時はファイル本体を attachment で返し、plan_history にスナップショット付きで記録する。
  必須欠落・不正値=400、認証失敗=401、計画データなし=404（`{"error": "no plan data"}`）。

## SRS改修 v2（2026-09-30 実装）
設計と経緯は `SRS_IMPROVEMENT_PLAN.md`（第2版）と `SRS_IMPROVEMENT_PLAN_tutor回答.md` を参照。

- **間隔伸長（卒業なし）**: 習熟度3で正答を重ねるごとに `基準週 × 1.5^(連続正答-1)`、上限36週で必ず再出題。
  基準週は復習価値別（5:6 / 4:8 / 3:12 / 2:18 / 1:24）。連続正答は Record/Auto/Manual の score≥4 行のみ
  数え、score 3 は据え置き（数えず中断もしない）、score≤2 で習熟度2に落ちてリセット。
  AutoPromotion / LinkedPromotion は数えない。database.py `get_correct_streak_c` / `interval_weeks` / `get_next_date(…, streak)`。
- **代表問題の連動（再稼働）**: 復習価値4以上の問題を add_record / add_records / Web記録で記録すると
  `apply_linked_after_record` が周辺問題の **assignments の日付だけ** を動かす（習熟度・history は触らない）。
  正答(score≥4): 周辺の次回日を「自身の次回日と代表の次回日の遅い方」へ送る。誤答(score≤2): 代表と同じ次回日に
  Recall で戻す。score 3 は何もしない。同じ日に明示記録した問題は動かさない。戻り値 `linked` に内容が出る。
  auto_record_unreported（掃き込み）からは発火しない。旧 process_representative_* / suppression 登録は廃止
  （suppression テーブルと get_suppression_list / clear_suppression は手動用に残置）。
- **周辺問題の定義**（`get_linked_problems_c`、優先順）: ① problems.representative_of がその代表を指す問題（明示）
  ② 代表に section_id があれば同テキスト・同セクションで復習価値がより低い問題（同値どうしは干渉しない）
  ③ セクション無しなら同テキスト・セクション未設定で初回授業日（history の最初の日、無ければ scheduled_date）が
  同じで復習価値がより低い問題。ただしグループが LINK_FALLBACK_MAX=12 問を超える場合は連動しない
  （本番検証で一括登録日の問題を最大31問拾ったため）。別の代表を明示している問題は②③から外れる。
  scheduled_date は家庭学習の予定日なのでグループ化に使わない。
- **事後修正ツール**: `update_problem` に section_id / section_name（検索→無ければ作成）/ representative_of（null で解除）
  を追加。`get_linked_problems`（student_id, problem_id）で連動対象を確認。`set_problem_sections`（entries, confirm）で
  セクションを一括バックフィル（confirm 無しはプレビュー、適用前に DB を .bak_日時 にコピー）。
  `get_problems` は section_id / section_name / representative_of を返す。textbook_sections(textbook_id, name) に一意索引。
- **起動時自動昇格は既定で停止**（app.py `AUTO_PROMOTE_ON_LAUNCH`、環境変数 AUTO_PROMOTE_ON_LAUNCH=1 で従来動作）。
  未報告は期限超過のまま残り、記録は add_records か明示的な auto_record_session で行う。
- **定着系の週上限**（planner.py `TEICHAKU_CAP_RATIO=0.40`）: Drill/Reinforce に使う時間を週キャパ（教科別スケジュール
  使用時は教科ごと）の40%まで。選抜順は `teichaku_priority`（復習価値高→期限超過が長い→習熟度低）。溢れた分は
  build_plan_data の `carried_over`（翌週へ繰り越し）として未割当と区別され、Excel/PDF の「CARRY OVER」ブロック、
  スナップショット、get_plan_days の `carried_over` に出る。assignments は残るので翌週に再候補になる。
- SERVER_VERSION = 2026-09-30-srs-linked-v2。

## 開発方針
- DBへの直接操作は必ずバックアップ後に行う
- カテゴリ値はDBに英語で保存（New/Recall/Drill/Reinforce）
- scheduled_date='2099-12-31'は「授業日未定」を意味する
- 計画表の出力はブラウザUIまたは `/api/export_plan`（X-API-Key認証）から行う。
  Claude Codeからの出力は講師のプレビュー承認後のみ実行する（tutor側 `/plan-export` スキル参照）
- 削除操作は必ず確認を取ってから実行する
## 生徒の削除（2026-10-25 追加）
- MCPツール `delete_student`（student_id, confirm）。confirm なしは関連テーブルごとの削除件数プレビューのみ。
  confirm=true で DB を `.bak_日時` にバックアップ（sqlite backup API）してから、tool_handlers.py の
  `STUDENT_TABLES`（history・assignments・suppression・plan_history・各スケジュール・student_textbooks）と
  students 行を1トランザクションで削除する。問題マスタ・テキストは残す。
- Web UI: 生徒詳細の Profile タブ末尾「Delete Student」（確認モーダル経由で POST /students/<id>/delete）。
- 生徒IDを参照するテーブルを増やしたら `STUDENT_TABLES` に追加すること。
