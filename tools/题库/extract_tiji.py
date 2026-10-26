# -*- coding: utf-8 -*-
"""P1 题集后处理：解析9章MinerU md，按题型标题+题号切分，复用分档表回填tier/考点，生成jsonl。
方案A：先入库题面(题干+选项+难度+分档)，答案区(书末)待后续识别补充(answer留空)。
切分要点：①"基础知识题"标题默认进选择题区 ②题号归1自动递进题型(解决个别章缺子标题)
         ③"## 数字."形式的题目去#当题号 ④代码块内不切 ⑤分档表题号数校验对照。
用法：python extract_tiji.py [章名关键词]
"""
import os, re, json, glob, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MINERU = os.path.join(ROOT, "_tmp", "mineru_out")
FENDANG = os.path.join(ROOT, "题库", "筛选", "题集")
OUT = os.path.join(ROOT, "_tmp", "tiji_all.jsonl")

CHAPTERS = {
    "第01章-绪论": (1, "绪论"), "第02章-线性表": (2, "线性表"),
    "第03章-栈和队列": (3, "栈队列"), "第04章-串": (4, "串"),
    "第05章-数组和广义表": (5, "数组广义表"), "第06章-树和二叉树": (6, "树"),
    "第07章-图": (7, "图"), "第09章-查找": (9, "查找"),
    "第10章-内部排序": (10, "排序"),
}
QTYPE = {"选": "选择", "答": "解答", "算": "算法设计"}
SEQ = ["选", "答", "算"]


def title_type(s):
    """从标题文本判题型；'基础知识题'下默认先是选择题。"""
    if "基础知识题" in s:
        return "选"
    if "单项选择" in s or "选择题" in s:
        return "选"
    if "解答题" in s or "简答" in s:
        return "答"
    if "算法设计" in s or ("算法" in s and "题" in s):
        return "算"
    return None


def load_fendang():
    info = {}
    for fp in glob.glob(os.path.join(FENDANG, "*分档表.md")):
        cur = None
        for line in open(fp, encoding="utf-8").read().split("\n"):
            if line.startswith("## "):
                cur = "一档" if "一档" in line else "二档" if "二档" in line else "三档" if "三档" in line else None
                continue
            if not line.strip().startswith("|") or cur is None:
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not cells or cells[0] in ("题号", "组") or set(cells[0]) <= set(":- "):
                continue
            for qid in re.findall(r"(\d+(?:选|答|算)\d+)", line):
                rec = {"tier": cur}
                if cur in ("一档", "二档") and len(cells) >= 2:
                    rec["kaodian"] = cells[1]
                pm = re.search(r"p0*(\d+)", line)
                if pm:
                    rec["page"] = int(pm.group(1))
                info.setdefault(qid, rec)
    return info


def parse_chapter(md_path):
    lines = open(md_path, encoding="utf-8").read().split("\n")
    qs, cur_type, cur, in_code, last_num = [], None, None, False, 0

    def flush():
        nonlocal cur
        if cur:
            qs.append(cur); cur = None

    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            if cur: cur["lines"].append(line)
            continue
        if in_code:
            if cur: cur["lines"].append(line)
            continue
        is_title = line.lstrip().startswith("#")
        content = re.sub(r"^#+\s*", "", line).rstrip()
        if is_title:
            t = title_type(content)
            if t:
                flush(); cur_type = t; last_num = 0; continue
            # 非题型标题：可能是被误标为标题的题目(## 4.① ...)，也可能是章首干扰(## 8.算法2.19)
        m = re.match(r"^(\d+)\s*[\.、．]\s*(.*)$", content)
        if m and cur_type:
            num = int(m.group(1))
            # 题号归1且当前区已有题 → 缺子标题，题型递进
            if num == 1 and last_num > 0 and cur_type in SEQ:
                i = SEQ.index(cur_type)
                if i + 1 < len(SEQ):
                    flush(); cur_type = SEQ[i + 1]; last_num = 0
            flush()
            rest = m.group(2)
            dm = re.search(r"([①②③④⑤])", rest)
            cur = {"type": cur_type, "num": num,
                   "diff": dm.group(1) if dm else "",
                   "lines": [content if is_title else line]}
            last_num = num
        elif cur:
            cur["lines"].append(content if is_title else line)
    flush()
    return qs


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    fendang = load_fendang()
    # 分档表每章题号数(校验基准)
    fcnt = defaultdict(lambda: {"选": 0, "答": 0, "算": 0})
    for qid in fendang:
        mm = re.match(r"(\d+)(选|答|算)(\d+)", qid)
        if mm:
            fcnt[int(mm.group(1))][mm.group(2)] += 1
    print(f"分档表载入 {len(fendang)} 题号")
    allq = []
    for dirname, (cnum, cstd) in CHAPTERS.items():
        if only and only not in dirname:
            continue
        md = os.path.join(MINERU, dirname, "auto", dirname + ".md")
        if not os.path.exists(md):
            print("  MISSING", md); continue
        qs = parse_chapter(md)
        cname = dirname.split("-", 1)[1]
        cnt = {"选": 0, "答": 0, "算": 0}
        for q in qs:
            cnt[q["type"]] += 1
            fd = fendang.get(f"{cnum}{q['type']}{q['num']}", {})
            allq.append({
                "id": f"题集-{cnum:02d}-{q['type']}{q['num']}",
                "source": "题集",
                "source_detail": f"严蔚敏《数据结构题集(第2版)》第{cnum}章{cname}",
                "chapter": cstd, "qtype": QTYPE[q["type"]],
                "number": f"{q['type']}{q['num']}", "difficulty": q["diff"],
                "tier": fd.get("tier", ""),
                "stem": "\n".join(q["lines"]).strip(),
                "kaodian": fd.get("kaodian", ""), "pdf_page": fd.get("page"),
                "notes": "题面MinerU识别；答案区(书末)待识别补充" + ("" if fd.get("tier") else "；分档表未匹配,待核"),
            })
        fc = fcnt[cnum]
        flag = "" if (cnt["选"] == fc["选"] and cnt["答"] == fc["答"] and cnt["算"] == fc["算"]) else "  <<< 与分档表不符"
        print(f"  第{cnum}章 {cname}: 切分 选{cnt['选']}/答{cnt['答']}/算{cnt['算']}={sum(cnt.values())} | 分档表 选{fc['选']}/答{fc['答']}/算{fc['算']}={sum(fc.values())}{flag}")
    with open(OUT, "w", encoding="utf-8") as f:
        for r in allq:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"合计 {len(allq)} 题 -> {OUT}")


if __name__ == "__main__":
    main()
