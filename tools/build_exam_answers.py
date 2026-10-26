"""Build six independently printable answer keys from reviewed Markdown/JSON."""
from __future__ import annotations
import argparse,json,re,html,hashlib
from pathlib import Path
from build_exam_papers import ROOT,OUT,SECTIONS,init_pdf,split_blocks,rich,paper_profile
from exam_figures import drawing

def normalize(text):
    superscript=dict(zip('⁰¹²³⁴⁵⁶⁷⁸⁹','0123456789'))
    text=re.sub('[⁰¹²³⁴⁵⁶⁷⁸⁹]+',lambda m:'^'+''.join(superscript[c] for c in m[0]),text)
    subscript=dict(zip('₀₁₂₃₄₅₆₇₈₉','0123456789'))
    text=re.sub('[₀₁₂₃₄₅₆₇₈₉]+',lambda m:'_'+''.join(subscript[c] for c in m[0]),text)
    for a,b in {'−':'-','–':'-','—':'-','∅':'NULL','₀':'_0','₁':'_1','₂':'_2','ᵢ':'_i','ₖ':'_k','ₙ':'_n','↔':'<->','⋅':'*','⋯':'...'}.items():text=text.replace(a,b)
    text=re.sub(r'⌊([^⌊⌋]+)⌋',r'floor(\1)',text)
    return re.sub(r'⌈([^⌈⌉]+)⌉',r'ceil(\1)',text)

def answer_data(paper):
    a=json.loads((OUT/f'源稿/答案/第{paper}套.json').read_text(encoding='utf-8-sig'))
    q=json.loads((OUT/f'源稿/试题/第{paper}套.json').read_text(encoding='utf-8-sig'))
    assert [x['id'] for x in a['questions']]==[x['id'] for x in q['questions']],f'S{paper} answer order/missing questions'
    for aq,sq in zip(a['questions'],q['questions']):
        assert len(aq['content'])>15 and aq['content'].count('```')%2==0,aq['id']
        assert aq.get('references'),aq['id']+' lacks provenance'
        assert not re.search(r'Θ|紧渐近|Theta',aq['content']),aq['id']+' contains untaught notation'
        aq.update(section=sq['section'],number=sq['number'],points=sq['points'])
        aq['content']=normalize(aq['content'])
        from reportlab.pdfbase import pdfmetrics
        cmap=pdfmetrics.getFont('ExamSong').face.charToGlyph
        missing=sorted({c for c in aq['content'] if ord(c)>32 and ord(c) not in cmap})
        if missing:raise ValueError(f'{aq["id"]}: unsupported print glyphs {missing}')
    return a

def figure_groups(qid,specs,width,style):
    from reportlab.platypus import Paragraph,Spacer,Table,TableStyle,KeepTogether
    items=specs.get(qid,[])
    result=[]
    i=0
    while i<len(items):
        group=[items[i]]
        if i+1<len(items) and sum(s['size'][0] for s in items[i:i+2])<=(width-16)/0.82:group.append(items[i+1])
        cells=[]
        for s in group:
            fig=drawing(s);scale=min(1,(width/len(group)-8)/fig.width,250/fig.height)
            fig.scale(scale,scale);fig.width*=scale;fig.height*=scale;fig.hAlign='CENTER'
            cells.append([fig,Paragraph(rich(s['caption']),style)])
        if len(cells)==1:result.append(KeepTogether(cells[0]))
        else:
            table=Table([cells],colWidths=[width/len(group)]*len(group))
            table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]))
            result.append(table)
        result.append(Spacer(1,8));i+=len(group)
    return result

def build(data,specs):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,XPreformatted,KeepTogether
    from reportlab.pdfbase.pdfmetrics import stringWidth
    margin=19*mm;width=A4[0]-margin*2-12
    body=ParagraphStyle('AnswerBody',fontName='ExamSong',fontSize=10.5,leading=15,wordWrap='CJK',spaceAfter=7,allowWidows=0,allowOrphans=0)
    title=ParagraphStyle('AnswerTitle',parent=body,fontName='ExamHei',fontSize=16,leading=24,alignment=1,spaceAfter=10)
    section=ParagraphStyle('AnswerSection',parent=body,fontName='ExamHei',fontSize=12.5,leading=19,spaceBefore=8,spaceAfter=10,keepWithNext=True)
    num=ParagraphStyle('AnswerNumber',parent=body,fontName='ExamHei',spaceBefore=9,spaceAfter=6,keepWithNext=True)
    fill_body=ParagraphStyle('FillBody',parent=body,leading=14,spaceAfter=4)
    fill_num=ParagraphStyle('FillNumber',parent=num,spaceBefore=5,spaceAfter=4)
    caption=ParagraphStyle('Caption',parent=body,fontSize=9,leading=13,alignment=1)
    cell=ParagraphStyle('AnswerCell',parent=body,fontSize=9.5,leading=13,spaceAfter=0)
    paper=data['paper'];target=OUT/f'成品/答案/重邮802模拟试卷第{paper}套答案.pdf';target.parent.mkdir(exist_ok=True)
    doc=SimpleDocTemplate(str(target),pagesize=A4,leftMargin=margin,rightMargin=margin,topMargin=18*mm,bottomMargin=18*mm,title=f'2027重邮802模拟试卷第{paper}套参考答案',author='',subject='参考答案与评分建议')
    story=[Paragraph(f'2027考研重邮802数据结构模拟试卷<br/>第{paper}套 参考答案',title),Paragraph('对应第6版题面。程序填空接受等价写法；非唯一的树形、编码或路径按题内规则判分。算法实现仅给出一种正确方法，其他满足题目约束的解法同样有效。',body),Paragraph('评分建议用于核对作答要点。复杂度须与考生实际实现一致；不能仅因实现与参考代码不同而扣分。',body)]
    current=None
    for q in data['questions']:
        if q['section']!=current:
            if current is not None:story.append(PageBreak())
            current=q['section'];story.append(Paragraph(SECTIONS[current][0],section))
        elif current in ('III','IV'):story.append(PageBreak())
        start=len(story)
        story.append(Paragraph(f'{q["number"]}．（{q["points"]}分）',fill_num if current=='II' else num))
        for kind,val in split_blocks(q['content']):
            if kind=='paragraph':
                val=re.sub(r'^#{1,6}\s*','',val)
                story.append(Paragraph(rich(val),fill_body if current=='II' else body))
            elif kind=='code':
                if current=='III' and q['id'] in specs and re.search(r'(?m)[/\\]|^[ \t]*[LR]:|\|--',val):
                    # Retain the editable text structure in JSON/Markdown. The
                    # print edition uses the independently checked vector tree.
                    story.append(Paragraph('树形见本题示意图。',body))
                    continue
                maxw=max((stringWidth(line,'ExamSong',9) for line in val.splitlines()),default=0)
                size=min(9,9*width/max(maxw,1))
                if size<8:raise ValueError(q['id']+f': code line too wide {maxw:.1f}pt; explicitly wrap source')
                cs=ParagraphStyle('AnswerCode',fontName='ExamSong',fontSize=size,leading=size+2,spaceAfter=8)
                story.append(XPreformatted(html.escape(val),cs))
            else:
                if any(len(row)!=len(val[0]) for row in val):raise ValueError(q['id']+': malformed table')
                weights=[max(3,min(25,max(len(c.replace('`','')) for c in [row[i] for row in val]))) for i in range(len(val[0]))]
                t=Table([[Paragraph(rich(c),cell) for c in row] for row in val],colWidths=[width*w/sum(weights) for w in weights],repeatRows=1,hAlign='LEFT')
                t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.4,colors.HexColor('#BBBBBB')),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EEEEEE')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
                story.extend([t,Spacer(1,7)])
        story.extend(figure_groups(q['id'],specs,width,caption))
        if current=='II':story[start:]=[KeepTogether(story[start:])]
    def footer(c,d):
        c.saveState();c.setFont('ExamSong',9);c.drawString(margin,9*mm,f'重邮802模拟试卷 第{paper}套 参考答案');c.drawRightString(A4[0]-margin,9*mm,f'第{d.page}页');c.restoreState()
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return target

def markdown(data,specs):
    lines=[f'# 重邮802模拟试卷第{data["paper"]}套参考答案','', '对应第6版题面。等价正确解法同样给分，复杂度应与实际实现一致。','']
    current=None
    for q in data['questions']:
        if q['section']!=current:current=q['section'];lines.extend([f'## {SECTIONS[current][0]}',''])
        lines.extend([f'### {q["number"]}（{q["points"]}分）','',q['content'],''])
        for i,s in enumerate(specs.get(q['id'],[]),1):lines.extend([f'![{s["caption"]}](../配图/答案/{q["id"]}-{i}.png)',''])
    return '\n'.join(lines)

def render(target,paper):
    import pypdfium2 as pdfium
    dest=ROOT/f'_tmp/exam_final/rendered_answers/第{paper}套';dest.mkdir(parents=True,exist_ok=True)
    pdf=pdfium.PdfDocument(str(target));pages=len(pdf)
    for i in range(pages):
        page=pdf[i];bitmap=page.render(scale=1.5);bitmap.to_pil().save(dest/f'page-{i+1:02d}.png');bitmap.close();page.close()
    pdf.close()
    for p in dest.glob('page-*.png'):
        if int(p.stem.split('-')[-1])>pages:p.unlink()
    return pages

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--papers',nargs='+',type=int,default=list(range(1,7)));parser.add_argument('--render',action='store_true');args=parser.parse_args()
    init_pdf();specs=json.loads((OUT/'源稿/答案配图源稿.json').read_text(encoding='utf-8'))
    md=OUT/'源稿/答案';md.mkdir(exist_ok=True);reports=[]
    for p in args.papers:
        data=answer_data(p);target=build(data,specs);(md/f'第{p}套答案.md').write_text(markdown(data,specs),encoding='utf-8')
        from pypdf import PdfReader
        pages=render(target,p) if args.render else len(PdfReader(target).pages)
        reports.append({'paper':p,'questions':24,'pages':pages,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()});print(f'PASS answer {p}: 24 questions, {pages} pages')
    if sorted(args.papers)==list(range(1,7)):
        from pypdf import PdfWriter
        writer=PdfWriter()
        for p in args.papers:writer.append(str(OUT/f'成品/答案/重邮802模拟试卷第{p}套答案.pdf'),outline_item=f'第{p}套答案')
        writer.write(str(OUT/'成品/六套模拟试卷答案合订本.pdf'));writer.close()
        (OUT/'审查/答案成卷核对.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
