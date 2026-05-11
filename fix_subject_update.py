import sqlite3

DB_PATH = r"C:\Users\ynaka\study_planner\study_planner.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 体系数学2 幾何 → 教科を「幾何」に変更
c.execute("""
    UPDATE problems SET subject='幾何'
    WHERE textbook LIKE '体系数学2 幾何%'
""")
print(f"✅ 幾何：{c.rowcount}件更新しました")

# 体系数学2 代数 第1章Level A → 教科を「代数」、テキスト名を「体系数学2 代数」に変更
c.execute("""
    UPDATE problems
    SET subject='代数', textbook='体系数学2 代数'
    WHERE textbook LIKE '体系数学2 代数%'
""")
print(f"✅ 代数：{c.rowcount}件更新しました")

conn.commit()
conn.close()
print("✅ 完了")