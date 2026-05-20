with open(r"C:\Users\ynaka\study_planner\templates\sections.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"総行数: {len(lines)}")
# scriptタグとbuildTable関連の行だけ表示
for i, line in enumerate(lines, 1):
    if any(kw in line for kw in [
        "<script", "</script", "function ", "buildTable",
        "escHtml", "xhr.onload", "loadSection", "toggleSection"
    ]):
        print(f"{i}: {line.rstrip()}")