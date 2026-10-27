"""Build the printable sprint booklet from its single Markdown source.

Run from the repository root. --render writes disposable page PNGs to _tmp.
The booklet source remains authoritative; this tool never changes it.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    CondPageBreak, Flowable, Paragraph, SimpleDocTemplate, Spacer,
    Table, TableStyle, PageBreak,
)

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '课程' / '复习资料'
SOURCE = BASE / '源稿' / '冲刺重点与代码背诵合集.md'
OUTPUT = BASE / '成品' / '冲刺重点与代码背诵合集.pdf'
TMP = ROOT / '_tmp' / 'sprint_collection'
MARGIN = 18 * mm
WIDTH = A4[0] - 2 * MARGIN - 12
CODE_SIZE = 9.4
CODE_LEADING = 14.0


def fonts():
    from reportlab.lib import textsplit
    from reportlab.platypus import paragraph
    for module in (textsplit, paragraph):
        module.ALL_CANNOT_START += '，；：？！'
    directory = Path('C:/Windows/Fonts')
    pdfmetrics.registerFont(TTFont('SprintSong', str(directory / 'simsun.ttc'), subfontIndex=0))
    pdfmetrics.registerFont(TTFont('SprintHei', str(directory / 'simhei.ttf')))
    pdfmetrics.registerFontFamily('SprintSong', normal='SprintSong', bold='SprintHei',
                                  italic='SprintSong', boldItalic='SprintHei')


def rich(text):
    # Local source links remain clickable in Markdown; the print copy shows labels.
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = html.escape(text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)


class Code(Flowable):
    def __init__(self, lines, continued=False):
        super().__init__()
        self.lines = list(lines)
        self.continued = continued
        self.spaceAfter = 9
        self.width = WIDTH
        self.height = len(self.lines) * CODE_LEADING + 16 + (13 if continued else 0)

    def wrap(self, available_width, available_height):
        self.width = min(WIDTH, available_width)
        for line in self.lines:
            if pdfmetrics.stringWidth(line, 'SprintSong', CODE_SIZE) > self.width - 18:
                raise ValueError('Code line too wide; wrap the source: ' + line)
        return self.width, self.height

    def split(self, available_width, available_height):
        capacity = int((available_height - 16 - (13 if self.continued else 0)) / CODE_LEADING)
        if capacity < 5:
            return []
        if capacity >= len(self.lines):
            return [self]
        # Do not strand a return statement and closing brace on the next page.
        capacity = min(capacity, len(self.lines) - 6)
        if capacity < 5:
            return []
        # Prefer a nearby function boundary; keep at least five lines together.
        candidates = [i for i in range(5, capacity + 1)
                      if not self.lines[i - 1].strip()]
        if candidates and candidates[-1] >= capacity - 7:
            capacity = candidates[-1]
        # Keep a function's short closing tail with some actual statements.
        # Otherwise a larger line spacing can leave only braces on the next page.
        for end in range(capacity, min(capacity + 4, len(self.lines))):
            if self.lines[end] == '}':
                capacity = max(5, min(capacity, end - 4))
                break
        while capacity > 5:
            before = self.lines[capacity - 1].strip()
            after = self.lines[capacity].strip()
            orphan_tail = after.startswith(('}', 'else', 'return ', 'break;', 'continue;'))
            detached_header = (before.endswith(('{', '(', '&&', '||', ','))
                               or before.startswith('//')
                               or bool(re.match(r'^(if|for|while)\b.*\)$', before)))
            if not (orphan_tail or detached_header):
                break
            capacity -= 1
        return [Code(self.lines[:capacity], self.continued),
                Code(self.lines[capacity:], True)]

    def draw(self):
        c = self.canv
        c.setFillColor(colors.HexColor('#F4F5F7'))
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        y = self.height - 8 - CODE_SIZE
        if self.continued:
            c.setFillColor(colors.HexColor('#526070'))
            c.setFont('SprintSong', 8)
            c.drawString(9, y, '代码续')
            y -= 13
        c.setFont('SprintSong', CODE_SIZE)
        c.setFillColor(colors.HexColor('#172334'))
        for line in self.lines:
            c.drawString(9, y, line)
            y -= CODE_LEADING


class Book(SimpleDocTemplate):
    def afterFlowable(self, item):
        if hasattr(item, 'bookmark'):
            name, title, level = item.bookmark
            self.canv.bookmarkPage(name)
            self.canv.addOutlineEntry(title, name, level=level, closed=False)


def blocks(text):
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith('<!--'):
            i += 1
            continue
        if line.startswith('```'):
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code.append(lines[i].rstrip())
                i += 1
            if i == len(lines):
                raise ValueError('Unclosed code fence')
            yield 'code', code
            i += 1
        elif line.startswith('#'):
            yield 'heading', (len(line) - len(line.lstrip('#')), line.lstrip('#').strip())
            i += 1
        elif line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                row = lines[i].strip()
                if not re.fullmatch(r'\|[ :|\-]+\|', row):
                    rows.append([x.strip() for x in re.split(r'(?<!\\)\|', row.strip('|'))])
                i += 1
            yield 'table', rows
        else:
            paragraph = [line.removeprefix('> ')]
            i += 1
            if not line.startswith(('-', '*')) and not re.match(r'\d+[.、]', line):
                while i < len(lines) and lines[i].strip() and not lines[i].startswith(('#', '|', '```', '- ', '> ', '<!--')):
                    paragraph.append(lines[i].strip())
                    i += 1
            yield 'paragraph', ' '.join(paragraph)


def build():
    fonts()
    text = SOURCE.read_text(encoding='utf-8-sig')
    cmap = pdfmetrics.getFont('SprintSong').face.charToGlyph
    missing = sorted({ch for ch in text if ord(ch) > 32 and ord(ch) not in cmap})
    if missing:
        raise ValueError(f'Unsupported print characters: {missing}')
    numbers = re.findall(r'^### (\d{2}) ', text, re.M)
    if numbers != [f'{i:02d}' for i in range(1, 24)]:
        raise ValueError('Code entries must be 01 through 23 in order')

    body = ParagraphStyle('Body', fontName='SprintSong', fontSize=10.3, leading=17.0,
                          wordWrap='CJK', spaceAfter=8, allowWidows=0, allowOrphans=0)
    title = ParagraphStyle('Title', parent=body, fontName='SprintHei', fontSize=20,
                           leading=28, spaceAfter=14)
    h2 = ParagraphStyle('H2', parent=body, fontName='SprintHei', fontSize=14,
                        leading=22, spaceBefore=12, spaceAfter=10, keepWithNext=True)
    h3 = ParagraphStyle('H3', parent=body, fontName='SprintHei', fontSize=12,
                        leading=18, spaceBefore=10, spaceAfter=8, keepWithNext=True)
    table_heading = ParagraphStyle('TableHeading', parent=h3, keepWithNext=False)
    h4 = ParagraphStyle('H4', parent=h3, fontSize=10.5, leading=16)
    cell = ParagraphStyle('Cell', parent=body, fontSize=9.3, leading=14.8, spaceAfter=0)
    story = []
    bookmark_counter = 0
    for kind, value in blocks(text):
        if kind == 'heading':
            level, heading = value
            if level == 2 and heading.startswith('二、'):
                story.append(PageBreak())
            elif level == 3:
                story.append(CondPageBreak(240 if re.match(r'\d{2} ', heading) else 140))
            style = {1: title, 2: h2, 3: h3}.get(level, h4)
            if level == 3 and not re.match(r'\d{2} ', heading):
                # Let long tables continue into the remaining space on this page.
                style = table_heading
            p = Paragraph(rich(heading), style)
            if level in (2, 3):
                bookmark_counter += 1
                p.bookmark = (f'part{bookmark_counter}', heading, level - 2)
            story.append(p)
        elif kind == 'paragraph':
            story.append(Paragraph(rich(value), body))
        elif kind == 'code':
            story.append(Code(value))
        elif kind == 'table':
            columns = len(value[0])
            if any(len(row) != columns for row in value):
                raise ValueError('Inconsistent table columns')
            # Frequency tables reserve room for the concrete knowledge items.
            weights = {3: [2.2, 1.9, 5.9], 4: [2.1, 1.4, 1.3, 5.2],
                       5: [1.8, 1, 1.1, 4.8, 1.3]}.get(columns, [1] * columns)
            widths = [WIDTH * w / sum(weights) for w in weights]
            t = Table([[Paragraph(rich(c), cell) for c in row] for row in value],
                      colWidths=widths, repeatRows=1, hAlign='LEFT')
            t.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EAF0F5')),
                ('LINEBELOW', (0, 0), (-1, 0), .6, colors.HexColor('#8093A6')),
                ('LINEBELOW', (0, 1), (-1, -1), .3, colors.HexColor('#CBD3DA')),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.extend([t, Spacer(1, 9)])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = Book(str(OUTPUT), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                    topMargin=16 * mm, bottomMargin=17 * mm,
                    title='重邮802冲刺重点与代码背诵合集', author='',
                    subject='近三年考点频率与23项代码复习', pageCompression=1)

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('SprintSong', 8.5)
        canvas.setFillColor(colors.HexColor('#647081'))
        canvas.drawString(MARGIN, 9 * mm, '重邮802数据结构  冲刺复习')
        canvas.drawRightString(A4[0] - MARGIN, 9 * mm, str(doc.page))
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    from pypdf import PdfReader
    pdf = PdfReader(OUTPUT)
    print(f'Built {len(pdf.pages)} pages; 23 code entries; source SHA256 '
          f'{hashlib.sha256(SOURCE.read_bytes()).hexdigest()}')
    return len(pdf.pages)


def render():
    import pypdfium2 as pdfium
    destination = TMP / 'pages'
    destination.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(str(OUTPUT))
    for index in range(len(pdf)):
        page = pdf[index]
        bitmap = page.render(scale=1.5)
        bitmap.to_pil().save(destination / f'page-{index+1:02d}.png')
        bitmap.close()
        page.close()
    pdf.close()
    print('Rendered pages to', destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--render', action='store_true')
    args = parser.parse_args()
    build()
    if args.render:
        render()
