# テンプレート共通レイアウト移行ガイド

`templates/base.html` + `static/css/app.css` + `static/js/ui.js` に共通部分を集約した。
新規ページも同じ流儀で作る。

## 移行状況

全20テンプレートが `base.html` 継承に移行済み（2026-09-29）。
`export.html` は削除し、`/export` は `/preview` へのリダイレクトにした。
新しいページを追加するときは以下の雛形に従う。

---

## 1. 最小の雛形

```jinja
{% extends "base.html" %}
{% set container_w = "1300px" %}          {# 省略時 1100px #}
{% set page_label = "04 / Records" %}
{% set page_title = "Assignments" %}
{% set page_title_ja = "出題予定管理" %}
{% set title_color = "var(--amber)" %}
{% set back_href = "/" %}
{% set back_label = "TOP" %}

{% block title %}Assignments — Study Planner{% endblock %}

{% block style %}
<style>
  /* このページだけで使うCSSのみ */
</style>
{% endblock %}

{% block content %}
  ...
{% endblock %}

{% block script %}
<script> ... </script>
{% endblock %}
```

`{% set %}` は **`{% extends %}` の直後・ブロックの外**に置く（ブロック内に書くと親から見えない）。

## 2. base.html のブロック

| ブロック | 用途 |
|----------|------|
| `title` | `<title>` の中身。既定 `Study Planner` |
| `head` | 追加の `<link>` / `<meta>` |
| `style` | ページ固有CSS（`<style>` タグごと書く） |
| `body_class` | `<body class="...">` に付けるクラス |
| `nav` | グローバルナビ。通常は上書き不要 |
| `header` | `.page-header`。既定は下の変数から描画。独自ヘッダーなら上書き |
| `flash` | Flash メッセージ（既定でトースト表示用の hidden DOM を出す） |
| `content` | 本文（`.container` の中） |
| `after_container` | `.container` の外に出したい要素（全画面オーバーレイ等） |
| `script` | ページ固有JS。`ui.js` の後に読まれる |

## 3. base.html が参照する変数

| 変数 | 例 | 挙動 |
|------|-----|------|
| `container_w` | `"1300px"` | `.container` の `--container-w` を上書き。既定 1100px |
| `hide_nav` | `true` | グローバルナビを出さない（index / login のみ） |
| `page_label` | `"02 / Students"` | `.page-label` |
| `page_title` | `"Students"` | `.page-title`。**未定義ならヘッダー全体を描画しない** |
| `page_title_ja` | `"生徒管理"` | `.page-title-ja` |
| `title_color` | `"var(--blue)"` | `.page-title` の文字色 |
| `back_href` | `"/"` | 右上の戻りリンク。未定義なら出さない |
| `back_label` | `"TOP"` | 戻りリンクの文言。既定 `BACK` |

グローバルナビの現在地は `request.path` の前方一致で自動判定するので、ページ側の指定は不要。

| ナビ | 色 | 前方一致するパス |
|------|----|------------------|
| 01 Master | `--red` | `/problems` `/textbooks`（`/textbooks/<id>/sections` 含む） |
| 02 Students | `--blue` | `/students` `/schedule` `/schedule_subject` `/class_schedule` |
| 03 Plan | `--green` | `/preview` `/history` |
| 04 Records | `--amber` | `/record` `/assignments` |

## 4. 削除してよい共通CSS

各テンプレートの `<style>` から、**次はすべて削除**する（app.css にある）。

- `:root { --bg … }` のトークン定義一式（`--red-main` は廃止。`--red` / `--danger` を使う）
- `*, *::before, *::after` のリセット、`body`、`body::after`（格子背景）
- `.container`
- `.page-header` `.page-label` `.page-title` `.page-title-ja` `.page-header-back`
- `.card` `.card-title`
- `label` / `label:first-child` / `input[type=…]` / `select` / `textarea` / `:focus` / `select option`
- `.btn` `.btn-sm` `.btn-primary` `.btn-success` `.btn-warn` `.btn-danger` `.btn-ghost` `.btn-purple`
- `.grid-2` `.grid-3` `.grid-4` `.row2` `.row3`
- `.data-table` とその `th` / `td` / `tr:hover` / `td.left`
- `.alert` `.alert-success` `.alert-info` `.alert-warn` `.alert-error`
- `.meta-text` `.hint` `.badge`
- `.fade-in` と `@keyframes fadeIn`
- `a { color:var(--blue) }`
- `#toast` 一式、`#confirm-modal` / `.confirm-box` / `.confirm-title` / `.confirm-message` / `.confirm-actions`
- `.tab-bar` `.tabs` `.tab-btn` `.tab-content`
- `input[type=checkbox]` の `accent-color`

**残すもの**＝そのページ固有のCSS。例：`assignments_list.html` の `.row-New` / `.editable` /
`.past-toggle-bar`、`student_detail.html` の `.subject-block`、`problems.html` の `.ai-box` など。

app.css に追加した便利クラス:

- `.table-scroll` … `overflow-x:auto`。テーブルの外側 div の inline style を置き換える
- `.empty-state` / `.empty-state .empty-title` … 0件表示
- `.data-table thead th` は `position:sticky; top:0` 済み

## 5. マークアップ側の置き換え

- `<div style="overflow-x:auto;">` → `<div class="table-scroll">`
- `#toast` と `#confirm-modal` のマークアップは **base.html にあるのでページから削除**する
- ローカル定義の `showToast` / `openConfirm` / `closeConfirm` / `confirmDelete` も削除する
- Flash メッセージの `{% with messages = get_flashed_messages(...) %}` ブロックは
  base.html が処理してトースト表示するので **ページから削除**する
  （`.alert` として画面に残したい場合だけ `{% block flash %}` を上書きする）

## 6. `data-confirm`（削除確認）

`confirm()` や独自モーダルの代わりに、POSTフォームへ属性を付けるだけでよい。

```html
<form method="POST" action="/textbooks/delete/{{ t.textbook_id }}"
      data-confirm="{{ t.name }} を削除しますか？"
      data-confirm-title="Confirm Delete"
      data-confirm-ok="Delete">
  <button type="submit" class="btn btn-danger btn-sm">×</button>
</form>
```

| 属性 | 既定 | 意味 |
|------|------|------|
| `data-confirm` | （必須） | モーダル本文。空なら確認しない |
| `data-confirm-title` | `Confirm` | モーダル見出し |
| `data-confirm-ok` | `OK` | OKボタンの文言 |
| `data-confirm-danger` | `true` | `false` にすると赤ではなく青（非破壊的操作用） |

`ui.js` が `submit` を捕まえてモーダルを出し、OK のときだけ再 submit する。
テーブル内のインラインフォームは `display:inline` にしておくとレイアウトが崩れない。

## 7. JS API（`static/js/ui.js`）

```js
showToast('保存しました');              // 既定 success
showToast('未保存の変更があります', 'warn');
// type: 'success' | 'info' | 'warn' | 'error'

const ok = await showConfirm({
  title: 'Confirm Delete',
  message: 'この記録を削除しますか？',
  okLabel: 'Delete',
  danger: true            // false で青（非破壊的）
});
if (ok) { /* 実行 */ }
```

- `showConfirm` は `Promise<boolean>` を返す。Esc キー・背景クリック・Cancel で `false`。
- `#confirm-modal` が無いページでは `window.confirm` にフォールバックする。
- Flash メッセージは base.html が自動でトースト化する（`success` / `info` / `warn` / `error`。
  `danger` は `error`、`message` は `info` に丸められる）。

## 8. アクセシビリティ / レスポンシブの約束

- 本文 `line-height:1.7`。日本語本文は 13px 以上、ラベル・メタ表記は最小 10px。
- `--text-dim` は `#7b84a3`（コントラスト 4.5:1 以上）。これより暗い色を新規に使わない。
- `:focus-visible` のアウトラインは app.css で共通指定済み。ページ側で `outline:none` を足さない。
- `@media (max-width:640px)` で `.grid-*` / `.row*` は自動で1列、`.page-header` は縦積みになる。
  ページ固有のグリッドを足す場合は同じブレークポイントで1列にするCSSを添える。
- 横に広いテーブルは必ず `.table-scroll` で包む（body 自体を横スクロールさせない）。
