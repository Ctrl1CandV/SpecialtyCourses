# -*- coding: utf-8 -*-
"""两册笔记 → 打印版 HTML（供 Chrome headless 出 PDF）。
设计族与题库 PDF 一致：蓝色 #2c5f8a 强调、Microsoft YaHei 正文、Consolas 代码。
阅读型文档标准：11pt 正文 1.7 行高、代码 8.75pt 浅底、表格通栏浅边框、图片块级居中限高、
A4 对称页边距、@bottom-center 页码、Generate 目录页（H1/H2 内部链接）。
"""
import base64
import html as H
import io
import os
import re
import sys

import markdown_it
from PIL import Image, ImageOps, ImageStat

ROOT = r"D:/Program Project/SpecialtyCourses"
NOTES = os.path.join(ROOT, "_tmp/pdf_v3/notes_opt")
IMGDIR = os.path.join(ROOT, "知识笔记", "image")
BUILD = os.path.join(ROOT, "_tmp/pdf_v3/build_notes")

BOOKS = [
    # (md 文件, 册名, 定位语)
    ("代码总结.md", "代码总结", "重邮802数据结构 · 主讲笔记"),
    ("重邮数据结构.md", "重邮数据结构", "重邮802数据结构 · 主讲笔记"),
]

MATH_ST, MATH_EN = "\ue000", "\ue001"  # 数学占位符定界符（私有区）

# ---------------- 数学保护 ----------------

def protect_math(t):
    """把 $$ 块与行内 $...$ 换成占位符，避免 markdown 吃掉反斜杠/下划线。"""
    store = []
    lines = t.split("\n")
    res, inf, j = [], False, 0
    while j < len(lines):
        L = lines[j]
        if L.strip().startswith("```"):
            inf = not inf
            res.append(L)
            j += 1
            continue
        if not inf and L.strip() == "$$":
            k = j + 1
            buf = []
            while k < len(lines) and lines[k].strip() != "$$":
                buf.append(lines[k])
                k += 1
            if k >= len(lines):
                raise ValueError(f"未闭合的 $$ 块（第 {j+1} 行起）")
            store.append("$$\n" + "\n".join(buf) + "\n$$")
            res.append(MATH_ST + str(len(store) - 1) + MATH_EN)
            j = k + 1
            continue
        res.append(L)
        j += 1
    t = "\n".join(res)
    out = []
    inf = False
    n_inline = 0
    for L in t.split("\n"):
        if L.strip().startswith("```"):
            inf = not inf
            out.append(L)
            continue
        if not inf and "$" in L:
            def repl(m):
                store.append(m.group(0))
                return MATH_ST + str(len(store) - 1) + MATH_EN
            L, n = re.subn(r"\$([^$\n]+)\$", repl, L)
            n_inline += n
        out.append(L)
    return "\n".join(out), store, len([s for s in store if s.startswith("$$")]), n_inline


def restore_math(html_text, store):
    def rep(m):
        raw = store[int(m.group(1))]
        return H.escape(raw, quote=False)
    return re.sub(MATH_ST + r"(\d+)" + MATH_EN, rep, html_text)


# ---------------- 图片 ----------------

def img_uri(fname):
    p = os.path.join(IMGDIR, fname)
    im = Image.open(p).convert("RGBA")
    # 深色底检测必须忽略 alpha（透明底＋浅色笔画的图，RGB 通道才是真实"主题色"）
    rgb_mean = ImageStat.Stat(im.convert("RGB").convert("L")).mean[0]
    inverted = rgb_mean < 100
    if inverted:
        r, g, b, a = im.split()
        rgb = ImageOps.invert(Image.merge("RGB", (r, g, b)))  # 只反色 RGB，保留 alpha
        im = Image.merge("RGBA", (*rgb.split(), a))
    amin, _ = im.getchannel("A").getextrema()
    if amin < 255:
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im)
    im = im.convert("RGB")
    flat_mean = ImageStat.Stat(im.convert("L")).mean[0]
    resized = ""
    if max(im.size) > 1600:
        r = 1600 / max(im.size)
        im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
        resized = f"→{im.width}x{im.height}"
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88, optimize=True)
    uri = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    return uri, rgb_mean, flat_mean, inverted, resized, len(buf.getvalue()) // 1024


def inline_images(t):
    def repl(m):
        fname = m.group(2)
        uri, rgb_mean, flat_mean, inv, resized, kb = img_uri(fname)
        print(f"  [img] {fname:24s} rgb={rgb_mean:5.1f} flat={flat_mean:5.1f} "
              f"invert={'Y' if inv else 'n'} {resized or '':>10s} {kb:4d}KB")
        if inv:
            Image.open(io.BytesIO(base64.b64decode(uri.split(",", 1)[1]))
                       ).save(os.path.join(BUILD, "..", "pages", f"_inv_{fname}.png"))
        return "](" + uri + ")"
    return re.sub(r"\]\((image/([^)]+))\)", repl, t)


# ---------------- 标题与目录 ----------------

def scan_headings(t):
    """扫描围栏外的 #/## 标题，返回 [(level, 纯文本)]。"""
    toc, inf = [], False
    for L in t.split("\n"):
        s = L.strip()
        if s.startswith("```"):
            inf = not inf
            continue
        if inf:
            continue
        m = re.match(r"^(#{1,2})\s+(.*)$", s)
        if m:
            txt = m.group(2)
            txt = re.sub(r"\*\*|\*|`", "", txt).strip()
            txt = H.escape(txt, quote=False)
            toc.append((len(m.group(1)), txt))
    return toc


def inject_ids(body_html, toc):
    """按出现顺序给 h1/h2 注入 id，并断言与 md 扫描数一致。"""
    state = {"n": 0}
    def repl(m):
        tag = m.group(1)
        i = state["n"]
        state["n"] += 1
        return f'<h{tag} id="s-{i}">'
    out = re.sub(r"<h([12])>", repl, body_html)
    assert state["n"] == len(toc), f"标题数不一致 HTML={state['n']} md={len(toc)}"
    return out


def build_toc_html(toc):
    lis = []
    for lv, txt in toc:
        cls = "l1" if lv == 1 else "l2"
        lis.append(f'<li class="{cls}"><a href="#s-{len(lis)}">{txt}</a></li>')
    return '<nav class="toc"><div class="toc-title">目 录</div><ul>' + "".join(lis) + "</ul></nav>"


# ---------------- CSS ----------------

CSS = """
@page { size: A4; margin: 17mm 20mm 19mm 20mm;
        @bottom-center { content: counter(page); font: 9pt "Microsoft YaHei","PingFang SC",sans-serif; color: #8a9096; } }
* { box-sizing: border-box; }
html, body { padding: 0; margin: 0; background: #fff; }
body { font-family: "Microsoft YaHei","PingFang SC","SimHei",sans-serif;
       font-size: 11pt; line-height: 1.7; color: #222; overflow-wrap: break-word; }

/* 封面：克制，无日期无过程痕迹 */
.cover { page-break-after: always; text-align: center; padding-top: 62mm; }
.cover .rule { width: 14mm; height: 1.2mm; background: #2c5f8a; margin: 0 auto 9mm; }
.cover .title { font-size: 30pt; font-weight: bold; color: #2c5f8a; letter-spacing: 0.06em; margin: 0 0 6mm; }
.cover .sub { font-size: 12.5pt; color: #666; }
.cover .note { margin-top: 64mm; font-size: 9.5pt; color: #b0b6bc; }

/* 目录 */
.toc { page-break-after: always; }
.toc .toc-title { font-size: 16pt; font-weight: bold; color: #2c5f8a; margin: 0 0 5mm;
                  border-bottom: 2px solid #2c5f8a; padding-bottom: 2mm; }
.toc ul { list-style: none; margin: 0; padding: 0; }
.toc li { line-height: 1.45; }
.toc li.l1 { font-weight: bold; font-size: 11.5pt; margin: 2.2mm 0 0.8mm; }
.toc li.l2 { font-size: 10.5pt; margin: 0.6mm 0 0.6mm 8mm; color: #444; font-weight: normal; }
.toc a { color: inherit; text-decoration: none; }

/* 正文标题 */
.body h1 { page-break-before: always; break-after: avoid; font-size: 16pt; color: #2c5f8a;
           border-bottom: 2px solid #2c5f8a; padding-bottom: 2mm; margin: 2mm 0 4mm; }
.body h1:first-of-type { page-break-before: auto; }
.body h2 { break-after: avoid; font-size: 13pt; color: #2c5f8a; border-left: 4px solid #2c5f8a;
           padding-left: 2.5mm; margin: 6mm 0 3mm; }
.body h3 { break-after: avoid; font-size: 12pt; color: #1f3f5c; margin: 5mm 0 2.5mm; }
.body h4 { break-after: avoid; font-size: 11.5pt; color: #333; margin: 4mm 0 2mm; }
.body h5 { break-after: avoid; font-size: 11pt; color: #555; margin: 3.5mm 0 2mm; }
.body h6 { break-after: avoid; font-size: 10.5pt; color: #666; }

.body p { margin: 1.6mm 0; orphans: 2; widows: 2; }
.body ul, .body ol { margin: 1.6mm 0; padding-left: 7mm; }
.body li { margin: 0.9mm 0; }
.body hr { border: 0; border-top: 1px solid #d0d6da; margin: 5mm 0; }

/* 代码 */
.body pre, .body code { font-family: Consolas, "Courier New", monospace; }
.body code { background: #f5f7f9; font-size: 9pt; padding: 0 1mm; border-radius: 2px; }
.body pre { background: #f5f7f9; border-left: 3px solid #9db8ce; padding: 2.2mm 3mm;
            font-size: 8.75pt; line-height: 1.5; white-space: pre-wrap; overflow-wrap: break-word;
            margin: 2mm 0 3mm; }
.body pre code { background: none; padding: 0; font-size: inherit; }

/* 引用块（思路要点/易错提示） */
.body blockquote { border-left: 3px solid #9db8ce; background: #f6f8fa; color: #44505a;
                   padding: 1.8mm 3mm; margin: 2mm 0 3mm; }
.body blockquote p { margin: 0.8mm 0; }

/* 表格：通栏浅边框 */
.body table { width: 100%; border-collapse: collapse; margin: 2.5mm 0 3.5mm; font-size: 9.5pt; line-height: 1.5; }
.body th { background: #eef3f8; color: #2c5f8a; font-weight: bold; }
.body th, .body td { border: 1px solid #d9dee3; padding: 1.2mm 2mm; text-align: center; }
.body td code, .body th code { font-size: 8.5pt; }
.body thead { break-inside: avoid; }

/* 图片：块级居中限高 */
.body img { display: block; margin: 2.5mm auto; max-width: 100%; max-height: 72mm; }
.body p.lead-fig { page-break-after: always; break-inside: avoid; margin: 8mm 0 0; }
.body p.lead-fig img { max-height: 195mm; }
.body p:has(img) { break-inside: avoid; margin: 2mm 0; }

/* 公式 */
.katex { font-size: 1.08em; }
.katex-display { margin: 3mm 0; }
"""

AUTO_RENDER = """
document.addEventListener("DOMContentLoaded", function() {
  renderMathInElement(document.body, {delimiters: [
    {left: "$$", right: "$$", display: true},
    {left: "\\\\(", right: "\\\\)", display: false},
    {left: "\\\\[", right: "\\\\]", display: true},
    {left: "$", right: "$", display: false}],
    ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code"],
    throwOnError: false, errorColor: "#999999"});
});
"""


def build_one(md_name, title, subtitle):
    src = io.open(os.path.join(NOTES, md_name), encoding="utf-8").read()
    # 删掉 [toc] 标记（目录由脚本自 Generate）
    src = re.sub(r"(?m)^\[toc\]\s*$\n?", "", src)
    n_img_before = len(re.findall(r"\]\(image/", src))

    prot, store, n_disp, n_inline = protect_math(src)
    print(f"[{title}] 数学：display 块 {n_disp}，行内 {n_inline}，占位 {len(store)}")
    prot = inline_images(prot)

    # CommonMark 渲染（源笔记的嵌套列表缩进是 CommonMark 口径）＋表格
    md = markdown_it.MarkdownIt("js-default", {"html": False, "linkify": False})
    md.enable("table")
    body = md.render(prot)
    body = restore_math(body, store)

    toc = scan_headings(src)
    body = inject_ids(body, toc)
    print(f"[{title}] H1/H2 标题 {len(toc)} 个（H1 {sum(1 for l,_ in toc if l==1)} / H2 {sum(1 for l,_ in toc if l==2)}）")
    n_img_html = len(re.findall(r'src="data:image/', body))
    print(f"[{title}] 图片：md 引用 {n_img_before}，内嵌 {n_img_html}")
    assert n_img_before == n_img_html, "有图片未内嵌成功"

    # 首图（思维导图）单独放大
    body = body.replace("<p><img", '<p class="lead-fig"><img', 1)

    page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>{H.escape(title)}</title>
<link rel="stylesheet" href="katex/dist/katex.min.css">
<script defer src="katex/dist/katex.min.js"></script>
<script defer src="katex/dist/contrib/auto-render.min.js"></script>
<style>{CSS}</style></head><body>
<div class="cover"><div class="rule"></div><div class="title">{H.escape(title)}</div>
<div class="sub">{H.escape(subtitle)}</div><div class="note">数据结构 · 考研笔记</div></div>
{build_toc_html(toc)}
<div class="body">
{body}
</div>
<script>{AUTO_RENDER}</script>
</body></html>"""
    out_html = os.path.join(BUILD, f"{title}.html")
    io.open(out_html, "w", encoding="utf-8", newline="\n").write(page)
    print(f"[{title}] HTML 写出：{out_html}（{os.path.getsize(out_html)//1024}KB）")
    return out_html, len(store)


def main():
    for md_name, title, subtitle in BOOKS:
        build_one(md_name, title, subtitle)


if __name__ == "__main__":
    main()
