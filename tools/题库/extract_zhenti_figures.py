# -*- coding: utf-8 -*-
"""P0 真题转化·第1步：抽取题目配图。
过滤整页扫描背景(2479x3508)与校徽logo(1884x1901)，只留题目内插图(树/图/散列表/AOE网等)。
按 xref 去重，存到 images/真题/，输出图清单供结构化时引用。
"""
import os, fitz

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ZHEN = os.path.join(ROOT, "资料", "重邮802真题")
IMGOUT = os.path.join(ROOT, "题库", "images", "真题")
os.makedirs(IMGOUT, exist_ok=True)
OUT = os.path.join(ROOT, "_tmp", "zhenti_figures.txt")

FILES = {
    "26重邮208数据结构真题回忆版.pdf": "z26",     # 2026 题目(回忆版)
    "真题24-25.pdf": "z2425",                       # 2024卷+2025卷+两套答案
    "重邮2026年802真题答案.pdf": "a26",             # 2026 答案
}
SKIP_SIZES = {(2479, 3508), (1884, 1901), (2479, 3507), (1884, 1900),
              (2480, 3508), (1885, 1901)}           # 整页扫描背景 & 校徽
MIN_AREA = 130 * 130                                 # 过小的装饰图丢弃

L = []
def p(*a): L.append(" ".join(str(x) for x in a))
saved = {}   # (fname,xref) -> rel path
count = 0

for fname, tag in FILES.items():
    path = os.path.join(ZHEN, fname)
    if not os.path.exists(path):
        p("MISSING:", fname); continue
    doc = fitz.open(path)
    p("#" * 60); p("FILE:", fname, "pages=", doc.page_count)
    for pno in range(doc.page_count):
        page = doc[pno]
        page_figs = []
        for idx, im in enumerate(page.get_images(full=True)):
            xref = im[0]
            try:
                pix = fitz.Pixmap(doc, xref)
            except Exception as e:
                p(f"  p{pno} img{idx} ERR {e}"); continue
            w, h = pix.width, pix.height
            if (w, h) in SKIP_SIZES or w * h < MIN_AREA:
                pix = None; continue
            key = (fname, xref)
            if key in saved:                          # 同图跨页复用，不重复存
                page_figs.append(saved[key]); pix = None; continue
            if pix.n - pix.alpha >= 4:                # CMYK→RGB
                pix = fitz.Pixmap(fitz.csRGB, pix)
            outname = f"{tag}-p{pno:02d}-{idx}.png"
            pix.save(os.path.join(IMGOUT, outname))
            rel = f"images/真题/{outname}"
            saved[key] = rel; count += 1
            page_figs.append(rel)
            p(f"  p{pno:02d} img{idx} {w}x{h} -> {rel}")
            pix = None
        if page_figs:
            p(f"  >> p{pno:02d} 题目图: {page_figs}")
    doc.close()

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(L))
print("WROTE", OUT)
print("题目配图 saved:", count, "->", IMGOUT)
