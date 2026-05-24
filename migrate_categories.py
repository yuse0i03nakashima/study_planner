import sqlite3, shutil, os
from datetime import datetime

DB = r"C:\Users\ynaka\study_planner\study_planner.db"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# バックアップ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
backup = DB + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(DB, backup)
print(f"✅ バックアップ作成: {backup}")

conn = sqlite3.connect(DB)
c = conn.cursor()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. assignments.category を英語に統一
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
asgn_map = {
    "予習": "New",
    "復習": "Recall",
    "定着": "Drill",
    "再定着": "Reinforce",
}
for ja, en in asgn_map.items():
    c.execute("UPDATE assignments SET category=? WHERE category=?", (en, ja))
    print(f"✅ assignments: {ja}→{en} ({c.rowcount}件)")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. history.category を英語に統一
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
hist_map = {
    "記録":        "Record",
    "自動登録":    "Auto",
    "手動修正":    "Manual",
    "自動昇格":    "AutoPromotion",
    "代表問題連動": "LinkedPromotion",
}
for ja, en in hist_map.items():
    c.execute("UPDATE history SET category=? WHERE category=?", (en, ja))
    print(f"✅ history: {ja}→{en} ({c.rowcount}件)")

conn.commit()
conn.close()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 確認
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
conn2 = sqlite3.connect(DB)
conn2.row_factory = sqlite3.Row
c2 = conn2.cursor()

print("\n=== 移行後: assignments.category ===")
c2.execute("SELECT category, COUNT(*) as cnt FROM assignments GROUP BY category ORDER BY cnt DESC")
for r in c2.fetchall():
    print(f"  '{r['category']}': {r['cnt']}件")

print("\n=== 移行後: history.category ===")
c2.execute("SELECT category, COUNT(*) as cnt FROM history GROUP BY category ORDER BY cnt DESC")
for r in c2.fetchall():
    print(f"  '{r['category']}': {r['cnt']}件")

conn2.close()
print("\n✅ マイグレーション完了")