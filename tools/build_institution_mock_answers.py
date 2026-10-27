"""Build the three 2026 institution mock-paper answer PDFs from editable sources."""
from pathlib import Path
import argparse
import hashlib
import html
import json
import re

from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                              Table, TableStyle, XPreformatted, KeepTogether)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
from reportlab.graphics.shapes import Drawing, Line, Rect, String, Polygon
from build_prediction_answers import figure as standard_figure, rich

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '试卷/2026机构押题'
FIGURES = OUT / '源稿/模拟卷配图源稿.json'


def source_path(number):
    return OUT / '源稿/可编辑答案' / f'模拟卷{number}参考答案.md'


def fingerprint(number):
    payload = source_path(number).read_bytes() + FIGURES.read_bytes()
    payload += Path(__file__).read_bytes()
    return hashlib.sha256(payload).hexdigest()


def linked_cases(spec):
    """Show independent operations on the same physical list, including pointers."""
    d = Drawing(465, 395)
    ink = HexColor('#263544')
    xs = [61 + 51 * i for i in range(8)]
    for row, case in enumerate(spec['cases']):
        y = 360 - row * 46
        d.add(String(3, y - 3, case['name'], fontName='Song', fontSize=9))
        for j, value in enumerate(case['values']):
            x = xs[j]
            if value == '...':
                d.add(String(x, y - 3, '...', fontName='Song', fontSize=10,
                             textAnchor='middle'))
            else:
                d.add(Rect(x - 16, y - 10, 32, 20, fillColor=white, strokeColor=ink))
                d.add(String(x, y - 3, str(value), fontName='Song', fontSize=10,
                             textAnchor='middle'))
            if j < 7:
                a, b = x + 17, xs[j + 1] - 17
                d.add(Line(a, y, b, y, strokeColor=ink))
                d.add(Polygon([b, y, b - 4, y + 2, b - 4, y - 2],
                              fillColor=ink, strokeColor=ink))
        li = case.get('L', 0)
        d.add(String(xs[li], y + 16, 'L', fontName='Song', fontSize=9,
                     textAnchor='middle'))
        d.add(Line(xs[li], y + 14, xs[li], y + 11, strokeColor=ink))
        for j, label in [(1, 'P'), (2, 'Q'), (3, 'R'), (4, 'S')]:
            d.add(String(xs[j], y - 21, label, fontName='Song', fontSize=8,
                         textAnchor='middle'))
        if case.get('T'):
            d.add(String(462, y - 21, case['T'], fontName='Song', fontSize=8,
                         textAnchor='end'))
    return d


def kmp_picture(spec):
    d = Drawing(465, 215)
    t, p = spec['text'], spec['pattern']
    cell, x0 = 21, 38
    ink = HexColor('#263544')
    for j, char in enumerate(t):
        x = x0 + j * cell
        d.add(String(x + cell / 2, 198, str(j + 1), fontName='Song',
                     fontSize=7, textAnchor='middle'))
        d.add(Rect(x, 170, cell, 22, fillColor=HexColor('#eeeeee'), strokeColor=ink))
        d.add(String(x + cell / 2, 177, char, fontName='Song', fontSize=11,
                     textAnchor='middle'))
    d.add(String(3, 177, '主串', fontName='Song', fontSize=9))
    for r, attempt in enumerate(spec['alignments']):
        y = 132 - r * 34
        d.add(String(3, y + 7, f'第{r + 1}趟', fontName='Song', fontSize=8))
        for j, char in enumerate(p):
            x = x0 + (attempt['start'] - 1 + j) * cell
            color = white
            if j < attempt['matched']:
                color = HexColor('#e3f1e3')
            elif 'mismatch' in attempt and j == attempt['mismatch'][1] - 1:
                color = HexColor('#f7dddd')
            d.add(Rect(x, y, cell, 22, fillColor=color, strokeColor=ink))
            d.add(String(x + cell / 2, y + 7, char, fontName='Song', fontSize=11,
                         textAnchor='middle'))
    return d


def figure(spec):
    if spec.get('kind') == 'linked_cases':
        return linked_cases(spec)
    if spec.get('kind') == 'kmp':
        return kmp_picture(spec)
    return standard_figure(spec)


def build(number):
    source = source_path(number)
    md = source.read_text(encoding='utf-8')
    specs = json.loads(FIGURES.read_text(encoding='utf-8'))
    assert len(re.findall(r'^### ', md, re.M)) == 23
    assert not re.search(r'TODO|待补齐|PLACEHOLDER', md)
    cmap = pdfmetrics.getFont('Song').face.charToGlyph
    missing = sorted({c for c in md if ord(c) > 32 and ord(c) not in cmap})
    if missing:
        raise ValueError(f'Unsupported glyphs: {missing}')
    body = ParagraphStyle('body', fontName='Song', fontSize=10.5, leading=15.5,
                          wordWrap='CJK', spaceAfter=7, allowWidows=0, allowOrphans=0)
    title = ParagraphStyle('title', parent=body, fontName='Hei', fontSize=16,
                           leading=24, alignment=1, spaceAfter=12)
    sec = ParagraphStyle('section', parent=body, fontName='Hei', fontSize=12.5,
                         leading=19, spaceAfter=10, keepWithNext=True)
    question_style = ParagraphStyle('question', parent=body, fontName='Hei',
                                    spaceBefore=7, spaceAfter=7, keepWithNext=True)
    cell_style = ParagraphStyle('cell', parent=body, fontSize=9.3, leading=13,
                                spaceAfter=0)
    caption = ParagraphStyle('caption', parent=body, fontSize=9, leading=13,
                             alignment=1)
    width = A4[0] - 38 * 72 / 25.4 - 12
    story, lines = [], md.splitlines()
    i = 0
    section, count = '', 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line:
            continue
        if line == '<!--pagebreak-->':
            story.append(PageBreak())
        elif line.startswith('# '):
            story.append(Paragraph(rich(line[2:]), title))
        elif line.startswith('## '):
            if section:
                story.append(PageBreak())
            section, count = line[3:], 0
            story.append(Paragraph(rich(section), sec))
        elif line.startswith('### '):
            if count and section.startswith(('三', '四')):
                story.append(PageBreak())
            count += 1
            story.append(Paragraph(rich(line[4:]), question_style))
        elif line.startswith('{{FIG:'):
            spec = specs[line[6:-2]]
            story.append(KeepTogether([figure(spec),
                Paragraph(rich(spec.get('caption', '')), caption), Spacer(1, 8)]))
        elif line.startswith('```'):
            rows = []
            while i < len(lines) and not lines[i].strip().startswith('```'):
                rows.append(lines[i]); i += 1
            i += 1
            max_width = max((pdfmetrics.stringWidth(x, 'Song', 9) for x in rows), default=1)
            size = min(9, 9 * width / max(max_width, 1))
            if size < 7.8:
                raise ValueError(f'Wrap long code line in {source}: {max_width}')
            code_style = ParagraphStyle('code', fontName='Song', fontSize=size,
                                         leading=size + 2.5, spaceAfter=9)
            story.append(XPreformatted(html.escape('\n'.join(rows)), code_style))
        elif line.startswith('|'):
            rows = []
            while True:
                if not re.match(r'^\|[\s:|\-]+\|$', line):
                    inside = line[1:-1] if line.endswith('|') else line[1:]
                    rows.append([x.strip() for x in re.split(r'(?<!\\)\|', inside)])
                if i >= len(lines) or not lines[i].strip().startswith('|'):
                    break
                line = lines[i].strip(); i += 1
            assert all(len(r) == len(rows[0]) for r in rows), rows
            weights = [max(3, min(36, max(len(r[j]) for r in rows)))
                       for j in range(len(rows[0]))]
            table = Table([[Paragraph(rich(c.replace('\\|', '|')), cell_style) for c in row]
                           for row in rows],
                          colWidths=[width * w / sum(weights) for w in weights],
                          repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), .4, HexColor('#b5b5b5')),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#eeeeee')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
            story.extend([table, Spacer(1, 8)])
        else:
            chunks = [line]
            while (i < len(lines) and lines[i].strip()
                   and not lines[i].strip().startswith(('#', '|', '```', '{{', '<!--'))):
                chunks.append(lines[i].strip()); i += 1
            story.append(Paragraph(rich(' '.join(chunks)), body))
    target = OUT / '成品' / f'模拟卷{number}参考答案.pdf'

    def footer(canvas, doc):
        canvas.saveState(); canvas.setFont('Song', 8)
        canvas.drawString(19 * 72 / 25.4, 24, f'重邮802数据结构 模拟卷{number} 参考答案')
        canvas.drawRightString(A4[0] - 19 * 72 / 25.4, 24, f'第{doc.page}页')
        canvas.restoreState()

    doc = SimpleDocTemplate(str(target), pagesize=A4,
        leftMargin=19 * 72 / 25.4, rightMargin=19 * 72 / 25.4,
        topMargin=18 * 72 / 25.4, bottomMargin=18 * 72 / 25.4,
        title=f'重邮802模拟卷{number}参考答案', author='',
        subject='source-sha256:' + fingerprint(number))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(target)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('paper', choices=['一', '二', '三'])
    build(parser.parse_args().paper)
