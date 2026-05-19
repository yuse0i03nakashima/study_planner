templates = r"C:\Users\ynaka\study_planner\templates"
import os
with open(os.path.join(templates, "preview.html"), "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, line in enumerate(lines):
    if any(x in line for x in ["form", "input", "select", "button", "name=", "action"]):
        print(f"{i+1}: {line.rstrip()}")