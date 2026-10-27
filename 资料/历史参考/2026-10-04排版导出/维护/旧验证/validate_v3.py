# -*- coding: utf-8 -*-
"""v3 分区版三册 PDF 程序化验收。

检查项（对应任务验收清单）：
  1. tiku.db 哈希不变（只读）
  2. 三册题 ID 集合与基线（改动前默认行为）一致，仅顺序不同；数量 401/553/223
  3. 精选/补充册 v3 序号连续 1..N；答案册序号与精选册一一对应
  4. type-chapter 结构：题型一级（h1）→ 章二级（h2），节题数求和=总题数，目录锚点存在
  5. PDF 书签：一级=题型（+书名/编制说明），二级=章，目标页有效
  6. 目录内部链接注解全部可解析
  7. 无空白页、无文本越界、页脚页码存在
  8. KaTeX 公式错误与基线比无新增（math_check 单独跑 node 脚本）
结果写 _tmp/pdf_v3/validation.json。
"""
import hashlib
import json
import pathlib
import re
import sys

from pypdf import PdfReader
import pypdfium2 as pdfium

R = pathlib.Path('D:/Program Project/SpecialtyCourses')
V3 = R / '_tmp/pdf_v3'
BUILD = V3 / 'build_ji'
OUT = V3 / '产出'
DB = R / '题库数据库/tiku.db'
NAMES = [('精选题集', 401), ('补充题集', 553), ('答案册', 223)]
QTYPES = ['选择', '填空', '程序阅读', '综合应用', '算法设计']
QTYPE_LABEL = {'选择': '选择题', '填空': '填空题', '程序阅读': '程序阅读题',
               '综合应用': '综合应用题', '算法设计': '算法设计题'}
Q_RE = re.compile(r'<div class="q" id="q-([^"]+)" data-seq="(\d+)">')

res = {'books': {}, 'checks': {}}
ok = True


def chk(name, cond, detail=''):
    global ok
    ok &= bool(cond)
    res['checks'][name] = {'pass': bool(cond), 'detail': detail}
    print(('PASS ' if cond else 'FAIL ') + name + ('　' + detail if detail else ''))


# 1) tiku.db 哈希
h = hashlib.sha256(DB.read_bytes()).hexdigest()
chk('tiku_db_hash_unchanged', h == '6684ce361bebf47c1be0b59e1a521e7af03088dd42b26192d4d90ea311ddb3ea', h)

for name, count in NAMES:
    html = (BUILD / f'{name}_优化版.html').read_text(encoding='utf-8')
    seqs = [(i, int(s)) for i, s in Q_RE.findall(html)]
    base = [(i, int(s)) for i, s in
            Q_RE.findall((V3 / 'baseline_order' / f'{name}_优化版.html').read_text(encoding='utf-8'))]
    b = {'questions': len(seqs)}

    # 2) 集合一致、数量、仅顺序不同
    chk(f'{name}_set_same_as_baseline', sorted(x[0] for x in seqs) == sorted(x[0] for x in base))
    chk(f'{name}_count', len(seqs) == count, f'{len(seqs)}/{count}')

    # 4) 结构与序号
    if name != '答案册':
        cont = [s for _, s in seqs] == list(range(1, count + 1))
        chk(f'{name}_seq_continuous', cont)
    else:
        jxmap = dict((i, int(s)) for i, s in
                     Q_RE.findall((BUILD / '精选题集_优化版.html').read_text(encoding='utf-8')))
        chk('答案册_seq_matches_jingxuan',
            all(jxmap.get(i) == s for i, s in seqs), f'{len(seqs)} 题')
    secs = re.findall(r'<h2 class="ch" id="sec-(\d+)">(.*?)<span class="cnt">(\d+) 题</span>', html)
    parts = re.findall(r'<h1 class="qt" id="part-(\d+)">(.*?)<span class="cnt">(\d+) 题</span>', html)
    chk(f'{name}_sections_sum', sum(int(s[2]) for s in secs) == count,
        f'{len(parts)} 题型区 / {len(secs)} 章节')
    # 题型区顺序符合 QTYPES
    plabels = [p[1] for p in parts]
    expect = [QTYPE_LABEL[qt] for qt in QTYPES if QTYPE_LABEL[qt] in plabels]
    chk(f'{name}_part_order', plabels == expect, '→'.join(plabels))
    ids = set(re.findall(r'id="(part-\d+|sec-\d+)"', html))
    hrefs = set(re.findall(r'href="#(part-\d+|sec-\d+)"', html))
    chk(f'{name}_toc_anchors', hrefs <= ids, f'{len(hrefs)} 个目录锚点')

    # 5-7) PDF 层
    pdfpath = OUT / f'{name}.pdf'
    pdf = PdfReader(str(pdfpath))
    doc = pdfium.PdfDocument(str(pdfpath))
    texts = [pg.extract_text() or '' for pg in pdf.pages]
    blank = [i + 1 for i, t in enumerate(texts) if len(re.sub(r'\s', '', t)) < 5]
    chk(f'{name}_no_blank_pages', not blank, f'pages={len(pdf.pages)}')

    overflow = []
    for i, page in enumerate(doc):
        tp = page.get_textpage()
        w, hgt = page.get_size()
        for j in range(tp.count_rects()):
            l, bb, rr, tt = tp.get_rect(j)
            if l < -1 or bb < -1 or rr > w + 1 or tt > hgt + 1:
                overflow.append(i + 1)
                break
    chk(f'{name}_no_text_overflow', not overflow, str(overflow[:5]))

    pageno_missing = [i + 1 for i, t in enumerate(texts)
                      if not re.search(r'(?<!\d)' + str(i + 1) + r'(?!\d)', t)]
    chk(f'{name}_footer_page_numbers', not pageno_missing, str(pageno_missing[:5]))

    # 书签：一级 = 书名 + 题型（按出现序）；题型下二级 = 章
    flat = []

    def walk(items, depth=0):
        for it in items:
            if isinstance(it, list):
                walk(it, depth + 1)
            else:
                dest = pdf.get_destination_page_number(it)
                assert dest is not None and 0 <= dest < len(pdf.pages), it.title
                flat.append((depth, it.title, dest + 1))

    walk(pdf.outline)
    roots = [t for d, t, _ in flat if d == 0]
    want_parts = [QTYPE_LABEL[qt] for qt in QTYPES
                  if any(p[1].startswith(QTYPE_LABEL[qt]) for p in parts)]
    got_parts = [next(w for w in want_parts if t.startswith(w))
                 for t in roots if any(t.startswith(w) for w in want_parts)]
    chk(f'{name}_outline_level1_parts', got_parts == want_parts,
        f'一级书签（除书名）: {got_parts}')
    subc = {}
    last_root = None
    for d, t, _ in flat:
        if d == 0:
            last_root = next((w for w in want_parts if t.startswith(w)), None)
        elif last_root:
            subc.setdefault(last_root, []).append(t)
    nch = sum(len(v) for v in subc.values())
    chk(f'{name}_outline_level2_chapters', nch == len(secs),
        f'章书签 {nch} 个；例: {subc[want_parts[0]][:3] if subc else []}')
    b['pages'] = len(pdf.pages)
    b['bytes'] = pdfpath.stat().st_size
    b['outline_roots'] = roots
    b['outline_entries'] = len(flat)

    # 6) 链接注解可解析
    links = 0
    for page in pdf.pages:
        for ref in page.get('/Annots', []):
            a = ref.get_object()
            if '/Dest' in a:
                dest = a['/Dest']
                if isinstance(dest, list):
                    assert pdf.get_page_number(dest[0].get_object()) is not None
                else:
                    nd = pdf.named_destinations
                    assert dest in nd and pdf.get_destination_page_number(nd[dest]) is not None
                links += 1
    chk(f'{name}_links_valid', links >= len(hrefs), f'{links} 个链接注解')
    b['links'] = links
    res['books'][name] = b
    print(f'  == {name}: {b["pages"]} 页, {b["bytes"]//1024} KB, 书签 {b["outline_entries"]}')

(V3 / 'validation.json').write_text(
    json.dumps({'all_pass': ok, **res}, ensure_ascii=False, indent=2), encoding='utf-8')
print('ALL PASS' if ok else 'HAS FAILURES')
sys.exit(0 if ok else 1)
