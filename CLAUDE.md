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
| database.py | DB接続・get_plan_v2・SRSロジック |
| excel_export.py | Excel出力 + **計画生成ロジック build_plan_data()・assign_days_v2()** |
| pdf_export.py | PDF出力（build_plan_dataをexcel_export.pyからimport） |
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

### 1. 計画生成ロジックの分離（リファクタリング）
build_plan_data()・assign_days_v2()がexcel_export.pyに存在している。
本来はplanner.pyとして独立させるべき。
現状pdf_export.pyもexcel_export.pyからimportしているため影響範囲が広い。
**対応方針:** planner.pyを新規作成し、excel/pdf_export.pyからimportする形に変更。

### 2. SRS自動登録が安定しない
仕様：出題予定日を過ぎてadd_recordが呼ばれた際、未記録の問題を
難易度1〜3はscore=5(Perfect)、難易度4〜5はscore=4(Good)で自動登録し、
習熟度・カテゴリを自動更新する。
**症状:** 自動登録・カテゴリ昇格が動作しない場合がある。
**確認箇所:** database.pyのget_plan_v2・mcp_server.pyのadd_record処理。

### 3. Add Recordが反映されない場合がある
手動でadd_recordを実行しても習熟度・カテゴリが更新されないケースがある。
**確認箇所:** mcp_server.pyのcalc_new_mastery関数・add_record処理。

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

## 開発方針
- DBへの直接操作は必ずバックアップ後に行う
- カテゴリ値はDBに英語で保存（New/Recall/Drill/Reinforce）
- scheduled_date='2099-12-31'は「授業日未定」を意味する
- 計画表の出力はブラウザUIから手動で行う（MCPからは実行しない）
- 削除操作は必ず確認を取ってから実行する