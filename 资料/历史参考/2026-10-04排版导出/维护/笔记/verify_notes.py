# -*- coding: utf-8 -*-
"""程序化验收：页数、书签(H1)、目录链接、空白页、文本越界、代码块数、样张定位。"""
import os
import re

import pypdf
import pypdfium2 as pdfium

OUT = r"D:/Program Project/SpecialtyCourses/_tmp/pdf_v3/产出"
BUILD = r"D:/Program Project/SpecialtyCourses/_tmp/pdf_v3/build_notes"
PAGES = r"D:/Program Project/SpecialtyCourses/_tmp/pdf_v3/pages"
A4W, A4H = 595.32, 841.92

SRC_FACTS = {"代码总结": dict(h1=9, pre=87, imgs=0), "重邮数据结构": dict(h1=8, pre=55, imgs=33)}


def outline_titles(reader):
    flat = []
    def walk(items, depth):
        for it in items:
            if isinstance(it, list):
                walk(it, depth + 1)
            else:
                flat.append((depth, it.title))
    walk(reader.outline, 0)
    return flat


def main():
    report = {}
    for name, fact in SRC_FACTS.items():
        p = os.path.join(OUT, f"{name}.pdf")
        reader = pypdf.PdfReader(p)
        n = len(reader.pages)
        box = reader.pages[0].mediabox
        ol = outline_titles(reader)
        h1_titles = [t for d, t in ol if d == 0]
        # 目录页链接注解
        link_pages = []
        for i, pg in enumerate(reader.pages[:6]):
            annots = pg.get("/Annots")
            if annots:
                k = sum(1 for a in annots if a.get_object().get("/Subtype") == "/Link")
                if k:
                    link_pages.append((i + 1, k))
        # 页面尺寸与页序
        sizes_ok = all(abs(float(pg.mediabox.width) - A4W) < 1 and abs(float(pg.mediabox.height) - A4H) < 1
                       for pg in reader.pages)
        # HTML 侧：pre 数、目录锚点配对
        html = open(os.path.join(BUILD, f"{name}.html"), encoding="utf-8").read()
        n_pre = html.count("<pre>")
        n_imgs = len(re.findall(r'src="data:image/', html))
        hrefs = set(re.findall(r'href="#(s-\d+)"', html))
        ids = set(re.findall(r'id="(s-\d+)"', html))
        missing_anchor = sorted(hrefs - ids)
        report[name] = dict(pages=n, size_kb=os.path.getsize(p) // 1024,
                            mediabox=(round(float(box.width), 1), round(float(box.height), 1)),
                            sizes_ok=sizes_ok, bookmarks=len(ol), h1_bookmarks=len(h1_titles),
                            h1_titles=h1_titles, link_pages=link_pages,
                            html_pre=n_pre, html_imgs=n_imgs,
                            toc_links=len(hrefs), missing_anchor=missing_anchor)
        print(f"== {name}")
        for k, v in report[name].items():
            if k != "h1_titles":
                print(f"   {k}: {v}")
        print("   H1 书签:", " | ".join(h1_titles))
        assert report[name]["h1_bookmarks"] == fact["h1"], "H1 书签数不符"
        assert n_pre == fact["pre"], f"代码块数不符 HTML={n_pre} 期望={fact['pre']}"
        assert n_imgs == fact["imgs"], "图片内嵌数不符"
        assert not missing_anchor, "目录锚点缺失"

        # ---- pypdfium2：空白页 + 越界 + 找样张 ----
        doc = pdfium.PdfDocument(p)
        blanks, overflows, pages_text = [], [], []
        for i in range(len(doc)):
            page = doc[i]
            tp = page.get_textpage()
            txt = tp.get_text_bounded()
            pages_text.append(txt)
            n_rect = tp.count_rects()
            maxx = 0
            for ridx in range(n_rect):
                l, b, rr, t = tp.get_rect(ridx)
                maxx = max(maxx, rr)
            if maxx > A4W - 42:  # 版心右缘 ≈ 595.32-56.7=538.6pt，留 6pt 容差
                overflows.append((i + 1, round(maxx, 1)))
            # 低清栅格化看墨迹
            bmp = page.render(scale=0.35)
            pil = bmp.to_pil().convert("L")
            hist = pil.histogram()
            ink = sum(hist[:245]) / (pil.width * pil.height)
            body_txt = re.sub(r"(?s)^\s*\d+\s*$", "", txt).strip()  # 去掉页脚页码
            if ink < 0.002 and len(body_txt) < 10:
                blanks.append(i + 1)
        print("   空白页:", blanks if blanks else "无")
        print("   疑似越界页(右缘pt):", overflows if overflows else "无")
        report[name]["blanks"] = blanks
        report[name]["overflows"] = overflows
        report[name]["pages_text"] = pages_text
        doc.close()

    # 找样张页
    picks = {
        "代码总结": ["全局约定（阅读前必看）", "堆排序", "2026"],
        "重邮数据结构": ["邻接表定义如下", "Floyd", "InputList"],
    }
    for name, keys in picks.items():
        pt = report[name]["pages_text"]
        for key in keys:
            for i, t in enumerate(pt):
                if key in t and i >= 2:
                    print(f"[样张] {name} “{key}” → 第 {i+1} 页")
                    break
    # 保存抽取文本备查
    for name in SRC_FACTS:
        with open(os.path.join(BUILD, f"{name}_pages.txt"), "w", encoding="utf-8") as f:
            for i, t in enumerate(report[name]["pages_text"]):
                f.write(f"\n===== PAGE {i+1} =====\n{t}")
    print("OK")


if __name__ == "__main__":
    main()
