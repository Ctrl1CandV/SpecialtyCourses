# -*- coding: utf-8 -*-
"""v3 顺序语义检查：回归（chapter-type 与改动前一致）+ 分区版（type-chapter）结构。"""
import re, pathlib

R = pathlib.Path('D:/Program Project/SpecialtyCourses')
BASE = R / '_tmp/pdf_v3/baseline_order'      # 改动前代码生成
REG = R / '_tmp/pdf_v3/regress_ct'           # 改动后默认模式
V3 = R / '_tmp/pdf_v3/build_ji'              # type-chapter
NAMES = [('精选题集', 401), ('补充题集', 553), ('答案册', 223)]
Q_RE = re.compile(r'<div class="q" id="q-([^"]+)" data-seq="(\d+)">')

def seqs(d, name):
    t = (d / f'{name}_优化版.html').read_text(encoding='utf-8')
    return [(i, int(s)) for i, s in Q_RE.findall(t)]

ok = True
for name, n in NAMES:
    b, r, v = (seqs(d, name) for d in (BASE, REG, V3))
    # 1) 回归：默认模式与改动前逐项一致
    same = (b == r)
    print(f'{name}: 回归一致={same}  基线{len(b)} 回归{len(r)} v3={len(v)}')
    ok &= same and len(b) == n and len(v) == n
    # 2) v3 集合一致（仅顺序不同）
    ok &= sorted(x[0] for x in b) == sorted(x[0] for x in v)
    # 3) v3 顺序确实不同（分区生效）
    if [x[0] for x in b] == [x[0] for x in v]:
        print(f'  !! {name} v3 顺序与章→题型完全相同？'); ok = False
for name, n in [('精选题集', 401), ('补充题集', 553)]:
    v = seqs(V3, name)
    cont = [s for _, s in v] == list(range(1, n + 1))
    print(f'{name}: v3 序号连续 1..{n} = {cont}')
    ok &= cont
# 4) 答案册复用精选册 v3 序号
jx = dict(seqs(V3, '精选题集')); ans = seqs(V3, '答案册')
mism = [(i, s, jx.get(i)) for i, s in ans if jx.get(i) != s]
print(f'答案册: 与精选册序号一致 = {not mism}（{len(ans)} 题）')
ok &= not mism
# 5) v3 分区结构：h1 题型 / h2 章 / 目录链接
for name, n in NAMES:
    t = (V3 / f'{name}_优化版.html').read_text(encoding='utf-8')
    parts = re.findall(r'<h1 class="qt" id="part-(\d+)">(.*?)<span class="cnt">(\d+) 题</span>', t)
    secs = re.findall(r'<h2 class="ch" id="sec-(\d+)">(.*?)<span class="cnt">(\d+) 题</span>', t)
    print(f'{name}: 题型区 {[(p[1][:3], p[2]) for p in parts]}')
    print(f'  章节数 {len(secs)}，节题数和 = {sum(int(s[2]) for s in secs)}（应 {n}）')
    ok &= sum(int(s[2]) for s in secs) == n
    ids = set(re.findall(r'id="(part-\d+|sec-\d+)"', t))
    hrefs = set(re.findall(r'href="#(part-\d+|sec-\d+)"', t))
    print(f'  目录锚点全部存在 = {hrefs <= ids}（{len(hrefs)} 链接）')
    ok &= hrefs <= ids
print('ALL OK' if ok else 'FAILED')
