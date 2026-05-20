import re

checks = {
    r"C:\Users\ynaka\study_planner\database.py": [
        "interleaved_yosyu", "expanded_yosyu", "予習：No.順"
    ],
    r"C:\Users\ynaka\study_planner\excel_export.py": [
        "problem_number", "prob_text", "Problem列"
    ],
    r"C:\Users\ynaka\study_planner\app.py": [
        "INSERT INTO problems", "total_minutes", "order_in_textbook"
    ],
    r"C:\Users\ynaka\study_planner\templates\preview.html": [
        "problem_number", "session_total", "item\."
    ],
    r"C:\Users\ynaka\study_planner\templates\problems.html": [
        "estimated_minutes", "total_minutes", "Est\."
    ],
}

for path, keywords in checks.items():
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    fname = path.split("\\")[-1]
    print(f"\n=== {fname} ({len(lines)}行) ===")
    for i, line in enumerate(lines, 1):
        if any(re.search(kw, line) for kw in keywords):
            print(f"  {i}: {line.rstrip()}")