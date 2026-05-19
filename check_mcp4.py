with open(r"C:\Users\ynaka\study_planner\mcp_server.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# call_toolデコレータの周辺を表示
for i, line in enumerate(lines):
    if "call_tool" in line or "tool_name" in line or "arguments" in line.lower():
        start = max(0, i-1)
        end = min(len(lines), i+3)
        for j in range(start, end):
            print(f"  {j+1}: {lines[j].rstrip()}")
        print()
        if i > 300:
            break