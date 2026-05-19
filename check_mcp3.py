import re

with open(r"C:\Users\ynaka\study_planner\mcp_server.py", "r", encoding="utf-8") as f:
    content = f.read()

# Tool名を抽出
tools = re.findall(r'name="([^"]+)"', content)
print(f"ツール数: {len(tools)}")
for t in tools:
    print(f"  {t}")

# handle_tool_callのif/elif分岐を確認
handlers = re.findall(r'tool_name == "([^"]+)"', content)
print(f"\nハンドラ数: {len(handlers)}")
for h in handlers:
    print(f"  {h}")