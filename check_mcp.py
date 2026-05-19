import re

with open(r"C:\Users\ynaka\study_planner\mcp_server.py", "r", encoding="utf-8") as f:
    content = f.read()

print(f"総行数: {len(content.splitlines())}")

# ツール名を抽出
tools = re.findall(r'"name"\s*:\s*"([^"]+)"', content)
print(f"\nツール数: {len(tools)}")
for t in tools:
    print(f"  {t}")

# 各ツールの引数を確認
print("\n各ツールの引数:")
for match in re.finditer(
    r'"name"\s*:\s*"([^"]+)".*?"inputSchema".*?"properties"\s*:\s*(\{[^}]+\})',
    content, re.DOTALL
):
    name = match.group(1)
    props = re.findall(r'"(\w+)"\s*:', match.group(2))
    print(f"  {name}: {props}")