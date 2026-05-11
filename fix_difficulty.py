import os

base = r"C:\Users\ynaka\study_planner"
excel_path = os.path.join(base, "excel_export.py")

with open(excel_path, "r", encoding="utf-8") as f:
    content = f.read()

old = '''        -difficulty,     # 高い難易度を優先（難しい問題を先に）'''
new = '''        difficulty,      # 低い難易度を優先（簡単な問題を先にウォーミングアップ）'''

if old in content:
    content = content.replace(old, new)
    with open(excel_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ 難易度の配置順を修正しました（低難易度→高難易度）")
else:
    print("❌ 対象箇所が見つかりません")