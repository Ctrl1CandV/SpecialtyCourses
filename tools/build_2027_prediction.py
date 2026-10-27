"""Build the 2027 prediction papers, answer keys and recording notes.

Authoritative sources are JSON files in 试卷/2027押题卷/源稿.
Student PDFs read only content and figures, never answer/guide/basis fields.
Temporary renders belong to _tmp/revision_2027/rendered. Existing exams are untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    XPreformatted, KeepTogether, CondPageBreak, Flowable,
)
from reportlab.graphics.shapes import Drawing, Circle, Line, String, Polygon, Rect

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '试卷/2027押题卷'
TEMP = ROOT / '_tmp/revision_2027/rendered'
WIDTH = A4[0] - 38 * mm - 12
SECTIONS = {'I': ('一、程序阅读题', [6, 6, 4, 4]),
            'II': ('二、填空题', [3] * 10),
            'III': ('三、综合应用题', [10] * 7),
            'IV': ('四、算法设计与分析题', [8, 10, 12])}


def normalize(value):
    supers = dict(zip('⁰¹²³⁴⁵⁶⁷⁸⁹ᵈ⁽⁾', '0123456789d()'))
    value = re.sub(r'⁽([^⁽⁾]*)⁾',
                   lambda m: '^('+''.join(supers.get(c,c) for c in m[1])+')', value)
    value = re.sub('[⁰¹²³⁴⁵⁶⁷⁸⁹ᵈ⁽⁾]+',
                   lambda m: '^'+''.join(supers[c] for c in m[0]), value)
    subs = dict(zip('₀₁₂₃₄₅₆₇₈₉', '0123456789'))
    value = re.sub('[₀₁₂₃₄₅₆₇₈₉]+',
                   lambda m: '_'+''.join(subs[c] for c in m[0]), value)
    for a, b in {'−':'-', '∅':'空', '↔':'<->', '⋯':'...', '–':'—',
                 '₀':'_0', '₁':'_1', '₂':'_2', '₃':'_3', 'ᵢ':'_i',
                 '⁰':'^0', '¹':'^1', '²':'^2', '³':'^3'}.items():
        value = value.replace(a, b)
    value = re.sub(r'⌊([^⌊⌋]+)⌋', r'floor(\1)', value)
    return re.sub(r'⌈([^⌈⌉]+)⌉', r'ceil(\1)', value)


def rich(value):
    value = html.escape(normalize(value))
    value = re.sub(r'`([^`]+)`', r'\1', value)
    value = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', value)
    return value.replace('\n', '<br/>')


def init():
    pdfmetrics.registerFont(TTFont('PredSong', 'C:/Windows/Fonts/simsun.ttc', subfontIndex=0))
    pdfmetrics.registerFont(TTFont('PredHei', 'C:/Windows/Fonts/simhei.ttf'))
    pdfmetrics.registerFontFamily('PredSong', normal='PredSong', bold='PredHei',
                                italic='PredSong', boldItalic='PredHei')


def styles():
    body = ParagraphStyle('body', fontName='PredSong', fontSize=10.5, leading=16,
                          wordWrap='CJK', spaceAfter=7, allowWidows=0, allowOrphans=0)
    return {
        'body': body,
        'title': ParagraphStyle('title', parent=body, fontName='PredHei', fontSize=16,
                                leading=24, alignment=1, spaceAfter=10),
        'section': ParagraphStyle('section', parent=body, fontName='PredHei', fontSize=12.5,
                                  leading=19, spaceAfter=9, keepWithNext=True),
        'q': ParagraphStyle('q', parent=body, fontName='PredHei', keepWithNext=True, spaceBefore=6),
        'small': ParagraphStyle('small', parent=body, fontSize=9, leading=13),
        'cell': ParagraphStyle('cell', parent=body, fontSize=9.2, leading=13.5, spaceAfter=0),
        'code': ParagraphStyle('code', parent=body, fontSize=9, leading=12, spaceAfter=8),
    }


def blocks(text, st, table_padding=5):
    lines = normalize(text).splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line:
            continue
        if line.startswith('```'):
            code = []
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code.append(lines[i]); i += 1
            i += 1
            widest = max((pdfmetrics.stringWidth(x, 'PredSong', 9) for x in code), default=0)
            if widest > WIDTH - 8:
                raise ValueError('Wrap long code line: ' + max(code, key=len))
            out.append(XPreformatted(html.escape('\n'.join(code)), st['code']))
        elif line.startswith('|'):
            rows = [line]
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append(lines[i].strip()); i += 1
            rows = [[x.strip() for x in row[1:-1].split('|')] for row in rows
                    if not re.fullmatch(r'[\s|:\-]+', row)]
            if any(len(r) != len(rows[0]) for r in rows):
                raise ValueError('Unequal table columns')
            if rows[0] == ['起点', '终点', '权值'] and len(rows) > 7:
                edges = rows[1:]
                packed = [['起点—终点', '权值'] * 3]
                for start in range(0, len(edges), 3):
                    row = []
                    for edge in edges[start:start+3]:
                        row.extend([edge[0]+'—'+edge[1], edge[2]])
                    packed.append(row + [''] * (6-len(row)))
                rows = packed
            weights = [max(3, min(32, max(len(r[j]) for r in rows))) for j in range(len(rows[0]))]
            widths = [WIDTH * w / sum(weights) for w in weights]
            table = Table([[Paragraph(rich(c), st['cell']) for c in row] for row in rows],
                          colWidths=widths, repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('GRID',(0,0),(-1,-1),.4,colors.HexColor('#C9D1D8')),
                ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EAF0F5')),
                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                ('TOPPADDING',(0,0),(-1,-1),table_padding),('BOTTOMPADDING',(0,0),(-1,-1),table_padding),
                ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
            ]))
            out.extend([table, Spacer(1, 8)])
        else:
            out.append(Paragraph(rich(re.sub(r'^#{1,6}\s*', '', line)), st['body']))
    return out


def diagram(spec):
    """Small, labelled vector figures; problem data remain explicit in the text."""
    width, height = WIDTH, spec.get('height', 180)
    d = Drawing(width, height)
    ink = colors.HexColor('#263544')
    nodes, edges = {}, []
    if spec['kind'] == 'tree':
        children = spec['children']
        def walk(v, left, right, depth):
            if v is None:
                return
            x = (left + right) / 2
            nodes[v] = (x, height - 20 - 40 * depth)
            cs = children.get(v, [None, None])
            for index, c in enumerate(cs):
                if c is not None:
                    edges.append([v, c])
                    walk(c, left if index == 0 else x, x if index == 0 else right, depth + 1)
        walk(spec['root'], 12, width - 12, 0)
    else:
        labels = spec['nodes']
        custom = spec.get('positions', {})
        for i, v in enumerate(labels):
            if v in custom:
                nodes[v] = tuple(custom[v])
            else:
                angle = math.pi - 2 * math.pi * i / len(labels)
                nodes[v] = (width / 2 + (width / 2 - 30) * math.cos(angle),
                            height / 2 + (height / 2 - 22) * math.sin(angle))
        edges = spec['edges']
    for edge in edges:
        a, b = edge[:2]
        x, y = nodes[a]; xx, yy = nodes[b]
        length = math.hypot(xx-x, yy-y)
        ux, uy = (xx-x)/length, (yy-y)/length
        x += 13*ux; y += 13*uy; xx -= 13*ux; yy -= 13*uy
        d.add(Line(x,y,xx,yy,strokeColor=ink,strokeWidth=.8))
        if spec.get('directed'):
            d.add(Polygon([xx,yy,xx-7*ux+3*uy,yy-7*uy-3*ux,
                           xx-7*ux-3*uy,yy-7*uy+3*ux],fillColor=ink,strokeColor=ink))
        if len(edge) > 2:
            label = str(edge[2]); w = pdfmetrics.stringWidth(label,'PredSong',9)
            mx, my = (x+xx)/2+4*uy, (y+yy)/2-4*ux
            if len(edge) > 3:
                mx, my = edge[3]
            d.add(Rect(mx-w/2-2,my-2,w+4,12,fillColor=colors.white,strokeColor=None))
            d.add(String(mx,my,label,fontName='PredSong',fontSize=9,textAnchor='middle'))
    for v, (x,y) in nodes.items():
        if y < 13:
            raise ValueError('Tree figure too short')
        d.add(Circle(x,y,13,fillColor=colors.white,strokeColor=ink))
        d.add(String(x,y-3.5,str(v),fontName='PredSong',fontSize=10,textAnchor='middle'))
    return d


class WritingSpace(Flowable):
    def __init__(self, qid, minimum, records):
        super().__init__(); self.qid=qid; self.minimum=minimum; self.records=records
    def wrap(self, aw, ah):
        self.width=aw; self.height=max(self.minimum, ah-2)
        return self.width,self.height
    def draw(self):
        self.records.append({'id':self.qid,'page':self.canv.getPageNumber(),
                             'height_mm':round(self.height/mm,1)})
        self.canv.setStrokeColor(colors.HexColor('#DCE1E6'))
        self.canv.setLineWidth(.25)
        for y in range(8, int(self.height)-12, 25):
            self.canv.line(0,y,self.width,y)


def validate(data):
    paper=data['paper']; qs=data['questions']
    assert paper in (1,2,3)
    reading_points = [6,6,4,4] if paper == 1 else [4]*5
    assert len(qs) == len(reading_points)+20
    assert [q['section'] for q in qs] == ['I']*len(reading_points)+['II']*10+['III']*7+['IV']*3
    for sec, (_, points) in SECTIONS.items():
        if sec == 'I':
            points = reading_points
        group=[q for q in qs if q['section']==sec]
        assert [q['number'] for q in group]==list(range(1,len(points)+1))
        assert [q['points'] for q in group]==points
    assert sum(q['points'] for q in qs) == 150
    for q in qs:
        assert q['id']==f'P{paper}-{q["section"]}{q["number"]:02d}'
        for key in ('content','answer','basis','guide'):
            assert q.get(key) and len(q[key])>10,(q['id'],key)
        assert q['content'].count('```')%2==0 and q['answer'].count('```')%2==0
        assert not re.search('TODO|待补|参考答案|评分建议|教师|预测点',q['content']),q['id']
        assert not re.search('Θ|紧渐近',q['content']),q['id']
        if q['section']=='II':
            assert re.search(r'__\d+__|_{3,}',q['content']),q['id']
            assert not re.search(r'^[ABCD][.、]',q['content'],re.M)
        if q['section']=='IV':
            assert all(w in q['content'] for w in ('思想','复杂度'))
            assert not re.search(r'（[1-9]）',q['content']),q['id']
        if q['section']=='III':
            assert not re.search('解释原因|证明|说明理由',q['content']),q['id']
    cmap=pdfmetrics.getFont('PredSong').face.charToGlyph
    alltext=''.join(normalize(q[k]) for q in qs for k in ('content','answer','guide'))
    missing=sorted({c for c in alltext if ord(c)>32 and ord(c) not in cmap})
    assert not missing, f'Unsupported print glyphs {missing}'


def make_md(data, kind):
    p=data['paper']
    label={'试卷':'','答案':'参考答案','讲解':'逐题讲解稿'}[kind]
    lines=[f'# 2027考研重邮802押题卷 第{p}套 {label}'.rstrip(), '']
    if kind=='试卷':
        lines+=['满分150分，考试时间180分钟。四部分分值20、30、70、30分。',
                '各题独立，题内约定优先。程序用C或类C记法，整数运算不溢出；算法题写基本思想、实现及时间和辅助空间复杂度。','']
    else:
        lines+=['依据当前题面逐题解答；等价正确表达式及满足约束的其他算法同样有效。评分仅为教学建议。','']
    current=None
    for q in data['questions']:
        if q['section']!=current:
            current=q['section']; lines += ['## '+SECTIONS[current][0], '']
        lines += [f'### {q["number"]}（{q["points"]}分）', '']
        figure=[]
        if q.get('figure') and kind in ('试卷','讲解'):
            from reportlab.graphics import renderSVG
            asset=BASE/'源稿'/'配图'/f'{q["id"]}.svg'
            asset.parent.mkdir(exist_ok=True)
            renderSVG.drawToFile(diagram(q['figure']),str(asset))
            figure=[f'![第{q["number"]}题示意图](../配图/{asset.name})','']
        if kind=='试卷': lines += [q['content'],'']+figure
        elif kind=='答案': lines += [q['answer'],'']
        else:
            lines += ['**题目**',q['content'],'']+figure+['**讲解顺序**',q['guide'],'',
                      '**参考作答**',q['answer'],'', '**备课出处**',q['basis'],'']
    return '\n'.join(lines).rstrip()+'\n'


def build(data, kind):
    p=data['paper']; st=styles(); student=kind=='试卷'; records=[]
    label='' if student else '参考答案'
    output=BASE/'成品'/kind/f'重邮802押题卷第{p}套{label}.pdf'
    output.parent.mkdir(parents=True,exist_ok=True)
    story=[Paragraph(f'2027考研重邮802数据结构押题卷<br/>第{p}套 {label}',st['title'])]
    if student:
        story += [Paragraph('满分150分　考试时间180分钟　姓名：________________',st['body']),
                  Paragraph('各题独立，题内约定优先。程序可用C或类C记法，整数运算不溢出。算法题须写基本思想、实现及时间和辅助空间复杂度。',st['small'])]
    else:
        story += [Paragraph('等价正确写法同样有效；算法复杂度按实际实现分析。各小题分值为教学评分建议。',st['body'])]
    current=None
    for q in data['questions']:
        sec=q['section']
        if sec!=current:
            if current is not None: story.append(PageBreak())
            current=sec
            total=sum(SECTIONS[sec][1])
            story.append(Paragraph(f'{SECTIONS[sec][0]}（共{total}分）',st['section']))
        elif sec in ('III','IV') or student and sec=='I':
            story.append(PageBreak())
        story.append(CondPageBreak(80))
        group=[Paragraph(f'{q["number"]}．（{q["points"]}分）',st['q'])]
        group+=blocks(q['content'] if student else q['answer'],st,table_padding=5 if student else 4)
        if student and q.get('figure'):
            group += [diagram(q['figure']),Spacer(1,8)]
        elif not student and q.get('answer_figure'):
            group += [diagram(q['answer_figure']),Spacer(1,8)]
        if sec=='II':
            if student: group.append(Spacer(1,9))
            story.append(KeepTogether(group))
            if student and q['number'] in (5,10):
                story.append(Paragraph('草算区',st['small']))
                story.append(WritingSpace(q['id']+'-草算',25*mm,records))
                if q['number']==5:
                    story += [PageBreak(),Paragraph('二、填空题（续）',st['section'])]
        else:
            story.extend(group)
        if student and sec in ('I','III','IV'):
            story.append(Paragraph('作答区',st['small']))
            story.append(WritingSpace(q['id'],{'I':15,'III':75,'IV':45}[sec]*mm,records))
            if sec=='IV':
                story += [PageBreak(),Paragraph(f'四、第{q["number"]}题续答区（代码与分析）',st['section']),
                          WritingSpace(q['id']+'-续答',220*mm,records)]
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont('PredSong',9)
        canvas.drawString(19*mm,9*mm,f'重邮802押题卷 第{p}套 {label}')
        canvas.drawRightString(A4[0]-19*mm,9*mm,f'第{doc.page}页');canvas.restoreState()
    doc=SimpleDocTemplate(str(output),pagesize=A4,leftMargin=19*mm,rightMargin=19*mm,
                          topMargin=16*mm,bottomMargin=17*mm,
                          title=f'2027考研重邮802押题卷第{p}套{label}',author='')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return output,records


def render(path):
    import pypdfium2 as pdfium
    folder=TEMP/path.stem;folder.mkdir(parents=True,exist_ok=True)
    for old in folder.glob('*.png'):
        if re.fullmatch(r'\d+\.png',old.name): old.unlink()
    doc=pdfium.PdfDocument(str(path))
    for i in range(len(doc)):
        page=doc[i]; bmp=page.render(scale=1.3)
        bmp.to_pil().save(folder/f'{i+1:02d}.png');bmp.close();page.close()
    doc.close()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--papers',nargs='+',type=int,default=[1,2,3])
    ap.add_argument('--render',action='store_true');args=ap.parse_args();init()
    from pypdf import PdfReader
    report=[]
    for p in args.papers:
        source=BASE/'源稿'/f'第{p}套.json';data=json.loads(source.read_text(encoding='utf-8-sig'))
        validate(data)
        entry={'paper':p,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'outputs':[]}
        for kind in ('试卷','答案','讲解'):
            md=BASE/'源稿'/kind/f'第{p}套{kind}.md';md.parent.mkdir(parents=True,exist_ok=True)
            md.write_text(make_md(data,kind),encoding='utf-8')
            if kind=='讲解': continue
            output,spaces=build(data,kind);reader=PdfReader(output)
            text='\n'.join(page.extract_text() or '' for page in reader.pages)
            if kind=='试卷':
                assert not re.search('参考答案|评分建议|备课出处|讲解顺序',text)
            entry['outputs'].append({'file':str(output.relative_to(BASE)),'pages':len(reader.pages),
                                     'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'writing_spaces':spaces})
            if args.render:render(output)
        report.append(entry);print(f'Built paper {p}: {len(data["questions"])} questions, 150 points')
    folder=BASE/'审查';folder.mkdir(exist_ok=True)
    target=folder/'成卷核对.json'
    if target.exists():
        old=json.loads(target.read_text(encoding='utf-8'))
        report=[r for r in old['papers'] if r['paper'] not in args.papers]+report
    target.write_text(json.dumps({'papers':sorted(report,key=lambda x:x['paper']),
          '说明':'结构、总分、源稿/PDF绑定与作答留白记录；不替代独立数学核答或限时试做。'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
