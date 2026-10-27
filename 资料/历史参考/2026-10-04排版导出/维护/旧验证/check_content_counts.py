# -*- coding: utf-8 -*-
"""v3 与上一轮优化版 HTML 的勘误/图片/选项/考点行数量对比（内容机制未变的证据）。"""
import pathlib, re
R = pathlib.Path('D:/Program Project/SpecialtyCourses')
ok = True
for name in ['精选题集', '补充题集', '答案册']:
    base = (R / f'_tmp/pdf_build_optimized/{name}_优化版.html').read_text(encoding='utf-8')
    v3 = (R / f'_tmp/pdf_v3/build_ji/{name}_优化版.html').read_text(encoding='utf-8')
    row = {}
    for key, pat in [('errata', r'class="errata"'), ('img', r'<img '),
                     ('optline', r'class="optline"'), ('kd', r'class="kd"'),
                     ('figmiss', r'class="figmiss"'), ('note', r'class="note"'),
                     ('anslab', r'class="lab"')]:
        b, v = len(re.findall(pat, base)), len(re.findall(pat, v3))
        row[key] = (b, v, b == v)
        ok &= (b == v)
    print(name, row)
print('ALL SAME' if ok else 'DIFF FOUND')
