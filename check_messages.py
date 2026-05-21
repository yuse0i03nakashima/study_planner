import os, re

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")

# 日本語文字を含む行を抽出（CSSクラス名・変数名・コメントは除く）
ja_pattern = re.compile(r'[ぁ-んァ-ン一-龥]')

for fname in sorted(os.listdir(templates)):
    if not fname.endswith(".html"):
        continue
    fpath = os.path.join(templates, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    hits = []
    for i, line in enumerate(lines, 1):
        # Jinja2テンプレート変数・CSSクラス・コメントは除外
        stripped = line.strip()
        if stripped.startswith("{#"):  # Jinja2コメント
            continue
        # showToast・confirm・alert・placeholder・hint・label内の日本語
        if ja_pattern.search(line):
            if any(kw in line for kw in [
                "showToast", "confirm(", "alert(", "placeholder",
                "hint", "label", "title", "textContent",
                "innerHTML", "console", "message", "Toast",
                "toastMsg", "warn", "info", "success",
                "delete", "Delete", "×", "✓"
            ]):
                hits.append(f"  {i}: {line.rstrip()}")

    if hits:
        print(f"\n=== {fname} ===")
        for h in hits:
            print(h)

# app.pyのflash/jsonifyメッセージも確認
app_path = os.path.join(base, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    app_lines = f.readlines()

print("\n=== app.py: 日本語メッセージ ===")
for i, line in enumerate(app_lines, 1):
    if ja_pattern.search(line) and any(kw in line for kw in [
        "jsonify", "flash", "message", "error", "return"
    ]):
        print(f"  {i}: {line.rstrip()}")