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
| templates/ | Jinja2テンプレート群 |

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

## 既知のUI上の問題（優先度中）

### 4. problems.html: Section選択が不安定
Textbook変更時にloadProblemSections()が確実に呼ばれない。
`/api/sections_by_textbook?textbook_id=`のレスポンスは正常。
**確認箇所:** problems.html内のTextbook selectのonchange属性と
loadProblemSections()関数の定義位置。

### 5. 削除確認など一部のダイアログがブラウザネイティブ
confirm()・alert()を使用している箇所があり、ブラウザ言語に依存する。
**対応方針:** 既存のカスタムモーダル（#confirm-modal）を全ページに展開する。

### 6. 操作後にページトップに戻る
フォームのPOST送信後にリダイレクトされてページ先頭に戻る。
**対応方針:** fetch APIによる非同期送信に切り替え、
成功時はDOM更新のみ行いスクロール位置を維持する。

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

## 開発方針
- DBへの直接操作は必ずバックアップ後に行う
- カテゴリ値はDBに英語で保存（New/Recall/Drill/Reinforce）
- scheduled_date='2099-12-31'は「授業日未定」を意味する
- 計画表の出力はブラウザUIから手動で行う（MCPからは実行しない）
- 削除操作は必ず確認を取ってから実行する