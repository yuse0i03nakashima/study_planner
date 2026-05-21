import os

base = r"C:\Users\ynaka\study_planner"
templates = os.path.join(base, "templates")

targets = {
    "problems.html": ["教科", "テキスト", "問題番号", "学習指示", "授業日未定", "Undecided"],
    "problems_list.html": ["教科", "テキスト", "問題番号", "学習指示", "ダブルクリック", "Imp"],
    "record_list.html": ["教科", "テキスト", "問題番号", "正誤", "習熟度", "カテゴリ"],
    "assignments_list.html": ["教科", "テキスト", "習熟度", "カテゴリ", "出題日"],
    "record.html": ["教科", "カテゴリ", "正誤"],
}

for fname, keywords in targets.items():
    fpath = os.path.join(templates, fname)
    if not os.path.exists(fpath):
        print(f"\n=== {fname}: ファイルなし ===")
        continue
    with open(fpath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    print(f"\n=== {fname} ({len(lines)}行): 該当行 ===")
    for i, line in enumerate(lines, 1):
        if any(kw in line for kw in keywords):
            # <th>や<td>や重要そうな行のみ表示
            if any(tag in line for tag in ["<th", "<td", "label", "hint",
                                            "placeholder", "Undecided", "ダブル"]):
                print(f"  {i}: {line.rstrip()}")