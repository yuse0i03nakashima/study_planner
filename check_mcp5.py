with open(r"C:\Users\ynaka\study_planner\mcp_server.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# 338行目以降を表示
for i, line in enumerate(lines[337:420], start=338):
    print(f"  {i}: {line.rstrip()}")