#!/usr/bin/env python3
"""Validate student-only exam JSON and produce editable Markdown and print PDFs.

Use the bundled Codex Python runtime with reportlab, pypdf and pypdfium2.
No answer data is read or emitted by this tool. All input is in 试题源稿.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '资料整理' / '六套模拟卷成稿'
SOURCE = OUT / '试题源稿'
PDF_DIR = OUT / '学生卷PDF'
MD_DIR = OUT / '可编辑试题'
QA_DIR = ROOT / '_tmp' / 'exam_production' / 'rendered'
FORMAT = json.loads((OUT/'题型规范.json').read_text(encoding='utf-8'))
SECTIONS = {key:(value['name'],value['count'],sum(value['points']))
            for key,value in FORMAT['sections'].items()}
def paper_profile(paper: int) -> str:
    return '保守卷' if paper <= 3 else '适度创新卷'

ALGORITHM_REQUEST = '请写出算法的基本思想、C语言实现，并分析时间复杂度和辅助空间复杂度。'
INTRO = [
    '满分150分　考试时间180分钟',
    '姓名：________________　准考证号：________________',
    '请在题后作答区填写答案；算法设计题另附续答页。各大题内的小题从1开始编号，作答时写明小题及空号。',
    '程序中的 __1__、__2__ 等为待填代码；请按空号作答，允许等价的正确表达式或语句。填空题直接写出所求结果。',
    '程序使用C或类C记法，可省略标准头文件。未特别说明时，数组下标从0开始，整数运算不溢出，辅助容器容量足够。算法设计题须写基本思想、C语言实现和时间、辅助空间复杂度。',
    '不使用计算器。各题独立，题内约定优先于本页统一约定。',
]


def load_paper(paper: int) -> dict:
    data = json.loads((SOURCE / f'第{paper}套.json').read_text(encoding='utf-8-sig'))
    # The print font lacks these mathematical glyphs. Use explicit equivalent
    # notation in both editable text and PDF; never emit an invisible operand.
    replacements = {'−': '-', '–': '-', '—': '-', '‑': '-', '∅': 'NULL', '₀': '_0', '₁': '_1', '₂': '_2',
                    'ᵢ': '_i', 'ₖ': '_k', 'ₙ': '_n', '\u00a0': ' ', '↔': '<->'}
    for q in data.get('questions', []):
        q['content'] = re.sub(r'⌊([^⌊⌋]+)⌋', r'floor(\1)', q['content'])
        for old, new in replacements.items():
            q['content'] = q['content'].replace(old, new)
    return data


def validate(data: dict) -> list[str]:
    errors = []
    paper = data.get('paper')
    rows = data.get('questions', [])
    if paper not in range(1, 7) or len(rows) != 24:
        errors.append(f'paper={paper}: expected 24 questions')
    ids = set()
    for section, (_, count, points) in SECTIONS.items():
        group = [q for q in rows if q.get('section') == section]
        if len(group) != count or sum(q.get('points', 0) for q in group) != points:
            errors.append(f'S{paper}-{section}: section count/points mismatch')
        if [q.get('number') for q in group] != list(range(1, count+1)):
            errors.append(f'S{paper}-{section}: numbering mismatch')
    for i, q in enumerate(rows):
        qid = q.get('id', '')
        section = q.get('section')
        expected_id = f'S{paper}-{section}{q.get("number", 0):02d}'
        if qid != expected_id or qid in ids:
            errors.append(qid + ': duplicate or invalid ID')
        ids.add(qid)
        point_list = FORMAT['sections'].get(section, {}).get('points', [])
        expected_points = point_list[q['number']-1] if q['number'] in range(1,len(point_list)+1) else None
        if q.get('points') != expected_points:
            errors.append(qid + ': invalid points')
        if set(q) - {'id','section','number','points','content'}:
            errors.append(qid + ': student source contains unexpected metadata fields')
        body = q.get('content', '')
        if not isinstance(body, str) or len(body.strip()) < 25:
            errors.append(qid + ': incomplete question')
            continue
        if re.search(r'参考答案|答案蓝图|正确选项[为是：:]|教师答案|【答案】|评分细则|来源ID|待补齐|选用原题|TODO', body):
            errors.append(qid + ': teacher material or placeholder in student text')
        if body.count('```') % 2:
            errors.append(qid + ': unclosed code block')
        if re.search(r'紧渐近|Θ|Theta', body):
            errors.append(qid + ': use the taught time-complexity notation instead of Theta')
        if paper <= 3 and re.search(r'Shell|希尔排序|基数排序|LSD', body, re.I):
            errors.append(qid + ': conservative paper contains an excluded low-frequency sorting task')
        if paper == 6 and section == 'I' and q['number'] in (2, 3, 4):
            all_blanks = set(re.findall(r'__(\d+)__', body))
            if len(all_blanks) > 3:
                errors.append(qid + ': paper 6 reading question exceeds three answer blanks')
        if section == 'II':
            if re.search(r'^[ABCD][.．、]\s*|单项选择|正确选项|下列选项', body, re.M):
                errors.append(qid + ': section II must not contain choices')
            if not re.search(r'_{3,}|__\d+__', body):
                errors.append(qid + ': fill-in question requires an explicit blank')
            if re.search(r'填写查找动作|分别填写.*操作|应.*采取.*操作|说明理由|解释原因', body):
                errors.append(qid + ': open-ended operation or explanation is not a fill-in task')
        parts = [int(x) for x in re.findall(r'[（(]\s*(\d+)\s*分\s*[）)]', body)]
        if section == 'IV':
            if parts or re.search(r'^[（(][1-9][）)]', body, re.M):
                errors.append(qid + ': algorithm task must not be split into scored subquestions')
            if ALGORITHM_REQUEST not in body:
                errors.append(qid + ': algorithm task requires the common idea/code/time/space request')
            if re.search(r'倒数第\s*[kK]|倒数第.*个', body):
                errors.append(qid + ': excluded classic kth-from-end task')
        elif sum(parts) != q['points']:
            errors.append(qid + f': subquestion points {parts} != {q["points"]}')
        if section == 'III' and re.search(r'简述|解释.*原因|说明.*原因|为何|为什么|证明', body):
            errors.append(qid + ': application task contains an explanatory or proof request')
        if section == 'I' and '```' not in body:
            errors.append(qid + ': reading question missing code')
        if section == 'I' and q['number'] > 1:
            code = '\n'.join(re.findall(r'```[^\n]*\n(.*?)```', body, re.S))
            blanks = sorted(set(int(x) for x in re.findall(r'__(\d+)__', code)))
            if len(blanks) < 2 or blanks != list(range(1, len(blanks)+1)):
                errors.append(qid + ': code completion needs consecutive numbered blanks')
    complexity_fill = sum(bool(re.search(r'时间复杂度|空间复杂度', q['content']))
                          for q in rows if q.get('section') == 'II')
    if complexity_fill > (0 if paper in (1,2,3) else 1):
        errors.append(f'S{paper}-II: complexity fill-in exceeds the paper profile limit')
    return errors


def markdown(data: dict) -> str:
    from exam_figures import load_specs
    figure_specs=load_specs()
    paper = data['paper']
    lines = [f'# 2027考研重邮802数据结构模拟试卷 第{paper}套 {paper_profile(paper)}', '']
    for s in INTRO:
        lines += [s, '']
    current = None
    for index, q in enumerate(data['questions'], 1):
        if q['section'] != current:
            current = q['section']
            title, count, points = SECTIONS[current]
            lines += [f'## {title}（共{count}题，{points}分）', '']
        body=q['content'].strip()
        if q['id'] in figure_specs:
            spec=figure_specs[q['id']]
            body=body.replace('（1）',f'![{spec["caption"]}](../配图/{q["id"]}.png)\n\n（1）',1)
        lines += [f'### {q["number"]}（{q["points"]}分）', '', body, '']
        if q['section'] in {'I', 'III', 'IV'}:
            lines += ['作答区：', '', '<br>\n' * (4 if q['section']=='I' else 10), '']
        if q['section'] == 'IV':
            lines += [f'#### 第{q["number"]}题续答区（代码与分析）', '', '<br>\n'*24, '']
    return '\n'.join(lines)


def split_blocks(body: str):
    """Small predictable Markdown subset: paragraphs, fenced code and tables."""
    lines = body.strip().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('```'):
            i += 1
            block = []
            while i < len(lines) and not lines[i].strip().startswith('```'):
                block.append(lines[i].rstrip())
                i += 1
            yield 'code', '\n'.join(block)
            i += 1
        elif line.startswith('|') and i+1 < len(lines) and re.match(r'^\|[\s:|-]+\|$', lines[i+1].strip()):
            block = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                entry = lines[i].strip()
                if not re.match(r'^\|[\s:|-]+\|$', entry):
                    block.append([x.strip().replace(r'\|','|') for x in re.split(r'(?<!\\)\|',entry.strip('|'))])
                i += 1
            yield 'table', block
        else:
            block = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(('```','|')):
                if re.match(r'^(?:[ABCD][.．、]|[（(]\d+[）)]|\d+[.．])', lines[i].strip()):
                    break
                block.append(lines[i].strip())
                i += 1
            yield 'paragraph', ' '.join(block)


def rich(text: str) -> str:
    value = html.escape(text)
    value = re.sub(r'`([^`]+)`', lambda m: m.group(1), value)
    value = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', value)
    # Fill-in scores can occur anywhere in a line, not only at paragraph end.
    value = re.sub(r'([（(]\d+分[）)])', r'<nobr>\1</nobr>', value)
    return value


def scored_paragraph_text(text: str, max_width: float, font: str, size: float) -> str:
    """Wrap scores with their blanks; ReportLab CJK ignores the nobr attribute.

    Only used for scored prose, never code. Explicit line breaks preserve small
    answer/score units while the normal paragraph renderer handles the glyphs.
    """
    from reportlab.pdfbase.pdfmetrics import stringWidth
    plain = text.replace('`', '').replace('**', '')
    atom = (r'__\d+__(?:\s*[\u4e00-\u9fff]{0,5})?\s*[（(]\d+分[）)]'
            r'|[（(]\d+分[）)]|[A-Za-z0-9_]+| +|.')
    units = []
    opening = ''
    for token in re.findall(atom, plain):
        if token in '（([{':
            opening += token
            continue
        if opening:
            token = opening + token
            opening = ''
        if units and (token in '，。、；：？！）)]}' or re.fullmatch(r'[（(]\d+分[）)]', token)):
            units[-1] += token
        else:
            units.append(token)
    if opening:
        units.append(opening)
    lines, line = [], ''
    for token in units:
        if line and stringWidth(line+token, font, size) > max_width:
            lines.append(line.rstrip())
            line = token.lstrip()
        else:
            line += token
    if line:
        lines.append(line.rstrip())
    return '<br/>'.join(rich(line) for line in lines)


def init_pdf():
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase import pdfmetrics
    from reportlab.lib import textsplit
    from reportlab.platypus import paragraph
    # ReportLab's default kinsoku list omits common Chinese fullwidth marks.
    # Let one closing mark hang at the preceding line's edge instead of
    # starting the next line with punctuation.
    for module in (textsplit, paragraph):
        module.ALL_CANNOT_START += '，；：？！'
    font_dir = Path('C:/Windows/Fonts')
    pdfmetrics.registerFont(TTFont('ExamSong', str(font_dir/'simsun.ttc'), subfontIndex=0))
    pdfmetrics.registerFont(TTFont('ExamHei', str(font_dir/'simhei.ttf')))
    pdfmetrics.registerFontFamily('ExamSong', normal='ExamSong', bold='ExamHei', italic='ExamSong', boldItalic='ExamHei')


def check_font_coverage(datasets):
    from reportlab.pdfbase import pdfmetrics
    cmap = pdfmetrics.getFont('ExamSong').face.charToGlyph
    for data in datasets:
        for q in data['questions']:
            missing = sorted({c for c in q['content'] if ord(c) > 32 and ord(c) not in cmap})
            if missing:
                raise ValueError(f'{q["id"]}: unsupported print glyphs: {missing}')


def build_pdf(data: dict, target: Path):
    from exam_figures import load_specs, drawing
    figure_specs=load_specs()
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, XPreformatted, Flowable

    class CodeBlock(XPreformatted):
        def split(self, available_width, available_height):
            return []

    answer_spaces = []
    question_pages = {}
    class QuestionStart(Flowable):
        def __init__(self,qid):
            Flowable.__init__(self)
            self.qid=qid
            self.width=self.height=0
        def draw(self):
            question_pages[self.qid]=self.canv.getPageNumber()
    class AnswerSpace(Flowable):
        """Reserve writing space and record the actual usable page remainder."""
        def __init__(self, qid, height_mm, continuation=False):
            Flowable.__init__(self)
            self.qid = qid
            self.width = width-12
            self.height = height_mm*mm
            self.continuation = continuation

        def draw(self):
            top = self.canv._currentMatrix[5] + self.height
            usable = top - (17*mm+6)
            answer_spaces.append({'id':self.qid,'page':self.canv.getPageNumber(),
                                  'continuation':self.continuation,
                                  'writing_height_mm':round(usable/mm,1)})
            if self.continuation:
                self.canv.setStrokeColor(colors.HexColor('#E1E1E1'))
                self.canv.setLineWidth(0.3)
                for line in range(1, int(self.height/(8*mm))+1):
                    y = self.height-line*8*mm
                    self.canv.line(0,y,self.width,y)

    paper = data['paper']
    margin = 19*mm
    width = A4[0]-2*margin
    body_style = ParagraphStyle('Body', fontName='ExamSong', fontSize=10.5, leading=15,
                                spaceAfter=5, wordWrap='CJK', allowWidows=0, allowOrphans=0)
    section_style = ParagraphStyle('Section', parent=body_style, fontName='ExamHei', fontSize=12.5,
                                   leading=19, spaceBefore=6, spaceAfter=10, keepWithNext=True)
    number_style = ParagraphStyle('Number', parent=body_style, fontName='ExamHei', spaceBefore=8, spaceAfter=4, keepWithNext=True)
    title_style = ParagraphStyle('Title', parent=body_style, fontName='ExamHei', fontSize=17, leading=23, alignment=TA_CENTER, spaceAfter=7)
    info_style = ParagraphStyle('Info', parent=body_style, fontSize=10, leading=14, spaceAfter=4)
    answer_style = ParagraphStyle('AnswerLabel', parent=body_style, fontSize=9, leading=13,
                                  textColor=colors.HexColor('#666666'), spaceBefore=9, spaceAfter=8)
    code_style = ParagraphStyle('Code', fontName='ExamSong', fontSize=9.5, leading=12.5, leftIndent=8, spaceBefore=4, spaceAfter=7)
    cell_style = ParagraphStyle('Cell', parent=body_style, fontSize=10, leading=14, alignment=TA_CENTER, spaceAfter=0)
    doc = SimpleDocTemplate(str(target), pagesize=A4, rightMargin=margin, leftMargin=margin,
                            topMargin=18*mm, bottomMargin=17*mm,
                            title=f'2027考研重邮802数据结构模拟试卷 第{paper}套', author='', subject='学生试卷')
    story = [Paragraph('2027考研重邮802数据结构模拟试卷', title_style),
             Paragraph(f'第{paper}套　{paper_profile(paper)}', ParagraphStyle('PaperNo', parent=title_style, fontSize=14, leading=20))]
    for line in INTRO:
        story.append(Paragraph(rich(line), info_style))
    story.append(Spacer(1,5))
    current = None
    for index, q in enumerate(data['questions'], 1):
        group = []
        # Explicit pages make writing space reliable instead of incidental gaps
        # caused by moving a whole question to the next page.
        if index > 1 and (q['section'] in {'I','III','IV'} or
                          (q['section']=='II' and q['number'] in {1,6})):
            story.append(PageBreak())
        if q['section'] != current:
            current = q['section']
            title, count, points = SECTIONS[current]
            group.append(Paragraph(f'{title}（共{count}题，{points}分）', section_style))
        elif q['section'] in {'I','III','IV'} or (q['section']=='II' and q['number']==6):
            group.append(Paragraph(f'{SECTIONS[current][0]}（续）',section_style))
        group.append(QuestionStart(q['id']))
        group.append(Paragraph(f'{q["number"]}．（{q["points"]}分）', number_style))
        figure_added=False
        for kind, value in split_blocks(q['content']):
            if kind == 'paragraph':
                if q['id'] in figure_specs and not figure_added and re.match(r'^[（(]1[）)]',value):
                    spec=figure_specs[q['id']]
                    fig=drawing(spec)
                    scale=min(1,(width-12)/fig.width,165/fig.height)
                    fig.scale(scale,scale);fig.width*=scale;fig.height*=scale
                    fig.hAlign='CENTER'
                    group.extend([Spacer(1,5),fig,Paragraph(rich(spec['caption']),ParagraphStyle('FigureCaption',parent=body_style,fontSize=8.5,leading=12,alignment=TA_CENTER)),Spacer(1,5)])
                    figure_added=True
                # Put points beside the subquestion number, avoiding CJK line
                # breaking inside a trailing score at the right margin.
                match = re.match(r'^([（(]\d+[）)])\s*(.*?)\s*([（(]\d+分[）)])$', value)
                if match:
                    value = f'{match[1]}{match[3]} {match[2]}'
                rendered = (scored_paragraph_text(value, width-12.5, body_style.fontName, body_style.fontSize)
                            if re.search(r'[（(]\d+分[）)]', value) else rich(value))
                group.append(Paragraph(rendered, body_style))
            elif kind == 'code':
                # Protect code syntax and indent; never silently reflow a C line.
                from reportlab.pdfbase.pdfmetrics import stringWidth
                lines = value.splitlines()
                max_width = max((stringWidth(x, 'ExamSong', code_style.fontSize) for x in lines), default=0)
                if max_width > width-12:
                    raise ValueError(f'{q["id"]}: code line is too wide ({max_width:.1f} pt); wrap source explicitly')
                group.append(CodeBlock(html.escape(value), code_style))
            else:
                if not value or any(len(row) != len(value[0]) for row in value):
                    raise ValueError(q['id'] + ': malformed Markdown table')
                weights = [max(len(re.sub(r'`','',r[c])) for r in value) for c in range(len(value[0]))]
                weights = [max(4,min(24,x)) for x in weights]
                widths = [width*w/sum(weights) for w in weights]
                tbl = Table([[Paragraph(rich(c), cell_style) for c in row] for row in value], colWidths=widths, repeatRows=1, hAlign='LEFT')
                tbl.setStyle(TableStyle([
                    ('GRID',(0,0),(-1,-1),0.45,colors.HexColor('#D9D9D9')),
                    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EEEEEE')),
                    ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                    ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
                    ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
                ]))
                group.extend([tbl,Spacer(1,7)])
        if q['section'] in {'I','III','IV'}:
            label = '作答区（请标明空号）' if q['section']=='I' else '作答区'
            group.append(Paragraph(label,answer_style))
            minimum_mm = {'I':20,'III':85,'IV':30}[q['section']]
            group.append(AnswerSpace(q['id'],minimum_mm))
        else:
            group.append(Spacer(1,8*mm))
        # Keep a question and its subparts together, and attach a section title
        # to its first question. Avoid nested KeepTogether: its synthetic height
        # can otherwise create a nearly empty page before a code question.
        story.append(KeepTogether(group))
        if q['section']=='IV':
            story.append(PageBreak())
            story.append(Paragraph(f'四、算法设计与分析题　第{q["number"]}题续答',section_style))
            story.append(Paragraph('代码与分析作答区',answer_style))
            story.append(AnswerSpace(q['id'],230,continuation=True))
    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont('ExamSong', 9)
        canvas.drawString(margin, 9*mm, f'重邮802数据结构模拟试卷  第{paper}套  {paper_profile(paper)}')
        canvas.drawRightString(A4[0]-margin, 9*mm, f'第{document.page}页')
        canvas.restoreState()
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    for item in answer_spaces:
        section = item['id'].split('-')[1].rstrip('0123456789')
        minimum = 225 if item['continuation'] else {'I':20,'III':85,'IV':30}[section]
        if item['writing_height_mm'] < minimum-1:
            raise ValueError(f'{item["id"]}: insufficient writing area: {item}')
        if not item['continuation'] and item['page']!=question_pages[item['id']]:
            raise ValueError(f'{item["id"]}: question and primary writing area separated')
    return answer_spaces, question_pages


def render_pdf(target: Path):
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(target))
    dest = QA_DIR / target.stem
    dest.mkdir(parents=True, exist_ok=True)
    for i in range(len(doc)):
        page = doc[i]
        bitmap = page.render(scale=1.5)
        bitmap.to_pil().save(dest/f'page-{i+1:02d}.png')
        bitmap.close()
        page.close()
    count = len(doc)
    doc.close()
    for old_page in dest.glob('page-*.png'):
        if int(old_page.stem.split('-')[-1]) > count:
            old_page.unlink()
    return count


def merge_all():
    from pypdf import PdfReader, PdfWriter
    writer = PdfWriter()
    for paper in range(1,7):
        path = PDF_DIR/f'重邮802模拟试卷第{paper}套.pdf'
        writer.append(PdfReader(path), outline_item=f'第{paper}套 {paper_profile(paper)}')
    target = OUT/'六套模拟试卷合订本.pdf'
    writer.add_metadata({'/Title':'2027考研重邮802数据结构六套模拟试卷','/Author':''})
    with target.open('wb') as f:
        writer.write(f)
    writer.close()


def format_self_test(datasets):
    """Guard against the concrete format errors found in the first delivery."""
    from copy import deepcopy
    good = deepcopy(datasets[0])
    if validate(good):
        raise SystemExit('Self-test needs a valid current student paper')
    bad = deepcopy(good)
    q = next(q for q in bad['questions'] if q['section'] == 'II')
    q['content'] += '\nA. 一\nB. 二\nC. 三\nD. 四'
    if not any('must not contain choices' in e for e in validate(bad)):
        raise SystemExit('Self-test failed to reject choices')
    bad = deepcopy(good)
    q = next(q for q in bad['questions'] if q['section'] == 'II')
    q['content'] = re.sub(r'_{3,}|__\d+__', '作答位置被误删', q['content'])
    if not any('requires an explicit blank' in e for e in validate(bad)):
        raise SystemExit('Self-test failed to reject a missing fill-in blank')
    bad = deepcopy(good)
    q = next(q for q in bad['questions'] if q['section'] == 'I' and q['number'] == 2)
    q['content'] = re.sub(r'__\d+__', 'completed_expression', q['content'])
    if not any('code completion needs' in e for e in validate(bad)):
        raise SystemExit('Self-test failed to reject completed code in a completion slot')
    bad = deepcopy(good)
    bad['questions'][0]['points'] = 4
    if not any('invalid points' in e for e in validate(bad)):
        raise SystemExit('Self-test failed to reject incorrect question points')
    bad = deepcopy(good)
    q = next(q for q in bad['questions'] if q['section'] == 'IV')
    q['content'] += '\n（1）说明指针间距。（2分）'
    if not any('must not be split' in e for e in validate(bad)):
        raise SystemExit('Self-test failed to reject segmented algorithm questions')
    bad = deepcopy(good)
    q = next(q for q in bad['questions'] if q['section'] == 'III')
    q['content'] += '\n简述选择这种方法的原因。'
    if not any('explanatory or proof' in e for e in validate(bad)):
        raise SystemExit('Self-test failed to reject application explanation requests')
    bad = deepcopy(good)
    bad['questions'][0]['content'] += '\n时间使用紧渐近界Θ表示。'
    if not any('instead of Theta' in e for e in validate(bad)):
        raise SystemExit('Self-test failed to reject untaught Theta terminology')
    bad = deepcopy(good)
    bad['paper'] = 1
    bad['questions'][0]['content'] += '\n采用Shell排序。'
    if not any('excluded low-frequency sorting' in e for e in validate(bad)):
        raise SystemExit('Self-test failed to reject conservative Shell sorting')
    print('PASS format regression: points, choices, blanks, algorithm form, explanation requests, untaught notation and conservative sorting policy')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--papers', nargs='+', type=int, default=list(range(1,7)))
    args = parser.parse_args()
    datasets = [load_paper(p) for p in args.papers]
    errors = [e for data in datasets for e in validate(data)]
    if errors:
        raise SystemExit('\n'.join(errors))
    if args.self_test:
        format_self_test(datasets)
        return
    if args.build:
        PDF_DIR.mkdir(parents=True, exist_ok=True)
        MD_DIR.mkdir(parents=True, exist_ok=True)
        init_pdf()
        from exam_figures import export_figures
        export_figures()
        check_font_coverage(datasets)
    reports = []
    from pypdf import PdfReader
    for data in datasets:
        p = data['paper']
        target = PDF_DIR/f'重邮802模拟试卷第{p}套.pdf'
        if args.build:
            (MD_DIR/f'第{p}套试卷.md').write_text(markdown(data), encoding='utf-8')
            answer_spaces,question_pages = build_pdf(data, target)
        count = None
        if target.exists():
            pdf = PdfReader(target)
            count = len(pdf.pages)
            text = '\n'.join(page.extract_text() or '' for page in pdf.pages)
            if re.search('参考答案|答案蓝图|教师答案|评分细则|正确选项[为是：:]', text):
                raise SystemExit(f'Paper {p}: teacher content in PDF')
            printed = [int(x) for x in re.findall(r'(?m)^(\d+)[．.]\s*[（(]\d+分', text)]
            expected = [q['number'] for q in data['questions']]
            if printed != expected:
                raise SystemExit(f'Paper {p}: section-local question numbering mismatch: {printed}')
            for section_title, _, _ in SECTIONS.values():
                if section_title not in text:
                    raise SystemExit(f'Paper {p}: section heading missing: {section_title}')
            if re.search(r'单项选择|^[ABCD][.．、]\s*', text, re.M):
                raise SystemExit(f'Paper {p}: obsolete choice format in PDF')
            if args.render:
                render_pdf(target)
        reports.append({'paper':p,'version':data['version'],'questions':24,'points':150,'pages':count,
                        'sections':{s:{'name':v[0],'questions':v[1],'points':v[2]} for s,v in SECTIONS.items()},
                        'numbering':'各大题内独立编号',
                        'source_sha256':hashlib.sha256((SOURCE/f'第{p}套.json').read_bytes()).hexdigest()})
        if args.build:
            reports[-1]['answer_spaces']=answer_spaces
            reports[-1]['question_pages']=question_pages
        print(f'PASS paper {p}: 24 questions, 150 points, {count} PDF pages')
    if args.build and sorted(args.papers) == list(range(1,7)):
        merge_all()
    if args.build:
        (OUT/'成卷结构核对.json').write_text(json.dumps({'papers':reports,'说明':'检查固定题数分值、代码留空、第二部分填空格式、独立编号与无答案标记；不自动证明填空答案唯一、数学结论正确或难度实测合格。'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
