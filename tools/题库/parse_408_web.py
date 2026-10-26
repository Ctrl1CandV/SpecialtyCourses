# -*- coding: utf-8 -*-
"""P2·408网站真题解析：从 WebFetch 缓存文本提取"#### 数据结构"分区的题(选择题+综合题)。
严格只取数据结构分区(跳过组成原理/操作系统/计算机网络)，落实"禁止非802入内"。
用法：python parse_408_web.py <缓存文件> <年份> <输出jsonl>
网站格式：### 选择题/综合应用题 → #### 数据结构 → ##### N → 题干 → [标签](链接)选项...正确答案：X → 解析
"""
import re, json, sys, os

cache, year, out = sys.argv[1], sys.argv[2], sys.argv[3]
_raw = open(cache, encoding="utf-8").read()
# 去掉零宽字符等网页残留(\u200b零宽空格/\u200c/\u200d/\ufeff)，避免污染题库stem与Windows控制台gbk打印报错
_raw = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", _raw)
lines = _raw.split("\n")

# 标签→802章节映射(按考点关键词)
def to_chapter(tags, stem):
    t = " ".join(tags) + " " + stem[:60]
    # 顺序即优先级：先判更具体的串/图/查找/排序，再判栈队列/树/数组/线性表。
    # 避免"图的遍历/最小生成树"误归树、"邻接矩阵"误归数组、"折半查找"误归数组。
    rules = [
        ("串", ["KMP", "next数组", "模式匹配", "字符串", "串"]),
        ("图", ["图", "DFS", "BFS", "拓扑", "最短路径", "最小生成树", "生成树", "Prim", "Kruskal", "克鲁斯卡", "普里姆", "Dijkstra", "Floyd", "关键路径", "AOE", "AOV", "邻接", "图的遍历", "连通", "深度优先", "广度优先"]),
        ("查找", ["查找", "折半", "二分", "散列", "哈希", "BST", "排序树", "搜索树", "二叉排序", "ASL", "判定树", "B树", "B+树"]),
        ("排序", ["排序", "堆", "快排", "希尔", "归并", "基数", "插入排序", "冒泡", "起泡"]),
        ("栈队列", ["栈", "队列", "递归", "函数调用", "表达式", "后缀", "中缀", "卡特兰", "入栈", "出栈"]),
        ("树", ["二叉树", "哈夫曼", "赫夫曼", "前缀编码", "前缀码", "AVL", "平衡二叉", "线索", "森林", "完全二叉", "树", "并查集", "遍历", "二叉"]),
        ("数组广义表", ["数组", "广义表", "矩阵", "压缩存储", "稀疏"]),
        ("线性表", ["顺序表", "链表", "单链表", "双链表", "循环链表", "静态链表", "多项式"]),
        ("绪论", ["复杂度", "时间复杂", "空间复杂", "算法", "数据结构", "逻辑结构", "存储结构"]),
    ]
    for chap, kws in rules:
        for kw in kws:
            if kw in t:
                return chap
    return ""

def is_structural(s):
    """结构行：选项/小问编号/答案标记——不参与断句合并，保持独立。"""
    s = s.strip()
    if not s: return True
    if re.match(r"^[A-D][\.、．]", s): return True            # 选项 A. B. C. D.
    if re.match(r"^[\(（]\s*\d+\s*[\)）]", s): return True     # (1)（2）小问
    if re.match(r"^\d+\s*[\)）]", s): return True             # 1）2）小问
    if re.match(r"^[①②③④⑤⑥⑦⑧⑨⑩]", s): return True
    if re.search(r"正确答案|查看答案|^答案|^解析|【|评分说明", s): return True
    return False

def merge_math_fragments(body_lines):
    """还原被网页拆断的题干/解析：上一行未以句末标点结束、且当前行非结构行时并入上一行。
    网页把KaTeX公式每个符号拆成独立行(如 V={ / v0 / , / v1 / })，此合并把断句拼回整句。
    代码围栏内、空行、选项/小问/答案行不合并。"""
    out, in_code = [], False
    for ln in body_lines:
        if ln.strip().startswith("```"):
            in_code = not in_code; out.append(ln); continue
        if in_code:
            out.append(ln); continue
        c = ln.strip()
        if not c:
            out.append(""); continue
        if out and out[-1].strip():
            prev_s = out[-1].strip()
            fence = prev_s.startswith("```") or c.startswith("```")
            # 上一行以句末标点结束则视为完整句，不并；否则当前行是断句续行，并入
            if not fence and not is_structural(c) and not is_structural(prev_s) \
               and not re.search(r"[。？！；：）\)]$", prev_s):
                out[-1] = prev_s + c; continue
        out.append(ln)
    return out

qs, section, subject, cur = [], None, None, None
def flush():
    global cur
    if cur is not None and subject == "数据结构":
        qs.append(cur)
    cur = None

for line in lines:
    if line.startswith("### ") and not line.startswith("#### "):
        flush(); section = line[4:].strip(); subject = None; continue
    if line.startswith("#### "):
        flush(); subject = line[5:].strip(); continue
    if line.startswith("##### "):
        flush()
        if subject == "数据结构":
            cur = {"num": line[6:].strip(), "section": section, "body": []}
        continue
    if cur is not None:
        cur["body"].append(line)
flush()

print(f"{year}年 数据结构题提取: {len(qs)} 道")
recs = []
for q in qs:
    body = "\n".join(merge_math_fragments(q["body"])).strip()
    # 答案
    am = re.search(r"正确答案[：:]\s*\**([A-D])", body)
    answer = am.group(1) if am else ""
    # 标签(考点)
    tags = re.findall(r"\[([^\]]+)\]\(/study_methods/tags", body)
    tags = [t for t in tags if t and "查看答案" not in t]
    # 拆分：以"查看答案与解析"为界，前=题干+选项，后=答案区
    cut = re.search(r"查看答案与解析", body)
    if cut:
        stem_part = body[:cut.start()].strip()
        ans_part = body[cut.end():].strip()
    else:
        stem_part = body; ans_part = ""
    # 去掉答案区开头的网页"收藏(计数)"残留：只吃 收藏 和 (数字)/（数字），不吃答案自身的 1）编号
    ans_part = re.sub(r"^收藏\s*(?:[（(]\d+[)）])?\s*", "", ans_part).strip()
    # 选择题:答案区提取"正确答案:X"及其后解析;综合题:答案区整体为答案
    am2 = re.search(r"正确答案[：:]\s*\**\s*([A-D])", ans_part)
    if am2:
        answer = am2.group(1); analysis = re.sub(r"^\*+", "", ans_part[am2.end():].strip())
    else:
        answer = ""; analysis = re.sub(r"^\*+", "", ans_part.strip())
    # 去掉标签链接
    stem_clean = re.sub(r"\[[^\]]*\]\(/study_methods/tags[^)]*\)", "", stem_part).strip()
    # 分离选项：找最后的 A. ... B. ... C. ... D. ...
    opts = ""
    om = re.search(r"(A[\.、．][\s\S]*)$", stem_clean)
    if om:
        tail = om.group(1)
        if re.search(r"B[\.、．]", tail) and re.search(r"[CD][\.、．]", tail):
            stem_clean = stem_clean[:om.start()].strip()
            opts = tail.strip()
    qtype = "选择" if q["section"] and "选择" in q["section"] else "综合应用"
    chapter = to_chapter(tags, stem_clean)
    # 严格802考纲筛选：排除外部排序/动态存储管理/文件等超纲内容(802只考内部排序、不考动态存储与文件)
    NON802 = ["外部排序", "外排序", "动态存储", "败者树", "置换选择", "文件系统", "多路平衡归并"]
    if any(kw in (" ".join(tags) + stem_clean) for kw in NON802):
        print(f"  [跳过·非802] {q['num']} tags={tags}")
        continue
    rec = {
        "id": f"408-{year}-{q['num']}",
        "source": "408真题",
        "source_detail": f"{year}年全国408联考·数据结构部分(csgraduates.com)",
        "chapter": chapter,
        "qtype": qtype,
        "number": q["num"],
        "stem": stem_clean,
        "options": opts,
        "answer": answer if qtype == "选择" else analysis,
        "analysis": analysis if qtype == "选择" else "",
        "kaodian": ",".join(dict.fromkeys(tags)),
        "real_related": f"{year}年408联考真题",
        "notes": "网站已按科目分区,仅取数据结构;综合题answer含解析全文" if qtype == "综合应用" else "网站408数据结构选择题",
    }
    recs.append(rec)
    print(f"  {rec['id']} [{chapter}/{qtype}] tags={tags} ans={answer} stem={stem_clean[:30]}")

with open(out, "w", encoding="utf-8") as f:
    for r in recs:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"WROTE {out} 共{len(recs)}题")
