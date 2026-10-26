# -*- coding: utf-8 -*-
"""P1 题集切片：按《题集筛选工作流》第二节章-PDF页台账，把 331 页扫描版题集切成 9 章小片。
用 base python 的 pypdf（不依赖 mineru 环境）。题集 xref 损坏，strict=False 容错。
页码约定：全书 PDF页 = 书页 + 9；台账登记的是各章题目区页码。
"""
import os
from pypdf import PdfReader, PdfWriter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "资料", "教材与题集", "数据结构题集第二版.pdf")
OUT = os.path.join(ROOT, "_tmp", "tiji_slices")
os.makedirs(OUT, exist_ok=True)

# (章号, 章名, 题目区起页, 题目区止页)  —— 均为 PDF 页码(1-based)
CHAPTERS = [
    (1, "绪论", 29, 38),
    (2, "线性表", 47, 57),
    (3, "栈和队列", 62, 68),
    (4, "串", 70, 74),
    (5, "数组和广义表", 81, 88),
    (6, "树和二叉树", 93, 105),
    (7, "图", 116, 121),
    (9, "查找", 130, 143),
    (10, "内部排序", 146, 155),
]

print("加载题集 PDF (448MB，稍候)...")
reader = PdfReader(SRC, strict=False)
total = len(reader.pages)
print(f"总页数: {total}")

for num, name, start, end in CHAPTERS:
    if end > total:
        print(f"  [跳过] 第{num}章 页码越界 end={end} > {total}")
        continue
    writer = PdfWriter()
    for p in range(start - 1, end):          # 转 0-based
        writer.add_page(reader.pages[p])
    outpath = os.path.join(OUT, f"第{num:02d}章-{name}.pdf")
    with open(outpath, "wb") as f:
        writer.write(f)
    size = round(os.path.getsize(outpath) / 1024 / 1024, 2)
    print(f"  第{num}章 {name}: PDF页 {start}-{end} ({end-start+1}页) -> {os.path.basename(outpath)} {size}MB")

print("切片完成 ->", OUT)
