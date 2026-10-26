# -*- coding: utf-8 -*-
"""P2 教材知识体系抽取：严蔚敏《数据结构(C语言版)》正文按 TOC 章书签切分，每章存 markdown。
文本型 PDF，fitz 直抽。产出 题库数据库/教材/第X章-章名.md，供 C2/C3 备课的知识体系参考。
"""
import os, fitz, re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "资料", "教材与题集", "严蔚敏《数据结构》（C语言版）.pdf")
OUT = os.path.join(ROOT, "资料", "教材摘要")
os.makedirs(OUT, exist_ok=True)

doc = fitz.open(SRC)
toc = doc.get_toc()
n = doc.page_count
print(f"教材 {n} 页, TOC {len(toc)} 条")

# 提取章级书签(第X章)，按章号去重取首次出现页
chaps, seen = [], set()
for level, title, page in toc:
    t = re.sub(r"\s+", "", title.strip())
    m = re.match(r"^第(\d+)章(.*)$", t)
    if m and m.group(1) not in seen:
        seen.add(m.group(1))
        chaps.append((int(m.group(1)), title.strip(), page))
chaps.sort(key=lambda x: x[2])
print(f"识别到 {len(chaps)} 章:")
for cnum, title, page in chaps:
    print(f"   第{cnum}章 {title} @p{page}")

# 逐章抽取全文
for i, (cnum, title, sp) in enumerate(chaps):
    ep = chaps[i + 1][2] - 1 if i + 1 < len(chaps) else n
    parts = [f"# {title}\n", f"> 教材正文 PDF 页 {sp}-{ep}（严蔚敏《数据结构 C语言版》）\n"]
    for pno in range(sp - 1, min(ep, n)):
        parts.append(doc[pno].get_text("text"))
    text = "\n".join(parts)
    safe = re.sub(r'[\\/:*?"<>|\s]+', "", title)
    fp = os.path.join(OUT, f"第{cnum:02d}章-{safe}.md")
    with open(fp, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"  第{cnum}章 {title}: p{sp}-{ep} ({ep-sp+1}页) chars={len(text)} -> {os.path.basename(fp)}")

doc.close()
print("教材知识体系抽取完成 ->", OUT)
