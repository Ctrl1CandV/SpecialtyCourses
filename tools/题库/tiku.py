#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""802 题库数据库查询 CLI —— AI 与人的唯一取数入口。

用法:
    python tiku.py init                              建库/升级 schema
    python tiku.py list   [--chapter 图 --tier 一档] [--md] [--limit N]
    python tiku.py get    <id> [--md]                 取某题完整内容
    python tiku.py search <关键词> [--md]             全文搜题干/答案/解析/考点
    python tiku.py stats  [--by chapter]              多维统计
    python tiku.py export [--source 题集 --chapter 图] [-o 路径.md]
    python tiku.py import <jsonl文件>                 批量入库(UPSERT)
    python tiku.py delete --id <ID> | --like <模式>   删题(默认dry-run预览,加 --yes 才真删)

通用筛选参数: --source --chapter --qtype --tier --template --kaodian --difficulty --limit
主库: ../tiku.db   导出: ../导出/
"""
import argparse, io, json, os, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(os.path.dirname(os.path.dirname(HERE)), '题库')
DB = os.path.join(ROOT, "tiku.db")
SCHEMA = os.path.join(ROOT, "schema.sql")
EXPORT_DIR = os.path.join(ROOT, "导出")

# Windows 控制台中文输出
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

COLS = ["id", "source", "source_detail", "chapter", "qtype", "number", "difficulty",
        "tier", "stem", "options", "answer", "analysis", "kaodian", "template",
        "figures", "pdf_page", "real_related", "raw_text", "notes"]
FILTERS = ["source", "chapter", "qtype", "tier", "template", "difficulty"]


def conn():
    if not os.path.exists(DB):
        print(f"[err] 主库不存在: {DB}\n先跑: python tiku.py init")
        sys.exit(1)
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db


def build_where(args):
    conds, params = [], []
    for col in FILTERS:
        v = getattr(args, col, None)
        if v:
            conds.append(f"{col}=?"); params.append(v)
    if getattr(args, "kaodian", None):
        conds.append("kaodian LIKE ?"); params.append(f"%{args.kaodian}%")
    return ((" WHERE " + " AND ".join(conds)) if conds else ""), params


def one_line(s, n=50):
    s = (s or "").replace("\n", " ").replace("\r", " ").strip()
    return s[:n]


# ---------- init ----------
def cmd_init(args):
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    with open(SCHEMA, encoding="utf-8") as f:
        db.executescript(f.read())
    db.commit()
    n = db.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    print(f"[init] ok. questions={n}  db={DB}")
    db.close()


# ---------- list ----------
def cmd_list(args):
    db = conn(); where, params = build_where(args)
    sql = ("SELECT id, chapter, qtype, tier, number, source, stem "
           f"FROM questions{where} ORDER BY source, chapter, number")
    if args.limit:
        sql += f" LIMIT {int(args.limit)}"
    rows = db.execute(sql, params).fetchall()
    if not rows:
        print("(无匹配题目)"); db.close(); return
    print(f"共 {len(rows)} 题" + (f"（limit {args.limit}）" if args.limit else ""))
    for r in rows:
        head = one_line(r["stem"], 46)
        if args.md:
            print(f"- **{r['id']}** [{r['chapter']}/{r['qtype']}/{r['tier'] or '-'}] {head}")
        else:
            print(f"{r['id']:<20} {(r['chapter'] or ''):<8} {(r['qtype'] or ''):<8} "
                  f"{(r['tier'] or ''):<5} {head}")
    db.close()


# ---------- get ----------
def cmd_get(args):
    db = conn()
    r = db.execute("SELECT * FROM questions WHERE id=?", (args.id,)).fetchone()
    if not r:
        print(f"(未找到 id={args.id})"); db.close(); return
    figs = json.loads(r["figures"]) if r["figures"] else []
    if args.md:
        print(f"# {r['id']}\n")
        meta = [f"来源:{r['source']}", f"章节:{r['chapter']}", f"题型:{r['qtype']}"]
        for lbl, key in [("分档", "tier"), ("难度", "difficulty"), ("模板", "template"),
                         ("考点", "kaodian"), ("PDF页", "pdf_page")]:
            if r[key]:
                meta.append(f"{lbl}:{r[key]}")
        print("> " + " | ".join(str(m) for m in meta) + "\n")
        print("## 题干\n" + (r["stem"] or ""))
        if r["options"] and r["options"] not in ("[]", "{}", "null"):
            print("\n## 选项\n" + r["options"])
        if figs:
            print("\n## 图\n" + "\n".join(f"![]({f})" for f in figs))
        if r["answer"]:
            print("\n## 答案\n" + r["answer"])
        if r["analysis"]:
            print("\n## 解析\n" + r["analysis"])
        if r["real_related"]:
            print(f"\n> 真题同源：{r['real_related']}")
        if r["notes"]:
            print(f"\n> 备注：{r['notes']}")
    else:
        for k in COLS:
            v = r[k]
            if v not in (None, ""):
                print(f"[{k}] {v}")
    db.close()


# ---------- search ----------
def cmd_search(args):
    db = conn(); where, params = build_where(args)
    kw = f"%{args.keyword}%"
    cond = "(stem LIKE ? OR answer LIKE ? OR analysis LIKE ? OR kaodian LIKE ? OR options LIKE ? OR notes LIKE ?)"
    full = where + (" AND " if where else " WHERE ") + cond
    params = params + [kw] * 6
    sql = ("SELECT id, chapter, qtype, tier, stem "
           f"FROM questions{full} ORDER BY source, chapter, number")
    if args.limit:
        sql += f" LIMIT {int(args.limit)}"
    rows = db.execute(sql, params).fetchall()
    print(f"搜索 '{args.keyword}' 命中 {len(rows)} 题")
    for r in rows:
        print(f"{r['id']:<20} {(r['chapter'] or ''):<8} {(r['tier'] or ''):<5} {one_line(r['stem'], 50)}")
    db.close()


# ---------- stats ----------
def cmd_stats(args):
    db = conn(); by = args.by or "chapter"
    if by not in ["chapter", "qtype", "tier", "source", "template", "difficulty"]:
        print("--by 仅支持 chapter/qtype/tier/source/template/difficulty"); db.close(); return
    total = db.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    print(f"总题数: {total}   (按 {by} 统计)")
    rows = db.execute(
        f"SELECT {by} AS k, COUNT(*) AS c FROM questions GROUP BY {by} ORDER BY c DESC").fetchall()
    for r in rows:
        print(f"  {str(r['k']) or '(空)':<16} {r['c']}")
    db.close()


# ---------- export ----------
def cmd_export(args):
    db = conn(); where, params = build_where(args)
    rows = db.execute(f"SELECT * FROM questions{where} ORDER BY source, chapter, number",
                      params).fetchall()
    if not rows:
        print("(无匹配题目，未导出)"); db.close(); return
    out = args.o or os.path.join(EXPORT_DIR, f"{args.source or '全部'}.md")
    if not os.path.isabs(out):
        out = os.path.join(ROOT, out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    lines = [f"# 题库导出（{len(rows)} 题）", ""]
    cur = object()
    for r in rows:
        if r["chapter"] != cur:
            cur = r["chapter"]
            lines.append(f"\n## 【{cur or '未分类'}】\n")
        lines.append(f"### {r['id']}")
        meta = [x for x in [r["source"], r["qtype"], r["tier"]] if x]
        lines.append("> " + " | ".join(meta))
        lines.append("\n" + (r["stem"] or ""))
        if r["options"] and r["options"] not in ("[]", "{}", "null"):
            lines.append("\n**选项**\n" + r["options"])
        figs = json.loads(r["figures"]) if r["figures"] else []
        for f in figs:
            lines.append(f"\n![](../{f})")
        if r["answer"]:
            label = "\n**答案**"
            lines.append(label + ("\n\n" if "\n" in r["answer"] else "：") + r["answer"])
        if r["analysis"]:
            label = "\n**解析**"
            lines.append(label + ("\n\n" if "\n" in r["analysis"] else "：") + r["analysis"])
        lines.append("")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[export] {len(rows)} 题 -> {out}")
    db.close()


# ---------- import ----------
def cmd_import(args):
    db = conn()
    path = args.jsonl if os.path.isabs(args.jsonl) else os.path.join(HERE, args.jsonl)
    if not os.path.exists(path):
        print(f"[err] 文件不存在: {path}"); db.close(); return
    n = ok = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"  跳过(JSON错): {e} :: {line[:50]}"); continue
            if "id" not in rec or "stem" not in rec:
                print(f"  跳过(缺id/stem): {line[:50]}"); continue
            for k in list(rec.keys()):          # 任何 list/dict 字段统一转 JSON 字符串（不只 figures）
                if isinstance(rec[k], (list, dict)):
                    rec[k] = json.dumps(rec[k], ensure_ascii=False)
            keys = [k for k in rec if k in COLS]
            cols = ",".join(keys); ph = ",".join("?" * len(keys))
            upd = ",".join(f"{k}=excluded.{k}" for k in keys if k != "id")
            sql = (f"INSERT INTO questions ({cols}) VALUES ({ph}) "
                   f"ON CONFLICT(id) DO UPDATE SET {upd}")
            db.execute(sql, [rec[k] for k in keys])
            ok += 1
    db.commit()
    total = db.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    print(f"[import] 读 {n} 条, 入库/更新 {ok} 条, 库中总计 {total} 题")
    db.close()


# ---------- delete ----------
def cmd_delete(args):
    if not args.id and not args.like:
        print("[err] delete 需指定 --id <精确ID> 或 --like <ID模式，如 408-2015-选%>"); return
    db = conn()
    conds, params = [], []
    if args.id:
        conds.append("id=?"); params.append(args.id)
    if args.like:
        conds.append("id LIKE ?"); params.append(args.like)
    where = " WHERE " + " AND ".join(conds)
    rows = db.execute(f"SELECT id, source, chapter, qtype FROM questions{where}", params).fetchall()
    if not rows:
        print("(无匹配，未删除)"); db.close(); return
    print(f"匹配 {len(rows)} 题：")
    for r in rows:
        print(f"  {r['id']:<20} {(r['source'] or ''):<10} {(r['chapter'] or ''):<8} {r['qtype'] or ''}")
    if not args.yes:
        print("\n[dry-run] 未删除。确认无误后加 --yes 执行。"); db.close(); return
    db.execute(f"DELETE FROM questions{where}", params)
    db.commit()
    total = db.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    print(f"\n[delete] 已删 {len(rows)} 题，库中总计 {total} 题")
    db.close()


def add_filters(p):
    for c in FILTERS:
        p.add_argument(f"--{c}")
    p.add_argument("--kaodian")
    p.add_argument("--limit", type=int)
    p.add_argument("--md", action="store_true")


def main():
    ap = argparse.ArgumentParser(description="802 题库数据库查询 CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="建库/升级schema").set_defaults(func=cmd_init)
    p = sub.add_parser("list", help="按条件列题"); add_filters(p); p.set_defaults(func=cmd_list)
    p = sub.add_parser("get", help="取某题完整内容"); p.add_argument("id"); p.add_argument("--md", action="store_true"); p.set_defaults(func=cmd_get)
    p = sub.add_parser("search", help="全文搜索"); p.add_argument("keyword"); add_filters(p); p.set_defaults(func=cmd_search)
    p = sub.add_parser("stats", help="多维统计"); p.add_argument("--by"); p.set_defaults(func=cmd_stats)
    p = sub.add_parser("export", help="导出markdown"); add_filters(p); p.add_argument("-o"); p.set_defaults(func=cmd_export)
    p = sub.add_parser("import", help="从jsonl入库"); p.add_argument("jsonl"); p.set_defaults(func=cmd_import)
    p = sub.add_parser("delete", help="删题(--id精确/--like模式,默认dry-run)"); p.add_argument("--id"); p.add_argument("--like"); p.add_argument("--yes", action="store_true"); p.set_defaults(func=cmd_delete)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
