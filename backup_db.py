"""study_planner.db を OneDrive へバックアップする。

タスクスケジューラ(タスク名: StudyPlannerBackup, 週次 日曜21:00)から実行される。
手動実行も可: python backup_db.py
sqlite3 の backup API を使うため、アプリ稼働中でも整合性のあるコピーが取れる。
KEEP 世代を超えた古いバックアップは自動削除する。
"""
import glob
import os
import sqlite3
from datetime import datetime

SRC = os.path.join(os.path.dirname(__file__), 'study_planner.db')
DST_DIR = r'C:\Users\ynaka\OneDrive\Backups\study_planner'
KEEP = 8

def main():
    os.makedirs(DST_DIR, exist_ok=True)
    dst = os.path.join(DST_DIR, f"study_planner_{datetime.now():%Y%m%d_%H%M%S}.db")
    src = sqlite3.connect(SRC)
    out = sqlite3.connect(dst)
    try:
        with out:
            src.backup(out)
    finally:
        out.close()
        src.close()

    backups = sorted(glob.glob(os.path.join(DST_DIR, 'study_planner_*.db')))
    for old in backups[:-KEEP]:
        os.remove(old)
    print(f"backup OK: {dst} (保持 {min(len(backups), KEEP)} 世代)")

if __name__ == '__main__':
    main()
