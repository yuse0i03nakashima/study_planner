import sqlite3

DB = r"C:\Users\ynaka\study_planner\study_planner.db"
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# assignmentsテーブルのカテゴリ分布
print("=== assignments.category ===")
c.execute("""
    SELECT category, COUNT(*) as cnt
    FROM assignments
    GROUP BY category
    ORDER BY cnt DESC
""")
for r in c.fetchall():
    print(f"  '{r['category']}': {r['cnt']}件")

# historyテーブルのカテゴリ分布
print("\n=== history.category ===")
c.execute("""
    SELECT category, COUNT(*) as cnt
    FROM history
    GROUP BY category
    ORDER BY cnt DESC
""")
for r in c.fetchall():
    print(f"  '{r['category']}': {r['cnt']}件")

conn.close()