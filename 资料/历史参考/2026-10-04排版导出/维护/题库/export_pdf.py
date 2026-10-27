# -*- coding: utf-8 -*-
"""题库数据库 → 三册 PDF（HTML 中间产物 + headless Chrome 打印）。

分册（2026-09-28 主讲定）：
  精选题集  = 题集一档 + 408真题 + 802真题(2024/25/26)，章节→题型两层编排
  补充题集  = 题集二档+三档
  答案册    = 精选册范围内所有有答案的题（408+802真题；题集答案库中暂缺），
              序号与精选册一致，勘误以红框呈现（README 第六节口径，答案以修正版为准）
编排：章（chapters 表 order_num）→ 题型（选择/填空/程序阅读/综合应用/算法设计，
题集"解答"并入综合应用）→ 组内 题集按题号、408按年、真题按年。
考点只作标签行展示，不参与编排（本轮深度定档）。
图片：题集引用图已拷至 images/题集/；深色截图自动反色；低质图排除并留占位说明；
真题图按 figures 字段＋notes 提及关联，题面区/答案区页码决定出现在题面册还是答案册。

用法： python export_pdf.py            # 生成优化版 HTML 到 _tmp/pdf_build_optimized/
       python export_pdf.py --output-dir PATH  # 自定义 HTML 构建目录
       python export_pdf.py --order type-chapter --output-dir PATH
                                       # 题型→章 分区版（v3）：题型为一级、章为二级，
                                       # 全书序号按新顺序重编；默认 chapter-type 保持现行编排
       之后用 chrome --headless --print-to-pdf 渲染（命令见文件尾注释）。
"""
import argparse, base64, html as html_mod, io, json, os, re, shutil, sqlite3, sys
from PIL import Image, ImageOps
import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                                   # 题库数据库/
PROJ = os.path.dirname(ROOT)                                   # 项目根
DB = os.path.join(ROOT, "tiku.db")
BUILD = os.path.join(PROJ, "_tmp", "pdf_build_optimized")
IMG_TIJI = os.path.join(ROOT, "images", "题集")
IMG_ZHEN = os.path.join(ROOT, "images", "真题")

CHAPTERS = ["绪论", "线性表", "栈队列", "串", "数组广义表", "树", "图", "查找", "排序"]
QTYPES = ["选择", "填空", "程序阅读", "综合应用", "算法设计"]
QTYPE_MAP = {"选择": "选择", "填空": "填空", "程序阅读": "程序阅读",
             "综合应用": "综合应用", "算法设计": "算法设计", "解答": "综合应用"}
QTYPE_LABEL = {"选择": "选择题", "填空": "填空题", "程序阅读": "程序阅读题",
               "综合应用": "综合应用题", "算法设计": "算法设计题"}
SRC_ORDER = {"题集": 0, "408真题": 1, "真题2024": 2, "真题2025": 3, "真题2026": 4}
SRC_LABEL = {"题集": "题集", "408真题": "408真题", "真题2024": "802真题2024",
             "真题2025": "802真题2025", "真题2026": "802真题2026"}
CH_NUM = "一二三四五六七八九"


def ch_label(ch):
    """章标题：九章之内加"第X章"前缀。"""
    return f'第{CH_NUM[CHAPTERS.index(ch)]}章　{ch}' if ch in CHAPTERS else ch

# 人工快照审查（_tmp/pdf_build/sheet*.png）定的排除清单：低质图不附带
EXCLUDE = {
    "54a3345b6c98": "插图仅为装饰色块，非题目图形",
    "z26-p04-0.png": "回忆版手绘图照片，模糊不清（该题本就缺图，答案PDF已注明）",
}

# ---------------- 样式（v3：单蓝色强调 + 勘误红，字号成档，间距少量档位） ----------------
# 字号角色：题型一级 18pt / 章二级 14pt / 题号 12pt / 正文 10.5pt / 答案标签 9.5pt /
#           元数据·考点·图注 8.5pt / 代码 9pt / 页脚页码 9pt
# 间距档位：题型间=换页、章间=7mm、题间=3.2mm 区块、题内=1.5mm 一档
CSS = """
@page { size: A4; margin: 16mm 14mm 18mm 14mm;
        @bottom-center { content: counter(page); font: 9pt "Microsoft YaHei","PingFang SC",sans-serif; color: #8a9199; } }
* { box-sizing: border-box; }
html, body { padding: 0; background: white; }
body { font-family: "Microsoft YaHei","PingFang SC","SimSun",sans-serif;
       font-size: 10.5pt; line-height: 1.62; color: #222; overflow-wrap: break-word; }

/* 封面：排版式，无日期无过程痕迹 */
.cover { page-break-after: always; text-align: center; padding-top: 36mm; }
.cover h1 { font-size: 28pt; color: #2c5f8a; margin: 6mm 0 3mm; letter-spacing: 0.05em; }
.cover .sub { font-size: 12pt; color: #555; margin: 0; }
.cover .rule { width: 22mm; border-top: 2px solid #2c5f8a; margin: 9mm auto 8mm; }
.cover .stats { font-size: 10.5pt; color: #333; margin: 2mm 0; }
.cover .arrange { font-size: 9.5pt; color: #8a9199; margin: 8mm 0 0; }
.cover .meta { font-size: 9.5pt; color: #8a9199; margin-top: 24mm; }
.memo { text-align: left; width: 148mm; margin: 10mm auto 0; font-size: 9pt; color: #555;
        border-top: 1px solid #d8dee4; padding: 4mm 1mm 0; }
.memo h3 { font-size: 10.5pt; color: #2c5f8a; margin: 0 0 2mm; }
.memo ul { margin: 1mm 0; padding-left: 5.5mm; }
.memo li { margin: 1.4mm 0; line-height: 1.55; }
/* 标签芯片只此一档：蓝系浅底，信息靠文字本身 */
.tag, .tag.t1, .tag.t2, .tag.zt, .tag.kao { display: inline-block; background: #eef3f8;
       color: #2c5f8a; border-radius: 2px; padding: 0 1.2mm; font-size: 8.5pt; }

/* 目录：两级（题型→章 或 章→题型），带内部链接与题数 */
.toc { page-break-after: always; }
.toc .tochead, .toc h2 { font-size: 18pt; font-weight: bold; color: #2c5f8a;
        margin: 0 0 5mm; padding-bottom: 2.5mm; border-bottom: 2px solid #2c5f8a; }
.toc ol { list-style: none; margin: 0; padding: 0; }
.toc > ol > li { margin: 4.5mm 0 0; break-inside: avoid; }
.toc a { color: inherit; text-decoration: none; }
.toc a.c { font-size: 12pt; font-weight: bold; color: #222; }
.toc ol ol { padding: 1.2mm 0 0 2mm; }
.toc ol ol li { display: inline-block; margin: 1mm 6mm 1mm 0; font-size: 10pt; }
.toc a.t { color: #444; }
.cnt { font-size: 9.5pt; color: #8a9199; font-weight: normal; margin-left: 2mm; }

/* 一级=题型（强制换页），二级=章（不换页，靠间距与分隔线） */
h1.ch, h1.qt { page-break-before: always; font-size: 18pt; font-weight: bold; color: #2c5f8a;
               margin: 0 0 4.5mm; padding-bottom: 2.5mm; border-bottom: 2px solid #2c5f8a;
               break-after: avoid; }
h2.ch, h2.qt { font-size: 14pt; font-weight: bold; color: #1f2933;
               margin: 7mm 0 3mm; padding-bottom: 1.6mm; border-bottom: 1px solid #d8dee4;
               break-after: avoid; }

/* 题块：白底，细分隔线用 border-top（紧跟标题的首题无线），题号突出 */
.q { break-inside: auto; margin: 0; padding: 2.4mm 0 2.6mm; border-top: 0.5px solid #dbe1e7; }
h1 + .q, h2 + .q { border-top: none; padding-top: 0.5mm; }
.qh { margin: 0 0 1mm; color: #444; break-after: avoid; }
.qh .num { font-weight: bold; color: #2c5f8a; font-size: 12pt; margin-right: 2.5mm; }
.qh .src { font-size: 9pt; color: #444; }
.qmeta { color: #8a9199; font-size: 8.5pt; line-height: 1.4; margin-top: 0.3mm; }
.stem p { margin: 0.8mm 0; orphans: 2; widows: 2; }
.stem img, .figs img { max-width: 100%; max-height: 80mm; display: block; margin: 1.5mm auto;
                       object-fit: contain; }
.figs img { border: 1px solid #e8ecf0; }
figure { margin: 2mm 0; break-inside: avoid; }
.stem p:has(img) { break-inside: avoid; }
.stem pre, .stem code { font-family: Consolas, "Courier New", monospace; }
.stem pre { background: #f5f7f9; border-left: 2px solid #b9c9d6; padding: 2mm 3mm;
            font-size: 9pt; line-height: 1.45; white-space: pre-wrap; margin: 1.5mm 0;
            break-inside: auto; }
.stem code { background: #f5f7f9; font-size: 9pt; padding: 0 1mm; }
.stem pre code { background: none; padding: 0; }
.opts { padding-left: 8mm; margin: 0.8mm 0 0; }
.opts .optline { display: block; }
.figs { margin-top: 1.5mm; }
.figsrc { font-size: 8.5pt; color: #8a9199; text-align: center; margin: 0 0 1.5mm; }
.figmiss { color: #8a9199; font-style: italic; font-size: 9pt; }
.note { font-size: 8.5pt; color: #7a828a; margin-top: 1.5mm; border-top: 1px dashed #e3e8ec;
        padding-top: 1mm; }
.kd { font-size: 8.5pt; color: #7a828a; margin-top: 1.2mm; }
.kd b { color: #8a9199; font-weight: normal; }
.ansblock { margin-top: 1.8mm; }
.ansblock .lab { font-weight: bold; color: #2c5f8a; font-size: 9.5pt; margin: 1mm 0 0.5mm;
                 break-after: avoid; }
.ansblock .stem { padding-left: 7mm; }
.ansblock .stem p { margin: 0.6mm 0; }
.errata { border: 1px solid #e8c4c0; border-left: 3px solid #c0392b; background: #fdf3f2;
          padding: 2mm 3mm; margin: 2mm 0; font-size: 9.5pt; border-radius: 2px; }
.errata .t { color: #c0392b; font-weight: bold; margin-right: 2mm; }

.katex { font-size: 1.05em; }
"""

# ---------------- 图片处理 ----------------
_img_cache = {}

def img_data_uri(path, alt=""):
    """读图→深色自动反色→超宽降采样→base64。返回 (dataURI, 原尺寸) 或 None。"""
    key = os.path.abspath(path)
    if key in _img_cache:
        return _img_cache[key]
    try:
        im = Image.open(path)
        im = im.convert("RGB")
        w, h = im.size
        gray = im.convert("L")
        hist = gray.histogram()
        mean = sum(i * c for i, c in enumerate(hist)) / (w * h)
        if mean < 100:                       # 深色截图 → 反色成白底
            im = ImageOps.invert(im)
        if w > 1600:
            im = im.resize((1600, max(1, int(h * 1600 / w))))
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=88)
        uri = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
        _img_cache[key] = (uri, (w, h))
        return _img_cache[key]
    except Exception as e:
        print(f"  [warn] 图片读取失败 {path}: {e}")
        return None


def excl_reason(name):
    for k, v in EXCLUDE.items():
        if name.startswith(k):
            return v
    return None


# ---------------- 正文渲染 ----------------
_md = markdown.Markdown(extensions=["fenced_code", "tables"])

_L = re.compile(r"\\left(?![a-zA-Z])")
_R = re.compile(r"\\right(?![a-zA-Z])")


def _fix_span(s):
    """KaTeX 无法解析的 MinerU 残缺 LaTeX 的机械修复。"""
    s = re.sub(r"\\(?:medskip|smallskip|bigskip|noindent|centering)\b", " ", s)
    s = s.replace(r"\bar { \right] }", r"\right]")
    s = s.replace(r"\left{", r"\left\{").replace(r"\right}", r"\right\}")
    if len(_L.findall(s)) != len(_R.findall(s)):     # \left/\right 不配对 → 普通括号
        s = _L.sub("", _R.sub("", s))
    else:
        # 数量配对但结构错乱（\right 落在 \mathrm 组内）：退化为普通括号
        if r"\left(" in s and r"\mathrm {" in s and r"\right)" in s.split(r"\mathrm {", 1)[1]:
            s = _L.sub("", _R.sub("", s))
    if s == "\\":
        s = ""
    return s


def fix_math(text):
    """对正文中 $...$ / $$...$$ 公式 span 逐个修复；代码块不动。"""
    if not text or "$" not in text:
        return text
    out = []
    for p in re.split(r"(```.*?```)", text, flags=re.S):
        if p.startswith("```"):
            out.append(p)
            continue
        p = re.sub(r"\$\$(.+?)\$\$", lambda m: "$$" + _fix_span(m.group(1)) + "$$", p, flags=re.S)
        p = re.sub(r"\$[^\$\n]+?\$", lambda m: "$" + _fix_span(m.group(0)[1:-1]) + "$", p)
        out.append(p)
    return "".join(out)


def protect_math(text):
    """把 $...$/$$...$$ span 换成占位符，避免 markdown 吃掉公式中的反斜杠转义。"""
    spans = []

    def stash(m):
        spans.append(m.group(0))
        return f"MATHSPAN{len(spans) - 1}ENDSPAN"

    if not text or "$" not in text:
        return text, []
    t = re.sub(r"\$\$.+?\$\$", stash, text, flags=re.S)
    t = re.sub(r"\$[^\$\n]+?\$", stash, t)
    return t, spans


def restore_math(html_text, spans, escape=True):
    """还原公式占位符。escape=False 用于还要继续走 markdown/转义流程的场景。"""
    for i, s in enumerate(spans):
        if s.startswith("$$"):
            fixed = "$$" + _fix_span(s[2:-2]) + "$$"
        else:
            fixed = "$" + _fix_span(s[1:-1]) + "$"
        html_text = html_text.replace(
            f"MATHSPAN{i}ENDSPAN", html_mod.escape(fixed) if escape else fixed)
    return html_text

# ---------------- 渲染层 ASCII 字符图形串剔除（不改数据库原文） ----------------
# MinerU/OCR 把链表、邻接多重表等示意图识成无空格 ASCII 串（如
# "caebd^f1008H1000H1010H1004H100CH1014H"、"715^HEAD"、"a1010Hb100CH..."、
# "abcde0123401^13^20^3242^034^3^"）。导出时替换为占位说明。
# 保守口径：只处理"仅由字母/数字/^ 组成的无空格长串"，且满足下列之一：
#   1) 含 ^ 分隔；2) 含 ≥2 个带数字的 H 结尾十六进制地址。
# 公式在调用点前已被 MATHSPAN 占位符保护（见 clean_art 内的二次保护），
# 含空格的英文说明、代码、复杂度表达、Huffman 编码/遍历序列等不受影响。
_ART_RUN = re.compile(r"[A-Za-z0-9^]{6,}")
_ART_HEXH = re.compile(r"[0-9A-Fa-f]{2,4}H")
_ART_PLACEHOLDER = "〔结构示意未收录〕"


def _art_suspect(s):
    if "^" in s:
        return True
    hexh = [h for h in _ART_HEXH.findall(s) if any(c.isdigit() for c in h)]
    return len(hexh) >= 2


def clean_art(html_text):
    """剔除明显无空格 ASCII 字符图形/编码串，替换为占位说明。"""
    if not html_text or ("^" not in html_text and "H" not in html_text):
        return html_text
    # 遮蔽内嵌图片 base64 与公式占位符，避免被 run 正则误伤
    masked = []
    def mask(m):
        masked.append(m.group(0))
        return f"\ue001{len(masked) - 1}\ue002"
    tmp = re.sub(r"data:image/[A-Za-z0-9+/=;:.,]+", mask, html_text)
    tmp = re.sub(r"MATHSPAN\d+ENDSPAN", mask, tmp)
    tmp = _ART_RUN.sub(
        lambda m: _ART_PLACEHOLDER if _art_suspect(m.group(0)) else m.group(0), tmp)
    for i, t in enumerate(masked):
        tmp = tmp.replace(f"\ue001{i}\ue002", t, 1)
    return tmp


def img_ref_repl(m):
    """题集内嵌 ![](images/xx) → 图片或占位（stem_html 与 opts_html 共用）。"""
    name = os.path.basename(m.group(1).strip())
    reason = excl_reason(name)
    if reason:
        return f'<span class="figmiss">〔插图未收录：{reason}〕</span>'
    p = os.path.join(IMG_TIJI, name)
    got = img_data_uri(p)
    if not got:
        return f'<span class="figmiss">〔插图文件缺失〕</span>'
    uri, _ = got
    return f'<img src="{uri}" alt="题目插图">'


def opts_img_restore(body):
    """选项块 HTML 中残留的 ![](images/xx) 引用（转义后形态不变）替换为图片。"""
    return re.sub(r'!\[\]\(([^)]*)\)', img_ref_repl, body)


def stem_html(text, book):
    """题干 markdown → html；题集内嵌 ![](images/xx) 就地替换为图片或占位。"""
    text, spans = protect_math(text or "")
    _md.reset()
    out = _md.convert(re.sub(r'!\[\]\(([^)]*)\)', img_ref_repl, text))
    _md.reset()
    return clean_art(restore_math(out, spans))


# ---------------- 选项块：各选项各自一行 ----------------
_OPT_MARK = re.compile(r"([A-D])[．.]")


def find_option_marks(text):
    """在（已保护公式的）文本中顺序定位 A./B./C./D. 标记。

    支持前置空格/中文标点/公式结尾、句点或全角点、紧跟公式或普通文本；
    允许标记粘在单词后（如 "NULLC."、"1004HB."，选择题选项串中按
    A→B→C→D 顺序收敛，误判概率极低）。返回四个切分位置 [a,b,c,d]，
    未找齐时返回 None。
    """
    pos = {L: [] for L in "ABCD"}
    for m in _OPT_MARK.finditer(text):
        pos[m.group(1)].append(m.start())
    best = None
    for a in pos["A"]:                       # 取最靠后且后续仍有 B/C/D 的 A
        b = next((x for x in pos["B"] if x > a), None)
        if b is None:
            continue
        c = next((x for x in pos["C"] if x > b), None)
        if c is None:
            continue
        d = next((x for x in pos["D"] if x > c), None)
        if d is None:
            continue
        best = [a, b, c, d]
    return best


def _split_opts(o):
    """无换行的选项串按 B/C/D 标记首次出现断行（选项前常带数字，如 '7B.24'）。"""
    base = 0
    for mark in ("B", "C", "D"):
        m = re.search(mark + r"[．.]", o[base:])
        if not m:
            break
        idx = base + m.start()
        o = o[:idx] + "\n" + o[idx:]
        base = idx + 3                  # 换行 + 标记字母 + 句点
    return o


def opts_html(options):
    """各选项各自一行：按 A/B/C/D 标记逐段切出，段内乱换行折叠为空格；
    未找齐标记时回退原安全输出（单行按 B/C/D 断行，多行 pre-wrap）。"""
    if not options or options in ("[]", "{}", "null"):
        return ""
    fixed = fix_math(options)
    prot, spans = protect_math(fixed)
    marks = find_option_marks(prot)
    if marks:
        a, b, c, d = marks
        lines = []
        for seg in (prot[:b], prot[b:c], prot[c:d], prot[d:]):
            seg = html_mod.escape(re.sub(r"\s+", " ", seg).strip())
            if seg:
                lines.append(seg)
        if len(lines) >= 2:
            body = restore_math("<br>".join(lines), spans)   # 公式转义后还原，仅一次
            return f'<div class="opts">{clean_art(opts_img_restore(body))}</div>'
    opts = fixed
    if "\n" not in opts:        # 408 选项常为单行，按 B./C./D. 断行便于阅读
        opts = _split_opts(opts)
    body = html_mod.escape(opts).replace(chr(10), "<br>")
    return f'<div class="opts">{clean_art(opts_img_restore(body))}</div>'


def split_stem_options(stem):
    """题干粘连选项的选择题：渲染层把 A—D 选项串从题干切出（不改数据库）。

    返回 (stem_part, opts_part) 原始文本；未找齐 A/B/C/D 时返回 None。"""
    prot, spans = protect_math(stem or "")
    marks = find_option_marks(prot)
    if not marks:
        return None
    a = marks[0]
    stem_part = restore_math(prot[:a], spans, escape=False).rstrip()
    opts_part = restore_math(prot[a:], spans, escape=False).strip()
    if not stem_part or len(opts_part) < 4:
        return None
    return stem_part, opts_part


def notes_split(notes):
    """notes → (勘误文本 or None, 一般备注文本 or None)。"""
    if not notes:
        return None, None
    err = notes if any(k in notes for k in ("有误", "勘误", "矛盾", "存疑")) else None
    return err, notes


def qtags(q, book):
    t = []
    if q["source"] == "题集":
        tier = q["tier"] or ""
        cls = {"一档": "tag t1", "二档": "tag t2"}.get(tier, "tag")
        t.append(f'<span class="{cls}">题集{tier}</span>')
        if q["difficulty"]:
            t.append(f'<span class="tag">难度 {q["difficulty"]}</span>')
        if q["pdf_page"]:
            t.append(f'<span class="tag">原书 P{q["pdf_page"] - 9}</span>')
    elif q["source"] == "408真题":
        t.append('<span class="tag">408</span>')
        m = re.search(r"408-(\d{4})-", q["id"])
        if m:
            t.append(f'<span class="tag">{m.group(1)}年</span>')
    else:
        t.append(f'<span class="tag zt">{SRC_LABEL[q["source"]]}</span>')
    if q["template"]:
        t.append(f'<span class="tag kao">{html_mod.escape(q["template"])}</span>')
    return " ".join(t)


def kd_line(q):
    """考点行；解法模板（template，原在题头）并入此行并列展示，不丢信息。"""
    tpl = (q["template"] or "").strip()
    kd = (q["kaodian"] or "").strip()
    parts = []
    if tpl:
        parts.append(html_mod.escape(tpl))
    if kd:
        parts.append(clean_art(html_mod.escape(kd.replace(",", "、"))))
    if not parts:
        return ""
    return f'<div class="kd"><b>考点</b>　{"　｜　".join(parts)}</div>'


IMG_NAME_RE = re.compile(r"(?:images/真题/)?\b((?:a26|z26|z2425)-p\d+(?:-\d+)?\.png)")


def zhen_figs(q, zone):
    """真题图：zone='题面' 取 figures 字段＋notes/stem/答案解析提及的题面区图；
    zone='答案' 取 figures 字段中的答案区图＋提及的答案区图（a26-* 或 z2425-p≥13）。"""
    names = []
    for field in (q["figures"], q["notes"], q["stem"], q["answer"], q["analysis"]):
        if field:
            names += IMG_NAME_RE.findall(field)
    seen, out = set(), []
    for n in names:
        if n in seen:
            continue
        seen.add(n)
        is_answer_zone = n.startswith("a26-") or (
            n.startswith("z2425-") and int(re.search(r"p(\d+)", n).group(1)) >= 13)
        want = (zone == "答案") == is_answer_zone
        if want:
            out.append(n)
    return out


def figs_html(names, zone, book):
    if not names:
        return ""
    parts = []
    for n in names:
        reason = excl_reason(n)
        if reason:
            parts.append(f'<div class="figmiss">〔插图未收录：{reason}〕</div>')
            continue
        p = os.path.join(IMG_ZHEN, n)
        got = img_data_uri(p)
        if not got:
            parts.append(f'<div class="figmiss">〔插图文件缺失：{html_mod.escape(n)}〕</div>')
            continue
        uri, _ = got
        parts.append(f'<figure><img src="{uri}" alt="题目插图">')
        parts.append(f'<figcaption class="figsrc">图：{n}</figcaption></figure>')
    return f'<div class="figs">{"".join(parts)}</div>' if parts else ""


def q_header(q, seq):
    """题头：#N＋来源一行，难度·页码·内部ID 一行；章节与题型由分区结构承载，不重复。"""
    source = SRC_LABEL.get(q['source'], q['source']) + (q['tier'] or '' if q['source'] == '题集' else '')
    details = []
    if q['difficulty']:
        details.append(f"难度 {q['difficulty']}")
    if q['pdf_page']:
        details.append(f"原书 P{q['pdf_page'] - 9}" if q['source'] == '题集' else f"PDF P{q['pdf_page']}")
    details.append(q['id'])
    return (f'<div class="qh"><span class="num">#{seq}</span><span class="src">{html_mod.escape(source)}</span>'
            f'<div class="qmeta">{html_mod.escape("　·　".join(details))}</div></div>')


# ---------------- 数据装载 ----------------
def load():
    con = sqlite3.connect('file:' + DB.replace('\\', '/') + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute("SELECT * FROM questions")]
    con.close()
    for q in rows:
        q["qt"] = QTYPE_MAP.get(q["qtype"] or "", q["qtype"])
    return rows


def sort_key(q):
    """组内排序：题集按原书题号数值、408按年+题号、真题按年。"""
    qid = q["id"]
    m = re.search(r"(19|20)\d{2}", qid)
    year = int(m.group(0)) if m else 0
    m2 = re.search(r"(\d+)$", qid)
    num = int(m2.group(1)) if m2 else 0
    return (SRC_ORDER[q["source"]], year, num)


def build_index(rows):
    """index[(chapter, qt)] = [q...] 按章→题型→组内排序。"""
    idx = {}
    for q in rows:
        ch, qt = q["chapter"] or "未分类", q["qt"] or "未分类"
        idx.setdefault((ch, qt), []).append(q)
    for k in idx:
        idx[k].sort(key=sort_key)
    return idx


def ordered_pairs(idx, order="chapter-type", chapters=CHAPTERS):
    """[(chapter, qtype, [q...])]，空组跳过。

    chapter-type（默认）：章→题型，现行编排；type-chapter：题型→章（v3 分区版）。
    组内排序都沿用 sort_key；落在九章之外的章附在最后（数据中现无此类章）。
    """
    out = []
    if order == "chapter-type":
        for ch in chapters:
            for qt in QTYPES:
                qs = idx.get((ch, qt))
                if qs:
                    out.append((ch, qt, qs))
    else:
        for qt in QTYPES:
            for ch in chapters:
                qs = idx.get((ch, qt))
                if qs:
                    out.append((ch, qt, qs))
    for (ch, qt), qs in sorted(idx.items()):
        if ch not in chapters:
            out.append((ch, qt, qs))
    return out


# ---------------- 分册构造 ----------------
def select_jingxuan(rows):
    return [q for q in rows
            if q["source"] in ("408真题", "真题2024", "真题2025", "真题2026")
            or (q["source"] == "题集" and q["tier"] == "一档")]


def select_buchong(rows):
    return [q for q in rows if q["source"] == "题集" and q["tier"] in ("二档", "三档")]


def seq_map(qlist, order="chapter-type"):
    """全书连续序号：按当前编排遍历赋 #N（答案册复用精选册序号，不重编）。"""
    idx = build_index(qlist)
    m, n = {}, 0
    for ch, qt, qs in ordered_pairs(idx, order):
        for q in qs:
            n += 1
            m[q["id"]] = n
    return m


def book_html(title, subtitle, pairs, seqs, mode, order="chapter-type"):
    """mode: '题面' | '答案'；order: 'chapter-type'（章→题型，现行）| 'type-chapter'（题型→章，v3）。"""
    total = sum(len(qs) for _, _, qs in pairs)
    src_stat = {}
    for _, _, qs in pairs:
        for q in qs:
            src_stat[q["source"]] = src_stat.get(q["source"], 0) + 1
    stat_line = "　".join(f"{SRC_LABEL.get(k, k)} {v} 题" for k, v in
                          sorted(src_stat.items(), key=lambda x: SRC_ORDER.get(x[0], 9)))
    if len(src_stat) == 1:
        stat_line = ""

    H = [f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>{title}</title>',
         '<link rel="stylesheet" href="katex/dist/katex.min.css">',
         '<script defer src="katex/dist/katex.min.js"></script>',
         '<script defer src="katex/dist/contrib/auto-render.min.js"></script>',
         f"<style>{CSS}</style></head><body>",
         '<script>',
         'document.addEventListener("DOMContentLoaded", function() {',
         '  renderMathInElement(document.body, {delimiters: [',
         '    {left: "$$", right: "$$", display: true},',
         '    {left: "\\\\(", right: "\\\\)", display: false},',
         '    {left: "\\\\[", right: "\\\\]", display: true},',
         '    {left: "$", right: "$", display: false}],',
         '    ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code"],',
         '    throwOnError: false, errorColor: "#999999"});',
         '});',
         '</script>']

    # 封面（排版式，无日期、无过程痕迹）
    memo = MEMO[title]
    if order == "type-chapter":
        memo = memo.replace("<ul>", "<ul>" + ARRANGE_NOTE, 1)
    arrange = ("编排：按题型分区，题型内按章排列" if order == "type-chapter"
               else "编排：章 → 题型（选择/填空/程序阅读/综合应用/算法设计）")
    stat_html = f'<div class="stats">{stat_line}</div>' if stat_line else ""
    H.append(f'''<div class="cover"><h1>{title}</h1><div class="sub">{subtitle}</div>
<div class="rule"></div>
{stat_html}<div class="stats">合计 <b>{total}</b> 题</div>
<div class="arrange">{arrange}</div>
<div class="memo">{memo}</div>
<div class="meta">伴梦研途 · 重邮802数据结构代码课</div></div>''')

    # 目录：两级、带内部链接与题数；标题层级即书签层级
    if order == "chapter-type":
        chapters = list(dict.fromkeys(ch for ch, _, _ in pairs))
        chapter_id = {ch: f'ch-{i+1}' for i, ch in enumerate(chapters)}
        chapter_total = {ch: sum(len(qs) for c, _, qs in pairs if c == ch) for ch in chapters}
        H.append('<div class="toc"><h2>目录</h2><ol>')
        for ch in chapters:
            H.append(f'<li><a class="c" href="#{chapter_id[ch]}">{html_mod.escape(ch_label(ch))}'
                     f'<span class="cnt">{chapter_total[ch]} 题</span></a><ol>')
            for i, (c, qt, qs) in enumerate(pairs):
                if c == ch:
                    H.append(f'<li><a class="t" href="#type-{i}">{QTYPE_LABEL[qt]}'
                             f'<span class="cnt">{len(qs)} 题</span></a></li>')
            H.append('</ol></li>')
        H.append('</ol></div>')
    else:
        parts = list(dict.fromkeys(qt for _, qt, _ in pairs))      # pairs 已按 QTYPES 序
        part_id = {qt: f'part-{j+1}' for j, qt in enumerate(parts)}
        part_total = {qt: sum(len(qs) for c, t, qs in pairs if t == qt) for qt in parts}
        H.append('<div class="toc"><div class="tochead">目录</div><ol>')
        for qt in parts:
            H.append(f'<li><a class="c" href="#{part_id[qt]}">{QTYPE_LABEL[qt]}'
                     f'<span class="cnt">{part_total[qt]} 题</span></a><ol>')
            for i, (c, t, qs) in enumerate(pairs):
                if t == qt:
                    H.append(f'<li><a class="t" href="#sec-{i}">{html_mod.escape(ch_label(c))}'
                             f'<span class="cnt">{len(qs)} 题</span></a></li>')
            H.append('</ol></li>')
        H.append('</ol></div>')

    # 一级标题强制换页（题型分区版：题型；章→题型版：章），二级标题不换页靠间距分隔
    last_top = None
    for i, (ch, qt, qs) in enumerate(pairs):
        if order == "chapter-type":
            if ch != last_top:
                H.append(f'<h1 class="ch" id="{chapter_id[ch]}">{html_mod.escape(ch_label(ch))}'
                         f'<span class="cnt">{chapter_total[ch]} 题</span></h1>')
                last_top = ch
            H.append(f'<h2 class="qt" id="type-{i}">{QTYPE_LABEL[qt]}'
                     f'<span class="cnt">{len(qs)} 题</span></h2>')
        else:
            if qt != last_top:
                H.append(f'<h1 class="qt" id="{part_id[qt]}">{QTYPE_LABEL[qt]}'
                         f'<span class="cnt">{part_total[qt]} 题</span></h1>')
                last_top = qt
            H.append(f'<h2 class="ch" id="sec-{i}">{html_mod.escape(ch_label(ch))}'
                     f'<span class="cnt">{len(qs)} 题</span></h2>')
        for q in qs:
            seq = seqs[q["id"]]
            H.append(f'<div class="q" id="q-{html_mod.escape(q["id"])}" data-seq="{seq}">')
            H.append(q_header(q, seq))
            if mode == "题面":
                stem, opts_raw = q["stem"], q["options"]
                if q["qt"] == "选择" and not (opts_raw or "").strip():
                    got = split_stem_options(stem)   # 选项粘在题干：渲染层拆出
                    if got:
                        stem, opts_raw = got
                H.append(f'<div class="stem">{stem_html(stem, mode)}</div>')
                H.append(opts_html(opts_raw))
                if q["source"] != "题集":
                    H.append(figs_html(zhen_figs(q, "题面"), "题面", mode))
                err, note = notes_split(q["notes"])
                if q["source"] in ("真题2024", "真题2025", "真题2026") and note:
                    H.append(f'<div class="note">备注：{clean_art(html_mod.escape(note))}</div>')
            else:
                # 不截取题干：避免在公式内部切断，题号与 ID 足以对应精选册。
                if q["source"] != "题集":
                    H.append(figs_html(zhen_figs(q, "答案"), "答案", mode))
                ans = (q["answer"] or "").strip()
                ana = (q["analysis"] or "").strip()
                if ans:
                    H.append(f'<div class="ansblock"><div class="lab">答案</div>'
                             f'<div class="stem">{md_safe(ans)}</div></div>')
                if ana:
                    H.append(f'<div class="ansblock"><div class="lab">解析</div>'
                             f'<div class="stem">{md_safe(ana)}</div></div>')
                err, note = notes_split(q["notes"])
                if q["source"] in ("真题2024", "真题2025", "真题2026"):
                    if err:
                        H.append(f'<div class="errata"><span class="t">【勘误·以修正版为准】</span>'
                                 f'{clean_art(html_mod.escape(note))}</div>')
                    elif note:
                        H.append(f'<div class="note">备注：{clean_art(html_mod.escape(note))}</div>')
            H.append(kd_line(q))
            H.append("</div>")
    H.append("</body></html>")
    return "\n".join(H)


def md_safe(text):
    text, spans = protect_math(text or "")
    _md.reset()
    out = _md.convert(re.sub(r'!\[\]\(([^)]*)\)', lambda m: "〔图〕", text))
    return clean_art(restore_math(out, spans))


# type-chapter 分区版：编制说明加入编排口径一条（其余说明内容原样保留）
ARRANGE_NOTE = ("<li>编排：全书按题型分区，同一题型内按章节先后排列；"
                "目录与 PDF 书签即按此两级组织。</li>")

MEMO = {
    "精选题集": """<h3>编制说明</h3><ul>
<li>题源：严蔚敏《数据结构题集（第2版）》一档题（按价值分档）、408 统考真题 2015—2026（数据结构部分，按 802 考纲筛选）、重邮 802 真题 2024—2026（回忆版＋答案，答案勘误已入库）。</li>
<li>标记：<span class="tag t1">题集一档</span>=有价值必做　<span class="tag">难度①—⑤</span>=原书难度；802 真题、408 不设档。</li>
<li>题型口径：题集的"解答"题并入"综合应用题"。</li>
<li>插图为原书/答案 PDF 截图：深色底已自动反色，个别质量过差的未收录并留有占位说明；题集插图可按"原书页码 = PDF 页 − 9"回查原书。</li>
<li>考点仅作标签展示，未参与编排。</li>
<li>本册不含答案。《答案册》仅收录本册 408＋802 真题答案（序号一一对应）；题集一档答案暂缺。</li></ul>""",
    "补充题集": """<h3>编制说明</h3><ul>
<li>题源：严蔚敏《数据结构题集（第2版）》二档题（可做可不做）与三档题（了解即可），全书 9 章全部题面。</li>
<li>标记：<span class="tag t2">题集二档</span>=可做可不做　<span class="tag">题集三档</span>=了解即可　<span class="tag">难度①—⑤</span>=原书难度；三档题暂无考点标签。</li>
<li>题型口径：题集的"解答"题并入"综合应用题"。</li>
<li>插图为原书截图，个别质量过差的未收录并留有占位说明；可按"原书页码 = PDF 页 − 9"回查原书。</li>
<li>本册不含答案：题集官方答案区（书末）暂未识别入库，待补后另出修订。</li></ul>""",
    "答案册": """<h3>编制说明</h3><ul>
<li>本册收录《精选题集》范围内有答案的全部题目（408＋802真题）；题集（含一档）的官方答案区暂未识别入库，故无答案，待补后另出修订。</li>
<li>题号 #N 与《精选题集》一一对应；保留题目 ID 以便检索对照。</li>
<li>红框【勘误·以修正版为准】：答案 PDF 存在错误或存疑、经核对后修正的题目（详见题库 README 第六节），讲题/刷题一律以修正版为准。</li>
<li>802 真题为回忆版，个别题图缺失、题面不全，备注中如实标注。</li></ul>""",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', default=BUILD, help='HTML 和本地 KaTeX 输出目录')
    parser.add_argument('--order', choices=('chapter-type', 'type-chapter'), default='chapter-type',
                        help='编排：chapter-type 章→题型（现行，可复现）；type-chapter 题型→章（v3 分区版）')
    args = parser.parse_args()
    order = args.order
    build = os.path.abspath(args.output_dir)
    os.makedirs(build, exist_ok=True)
    katex = os.path.join(build, 'katex')
    if not os.path.exists(katex):
        shutil.copytree(os.path.join(PROJ, '_tmp', 'pdf_build', 'katex'), katex)
    rows = load()
    print(f"库中共 {len(rows)} 题；编排 {order}")
    jx = select_jingxuan(rows)
    bc = select_buchong(rows)
    print(f"精选 {len(jx)} 题（一档 {sum(1 for q in jx if q['source']=='题集')}＋408 "
          f"{sum(1 for q in jx if q['source']=='408真题')}＋802真题 "
          f"{sum(1 for q in jx if q['source'].startswith('真题'))}）；补充 {len(bc)} 题")

    seqs = seq_map(jx, order)                # 精选册序号，答案册复用（对应关系不变）
    books = [
        ("精选题集", "一档必做题 ＋ 408统考真题 ＋ 重邮802真题（2024—2026）",
         ordered_pairs(build_index(jx), order), "题面", seqs),
        ("补充题集", "严蔚敏题集 二档（可做可不做）与 三档（了解即可）题面",
         ordered_pairs(build_index(bc), order), "题面", seq_map(bc, order)),
        ("答案册", "《精选题集》全部答案与解析（408＋802真题；题集答案暂缺）",
         ordered_pairs(build_index([q for q in jx if q["source"] != "题集"]), order), "答案", seqs),
    ]
    for name, sub, pairs, mode, seqs_i in books:
        html = book_html(name, sub, pairs, seqs_i, mode, order)
        out = os.path.join(build, f"{name}_优化版.html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        n = sum(len(qs) for _, _, qs in pairs)
        print(f"  {name}.html  {n} 题  {len(html)//1024} KB")


if __name__ == "__main__":
    main()

# 渲染命令（chrome 路径按本机）：
# "C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --disable-gpu ^
#   --no-pdf-header-footer --generate-pdf-document-outline --virtual-time-budget=60000 ^
#   --print-to-pdf="题库数据库\导出\精选题集.pdf" "file:///D:/Program%20Project/SpecialtyCourses/_tmp/pdf_build/精选题集.html"
