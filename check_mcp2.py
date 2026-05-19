with open(r"C:\Users\ynaka\study_planner\mcp_server.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("最初の80行:")
for i, line in enumerate(lines[:80], 1):
    print(f"  {i}: {line.rstrip()}")