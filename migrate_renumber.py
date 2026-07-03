#!/usr/bin/env python3
"""problem_id / order_in_textbook(no) 再編マイグレーション。

方式: 新id = textbook_id*10000 + 新no
  - no はテキストごとの規則で problem_number から実行時算出(compute_new_no)。
  - problem_id を新idへ再割当し、history/assignments/suppression を連鎖更新。
  - 重複/テストデータ/テストtextbook・S000・テストseries を削除。

CLI:  python migrate_renumber.py --db study_planner.db [--apply]
tool: handle_tool("run_migration", {"mode": "dry_run"|"apply"})  (tool_handlers から run() を呼ぶ)

安全策: 既定 dry-run。apply 時はファイルバックアップ+単一トランザクション+孤児FK検証で rollback。
"""
import argparse, re, shutil, sqlite3, sys, time
from collections import defaultdict, Counter

# ── 承認済みの削除・上書き(Railway id基準) ─────────────────
DELETE_DUP = {366, 367, 368, 280, 281, 362}            # 重複の削除側
DELETE_SHIKKARI = {611, 612, 613, 614, 615, 696, 697}  # しっかり末尾の不要問題
OVERRIDE_NO = {698: 34, 90: 163}                       # PART3まとめ→34, 発展演習→163
TEST_TEXTBOOK_ID = 21
TEST_STUDENT_ID = "S000"
TEST_SERIES_ID = 9


def _num(pat, s):
    m = re.search(pat, s); return int(m.group(1)) if m else None


def compute_new_no(rows):
    """surviving問題の pid -> 新no と、算出不能 flags を返す。"""
    out, flags = {}, []
    jissen = defaultdict(list)   # 古文の実戦問題(課ごとに分割連番)
    for r in sorted(rows, key=lambda x: (x["order_in_textbook"], x["problem_id"])):
        pid, tid, pn = r["problem_id"], r["textbook_id"], (r["problem_number"] or "")
        if pid in OVERRIDE_NO:
            out[pid] = OVERRIDE_NO[pid]; continue
        if tid == 2:  # 古文: 文法問題n→10n+1, 実戦問題n→10n+2(分割は+3,+4)
            mg = re.match(r"文法問題(\d+)", pn); mj = re.match(r"実戦問題(\d+)", pn)
            if mg:   out[pid] = 10*int(mg.group(1)) + 1
            elif mj: jissen[int(mj.group(1))].append(pid)
            else:    flags.append((pid, tid, pn))
            continue
        no = None
        if tid in (1, 3):    no = _num(r"大問(\d+)", pn)
        elif tid in (15, 16):
            if "EXERCISE" in pn.upper():
                n = _num(r"EXERCISES?\s*(\d+)", pn); no = 9000+n if n else None
            elif "例題" in pn:  no = _num(r"例題(\d+)", pn)
        elif tid == 6:
            m = re.search(r"PART\s*(\d+)\s*Section\s*(\d+)", pn)
            no = int(m.group(1))*10 + int(m.group(2)) if m else None
        elif tid in (4, 5):
            if "深" in pn:
                n = _num(r"深(\d+)", pn); no = 9000+n if n else None
            elif pn.strip().isdigit(): no = int(pn.strip())
        elif tid == 19:  no = int(pn.strip()) if pn.strip().isdigit() else _num(r"(\d+)", pn)
        elif tid == 20:  no = _num(r"セクション\s*(\d+)", pn)
        elif tid in (17, 18): no = _num(r"パート\s*(\d+)", pn)
        if no is None: flags.append((pid, tid, pn))
        else: out[pid] = no
    for n, ids in jissen.items():
        for k, pid in enumerate(ids):
            out[pid] = 10*n + 2 + k
    return out, flags


def build_plan(conn):
    """移行計画を組み立てる。副作用なし。"""
    c = conn.cursor()
    rows = [dict(r) for r in c.execute("SELECT * FROM problems")]
    meta = {r["problem_id"]: r for r in rows}
    test_ids = {r["problem_id"] for r in rows if r["textbook_id"] == TEST_TEXTBOOK_ID}
    delete_ids = set(DELETE_DUP) | set(DELETE_SHIKKARI) | test_ids
    survivors = [r for r in rows if r["problem_id"] not in delete_ids]
    new_no, flags = compute_new_no(survivors)
    new_id = {pid: meta[pid]["textbook_id"]*10000 + no for pid, no in new_no.items()}
    # no衝突
    per = defaultdict(list)
    for pid, no in new_no.items(): per[meta[pid]["textbook_id"]].append((no, pid))
    collisions = []
    for tid, items in per.items():
        for no, cnt in Counter(n for n, _ in items).items():
            if cnt > 1:
                collisions.append({"textbook_id": tid, "no": no,
                                   "ids": [pid for nn, pid in items if nn == no]})
    return {"meta": meta, "delete_ids": delete_ids, "test_ids": test_ids,
            "new_no": new_no, "new_id": new_id, "flags": flags, "collisions": collisions}


def apply_plan(conn, plan):
    """計画を単一トランザクションで適用。検証失敗で例外→呼び出し側でrollback。"""
    c = conn.cursor()
    for pid in plan["delete_ids"]:
        c.execute("DELETE FROM history WHERE problem_id=?", (pid,))
        c.execute("DELETE FROM assignments WHERE problem_id=?", (pid,))
        c.execute("DELETE FROM suppression WHERE problem_id=?", (pid,))
        c.execute("DELETE FROM problems WHERE problem_id=?", (pid,))
    for pid, nid in plan["new_id"].items():
        nno = plan["new_no"][pid]
        c.execute("UPDATE problems SET order_in_textbook=?, problem_id=? WHERE problem_id=?", (nno, nid, pid))
        c.execute("UPDATE history SET problem_id=? WHERE problem_id=?", (nid, pid))
        c.execute("UPDATE assignments SET problem_id=? WHERE problem_id=?", (nid, pid))
        c.execute("UPDATE suppression SET problem_id=? WHERE problem_id=?", (nid, pid))
    c.execute("DELETE FROM textbooks WHERE textbook_id=?", (TEST_TEXTBOOK_ID,))
    c.execute("DELETE FROM students WHERE student_id=?", (TEST_STUDENT_ID,))
    try: c.execute("DELETE FROM series WHERE series_id=?", (TEST_SERIES_ID,))
    except sqlite3.OperationalError: pass
    mx = c.execute("SELECT MAX(problem_id) FROM problems").fetchone()[0]
    try: c.execute("UPDATE sqlite_sequence SET seq=? WHERE name='problems'", (mx,))
    except sqlite3.OperationalError: pass
    # 事前から存在した孤児FK(過去に削除された問題への参照)を掃除
    cleaned = {}
    for tbl in ("history", "assignments", "suppression"):
        n = c.execute(
            f"SELECT COUNT(*) FROM {tbl} WHERE problem_id NOT IN (SELECT problem_id FROM problems)").fetchone()[0]
        if n:
            c.execute(f"DELETE FROM {tbl} WHERE problem_id NOT IN (SELECT problem_id FROM problems)")
        cleaned[tbl] = n
    remain = sum(c.execute(
        f"SELECT COUNT(*) FROM {tbl} WHERE problem_id NOT IN (SELECT problem_id FROM problems)").fetchone()[0]
        for tbl in ("history", "assignments", "suppression"))
    if remain:
        raise RuntimeError(f"掃除後も孤児FK {remain}件 → rollback")
    return {"problems_after": c.execute("SELECT COUNT(*) FROM problems").fetchone()[0],
            "max_problem_id": mx, "orphans_cleaned": cleaned}


def orphan_stats(conn):
    """現状DBの孤児FK(削除済み問題を参照する行)をテーブル別に集計。"""
    c = conn.cursor()
    out, total = {}, 0
    for tbl in ("history", "assignments", "suppression"):
        rows = c.execute(
            f"SELECT problem_id, COUNT(*) FROM {tbl} "
            f"WHERE problem_id NOT IN (SELECT problem_id FROM problems) "
            f"GROUP BY problem_id ORDER BY problem_id").fetchall()
        out[tbl] = {int(r[0]): int(r[1]) for r in rows}
        total += sum(int(r[1]) for r in rows)
    out["total_rows"] = total
    out["orphan_problem_ids"] = sorted(set(out["history"]) | set(out["assignments"]) | set(out["suppression"]))
    return out


def run(db_path, mode="dry_run"):
    """tool/CLI 共通エントリ。mode: 'dry_run' | 'apply' | 'diagnose_orphans'。dict を返す。"""
    if mode == "diagnose_orphans":
        conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row
        try: return {"mode": mode, "status": "ok", "orphans": orphan_stats(conn)}
        finally: conn.close()
    backup = None
    if mode == "apply":
        backup = f"{db_path}.bak-{time.strftime('%Y%m%d-%H%M%S')}"
        shutil.copy2(db_path, backup)
    conn = sqlite3.connect(db_path); conn.row_factory = sqlite3.Row
    try:
        plan = build_plan(conn)
        changed_no = sum(1 for pid, no in plan["new_no"].items()
                         if no != plan["meta"][pid]["order_in_textbook"])
        summary = {"mode": mode, "backup": backup,
                   "survivors": len(plan["new_id"]), "renumbered": changed_no,
                   "deleted": len(plan["delete_ids"]),
                   "collisions": plan["collisions"], "flags_unmapped": plan["flags"]}
        if plan["flags"] or plan["collisions"]:
            summary["status"] = "aborted"; summary["reason"] = "算出不能または衝突あり"
            return summary
        if mode == "dry_run":
            sample = [{"old_id": pid, "new_id": plan["new_id"][pid],
                       "old_no": plan["meta"][pid]["order_in_textbook"], "new_no": plan["new_no"][pid],
                       "label": plan["meta"][pid]["problem_number"][:26]}
                      for pid in list(plan["new_id"])[:12]]
            summary["status"] = "ok_dry_run"; summary["sample"] = sample
            summary["preexisting_orphans"] = orphan_stats(conn)
            return summary
        # apply
        result = apply_plan(conn, plan)
        conn.commit()
        summary["status"] = "applied"; summary.update(result)
        return summary
    except Exception as e:
        conn.rollback(); return {"mode": mode, "status": "error", "error": str(e), "backup": backup}
    finally:
        conn.close()


def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    res = run(args.db, "apply" if args.apply else "dry_run")
    import json
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
