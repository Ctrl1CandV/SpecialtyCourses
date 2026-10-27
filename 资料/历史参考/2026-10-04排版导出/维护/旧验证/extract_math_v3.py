# -*- coding: utf-8 -*-
"""从 v3 三册 HTML 抽取公式 span（口径与上一轮 content_check.py 一致），写 math_nodes_v3.json。"""
from pathlib import Path
from bs4 import BeautifulSoup
import json, re

R = Path('D:/Program Project/SpecialtyCourses')
maths = {}
for name in ['精选题集', '补充题集', '答案册']:
    soup = BeautifulSoup((R / f'_tmp/pdf_v3/build_ji/{name}_优化版.html').read_text(encoding='utf-8'), 'html.parser')
    spans = []
    for node in soup.find_all(string=True):
        if node.find_parent(['script', 'style', 'pre', 'code']):
            continue
        spans += [m.group(1) if m.group(1) is not None else m.group(2)
                  for m in re.finditer(r'\$\$(.+?)\$\$|\$([^$\n]+?)\$', str(node), re.S)]
    maths[name + '_v3'] = spans
    print(name, len(spans), 'spans')
(R / '_tmp/pdf_v3/math_nodes_v3.json').write_text(json.dumps(maths, ensure_ascii=False), encoding='utf-8')
