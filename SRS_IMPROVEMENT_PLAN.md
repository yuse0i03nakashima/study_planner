# 定着・再定着ロジック改善計画（第2版）

- 作成日: 2026-09-30（第1版）／改訂: 2026-09-30（tutor 側回答 `SRS_IMPROVEMENT_PLAN_tutor回答.md` を反映）
- 作成: Claude Code（study_planner 側レビュー）
- 状態: **2026-09-30 実装済み・本番データ複製で検証済み・コミット済み（未デプロイ＝未 push）**。Q5・Q6 は講師が (b)/(b) で決定。
  事後修正の手段（update_problem の section/representative_of、get_linked_problems、set_problem_sections）も
  同時に実装した。実装の要点は CLAUDE.md「SRS改修 v2」を参照。

## 実装メモ（第2版からの差分）
- origin_date 列は追加しなかった。初回授業日は「history の最初の日、無ければ scheduled_date」として都度導出する
  （assignments の再登録箇所が app.py / tool_handlers.py / database.py に14箇所あり、列を引き継ぐより導出のほうが壊れない）。
- 案C（representative_of の明示指定）は保留ではなく実装した。優先順は 明示 → セクション → 初回授業日。
- 間隔表の rv5 3回目は四捨五入で 14週（13.5→14）。
- 連動は add_record / add_records / Web の記録画面（単発・一括）から発火する。掃き込み（auto_record_unreported）からは発火しない。
- 初回授業日フォールバックは「同テキスト・セクション未設定」に限定し、グループが12問を超える場合は連動しない
  （本番データで一括登録日の問題を最大31問拾い、誤答時に Recall が溢れるため。database.py LINK_FALLBACK_MAX）。
- テストは DB コピー上で実施（連動の deferred / recalled / skipped_explicit、間隔伸長、事後修正ツール、週上限、Excel/PDF 出力）。
- 本番（Railway）データは読み取り専用 API で取得して複製DBを作り検証した（移行・一意索引OK、同名セクション重複なし、
  習熟度3が382問で連続正答は1回が233問、代表問題の連動グループは最大12問、S003 翌週の未割当31問→繰り越し44問に置換、
  S001 定着系 1475分→1105分）。家庭学習の時間割は API に無いためローカルDBを流用、problems.section_id は旧 get_problems が
  返さないため複製では NULL（セクション連動の検証はローカルDBコピーで実施）。
  本番 DB での section バックフィルは tutor 側の対応表を待って set_problem_sections のプレビュー→confirm で行う。
- 対象コード: database.py（SRS・代表問題処理）、tool_handlers.py（add_record / add_records / get_problems /
  update_problem）、planner.py（assign_days_v2）、app.py（起動時自動昇格）

---

## 0. 第2版での変更点（要約）

| 項目 | 第1版 | 第2版 |
|---|---|---|
| 周辺問題の定義 | 案C（明示指定）＋案A（授業日）を推奨 | **案B（セクション）本命、案A（origin_date）フォールバック**。案Cは保留 |
| 根拠 | — | 同一単元が複数授業日にまたがるのが常態（tutor 側回答 Q2 実例A〜D）。特に S004 不定積分では復習価値5の代表2問が周辺と別日に落ちている |
| 実装順 | Step 1→2→3→4→5 | **Step 3・4・5 を先行**（tutor 側の作業に依存せず、件数削減効果が最も大きい）。Step 1・2 はセクション整備後 |
| ツール追加 | なし | get_problems に section を追加、update_problem で section 変更、セクション一括バックフィルツール |
| 代表正答時の周辺の扱い | 習熟度+1＋次回日を送る | **講師判断待ち（Q5）**。study_planner 側の推奨は「習熟度を動かさず次回日だけ送る」 |

---

## 1. 講師に決めてほしいこと（Q5・Q6）

tutor 側の見解と study_planner 側の推奨は一致している。**確認のみで進められる。**

### Q5: 総合演習（代表）に正解したとき、周辺問題をどうするか
- (a) 正解扱いで習熟度+1し、次回日を代表の次回日以降へ送る
- **(b) 習熟度は動かさず、次回日だけ代表の次回日以降へ送る（推奨）**

推奨理由: 総合演習の正解は部分技能それぞれの定着を保証しない。習熟度を上げると Step 3 で間隔が
最大36週まで伸び、「忘却対策として出し続ける」目的に反する。「短期間に同じ内容を重複して出さない」
目的は日付を送るだけで達成できる。history に架空の正答行を書かなくて済むので、2026-08-18 の
掃き込み事故と同種の「解いていないのに正答記録」を構造的に避けられる。

### Q6: 総合演習に誤答したとき、周辺問題をどうするか
- (a) 習熟度-1 して代表と同じ次回日に Recall で戻す
- **(b) 習熟度は動かさず、代表と同じ次回日に Recall で戻す（推奨）**

推奨理由: Q5 と対称にし、history を書かず assignments だけ動かす。躓きの原因が周辺のどれかは
授業で確かめるので、その結果は通常の add_records で記録される。代表1問に周辺が数問戻るため、
**Step 5（週上限）とセットで入れる。**

(b)/(b) なら LinkedPromotion の history 行は書かず、ツールの戻り値と app ログに連動内容を残す。
replay_mastery・delete_record への影響もなくなる。

---

## 2. 確定した設計: 周辺問題の定義

**section_id があればセクション、無ければ origin_date（初回授業日）にフォールバック。**

- 代表: 復習価値4以上の問題。周辺: 同じ生徒・同じ textbook_id・同じ section_id の問題のうち、
  **代表より復習価値が低いもの**。同値どうしは干渉しない（1セクションに代表が複数あるのが通常のため必須）。
- section_id が NULL の問題（過去問・テスト直し・教材外の派生問題）は、同じ生徒・同じ教科・同じ
  origin_date の問題を周辺とする。S002 のテスト直し回のように単元概念が無い回はこちらが自然。
- セクションの単位は「教科書の節」（例:「38 不定積分」）。命名は tutor 側プリントの章立てと
  `problems/text/*.md` の `unit:` に合わせる。
- 案C（登録時に代表問題IDを明示）は保留。事後指定の手段が無いと推測入力になるため、案B＋案Aで
  不足が出てから検討する。

### 現状（study_planner 側で裏取り済み）
- `add_problem` は `section_name` を受け取り、既存検索→無ければ新規作成する（tool_handlers.py:569〜582）。
- `get_problems` の SELECT に section_id・セクション名が無い（tool_handlers.py:228〜231）。書けるが読めない。
- `update_problem` の更新可能フィールドに section が無い（tool_handlers.py:786）。事後修正ができない。
- `textbook_sections` に (textbook_id, name) の一意制約が無い。同名セクションの重複作成を防げない。
- ローカルDB（2026-08-05 時点）の section 付与率は 375問中228問だが、大半は速読英単語の1:1セクション。
  本番の数学教材は tutor 側報告どおり整備率が低い（Grasp 数II+B は1セクションのみ）。

---

## 3. 改善計画（実装順）

### 方針
- **卒業は導入しない**。習熟度3の連続正答で間隔を伸ばし、上限で必ず再出題する。
- tutor 側の作業（セクション整備）に依存しない Step 3・4・5 を先行し、件数膨張を先に止める。
- 代表問題ロジック（Step 1・2）は「短期間の重複を避ける」効果を主に見込む。tutor 側集計では
  代表1問あたりの周辺が平均2問程度で、件数削減効果は限定的。

### Step 3: 間隔の伸長（database.py get_next_date と tool_handlers.py のカーソル版）
| 復習価値 | 現在 | 改善後（連続正答0→1→2→3回） |
|---|---|---|
| 5 | 6週 | 6 → 9 → 14 → 20週、上限36週 |
| 4 | 8週 | 8 → 12 → 18 → 27週、上限36週 |
| 3 | 12週 | 12 → 18 → 27 → 36週 |
| 2 | 18週 | 18 → 27 → 36週 |
| 1 | 24週 | 24 → 36週 |
- 倍率1.5・上限36週は定数。連続正答は Record / Auto / Manual の correct=1 行のみ数え、
  直近の非正答（score≤2）でリセット。AutoPromotion・LinkedPromotion は数えない。
- score 3 は据え置き（間隔は現在の連続回数のまま）、score 2以下は習熟度2に落として3週サイクルへ。
- 習熟度1・2の間隔（1週・3週）は変えない。
- get_next_date の呼び出し元: database.py 4箇所（update_assignments_after_record・auto_promote_on_launch・
  process_representative_correct/wrong）、tool_handlers.py 1箇所（_update_assignments_after_record_c）。

### Step 4: 起動時自動昇格の停止（app.py・database.py）
- before_request の run_auto_promote_once_per_day と `__main__` の auto_promote_on_launch 呼び出しを止める。
- 未報告の課題は期限超過のまま残す。記録は add_records か明示的な auto_record_session で行う
  （既存の推奨フローと同じ）。既存の AutoPromotion 行は消さない。

### Step 5: 定着系の週上限（planner.py assign_days_v2）
- Recall と New の配置後、Drill と Reinforce に使える時間を週キャパの一定割合（初期値40%、定数）までに制限。
- 選ぶ順は復習価値の高い順、次に期限超過の長い順。溢れた分は「翌週へ繰り越し」として
  build_plan_data の戻り値で未割当と区別し、Excel/PDF/スナップショットでも区別して出す。
- 空き日を埋める coverage_pass は上限の範囲内で従来どおり動かす。
- Step 4 とセットで入れる（自動昇格を止めると期限超過が残るため）。Q6 の Recall 戻しもこの上限で吸収する。

### Step 2: セクション基盤の整備（tool_handlers.py・database.py）— tutor 側と並行
study_planner 側:
1. `get_problems` に section_id と section_name を追加（textbook_sections を LEFT JOIN）。
2. `update_problem` で section_id / section_name（add_problem と同じ検索→新規作成）を変更可能にする。
3. `textbook_sections` に (textbook_id, name) の一意索引を追加（init_db の migrations。重複があれば先に統合）。
4. 一括バックフィル用ツール `set_problem_sections`（引数: [{problem_id, section_name}], confirm）を追加。
   confirm 無しはプレビュー（新規作成されるセクション・上書きされる既存 section_id を列挙）、
   confirm=true で DB を `.bak_日時` にコピーしてから適用。run_migration と同じ運用。
5. assignments に origin_date を追加（フォールバック用）。add_assignment で記録し、記録後の再登録3箇所で
   引き継ぐ。既存行は history の最初の記録日、履歴の無い New は現在の scheduled_date で埋める。
6. get_same_class_problems を「section_id → origin_date フォールバック」に置き換える。
   現行の scheduled_date（家庭学習の予定日）による取得は廃止。

tutor 側（tutor 回答の「tutor 側の作業」1〜3）:
- register-problems スキルに section_name 指定を追加、登録ガイドに節名統一ルールを追記。
- `problems/text/*.md` の `unit:` と `problems:` から problem_id ↔ 節名の対応表を生成（267ファイル）。
  表記ゆれを目視確認のうえ、上記4のツールに渡す。

### Step 1: 代表問題処理の再接続（database.py・tool_handlers.py）— Step 2 の後
- add_record と add_records の両方から呼ぶ。add_records は全件記録後にまとめて処理（同一トランザクション）。
- 同じ日に明示記録がある問題は連動対象から除外する（授業での記録を上書きしない）。
- 代表正答: 周辺問題の scheduled_date を「自身の次回日と代表の次回日の遅い方」にする。
  Q5=(b) なら習熟度・history は触らない。抑制テーブル（suppression）は使わない。
- 代表誤答: 周辺問題を代表と同じ次回日に category=Recall で戻す。Q6=(b) なら習熟度・history は触らない。
- 代表が動かすのは自分より復習価値が低い問題だけ。
- 戻り値に連動した問題の一覧（problem_id・変更前後の日付・理由）を含める。
- process_representative_correct / wrong は上記仕様で書き直す（現行の +1/−1・suppression 登録は廃止）。
  suppression テーブルと get_suppression_list / clear_suppression は手動用として残す。

### 検証
- DBコピー上で、代表正答→周辺の次回日が代表以降、明示記録が上書きされない、誤答で Recall に戻ることを確認。
- 習熟度3の連続正答で次回日が表どおり伸び36週で止まることを確認。
- S003（代表が2件以上の日が24日中17日）と S004 の週間計画を改善前後で出力し、定着系の件数と合計分を比較。
- セクションバックフィルは本番DBのバックアップ上でプレビュー→適用の順で行う。
- SERVER_VERSION 更新、デプロイ後 check_connection で反映確認。

### 注意
- ローカルDBは 2026-08-05 以降更新のないコピー。数値の最終確認は本番DBのバックアップ上で行う。
- 作業ツリーの未コミット変更（UI共通化・セキュリティ強化）は別作業。先にコミットしてから着手する。
- tutor 側回答の補足（プリント規約の「部」廃止）は本計画に影響しない。

---

## 4. レビューで判明した現状（背景・第1版から変更なし）

### 代表問題ロジックが未接続
- database.py の process_representative_correct / process_representative_wrong は、
  コミット b551bae（2026-05-19、MCP全面更新）で add_record からの呼び出しが落ち、以降どこからも
  呼ばれていない。history の LinkedPromotion は 2026-05-13 の3件のみ、suppression も同日の3行のみ。
- planner.py の定着配置は代表問題を先に置くだけで件数は減らない。

### 定着・再定着が永久に周回する
- 習熟度の上限は3。3のまま正答しても次回間隔は復習価値別の固定値で伸びない。
- 起動時の auto_promote_on_launch が全生徒の期限切れ課題を「正答」として履歴に書く。
  ローカルDBでは履歴1096件中 AutoPromotion が579件で、実際の授業記録437件を上回る。
- 期限超過の課題は計画期間の全日を配置窓にするため、毎週キャパの限りに詰め込まれる。

### 現行の「周辺問題」定義が壊れている理由
- get_same_class_problems は「同じ scheduled_date を持つ assignment」で引くが、scheduled_date は
  家庭学習の予定日であって授業日ではない（tutor 側回答 フィードバック3）。前提から誤っている。
