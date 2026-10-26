"""Typeset the three institution prediction papers' independently solved keys."""
from pathlib import Path
import argparse, html, json, re, math, hashlib
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                              Table, TableStyle, XPreformatted, KeepTogether)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
from reportlab.graphics.shapes import Drawing, Line, Circle, Rect, String, Polygon

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'试卷'/'2026机构押题'
pdfmetrics.registerFont(TTFont('Song',r'C:\Windows\Fonts\simsun.ttc',subfontIndex=0))
pdfmetrics.registerFont(TTFont('Hei',r'C:\Windows\Fonts\simhei.ttf'))
pdfmetrics.registerFontFamily('Song',normal='Song',bold='Hei',italic='Song',boldItalic='Hei')

def rich(s):
    s=html.escape(s)
    s=re.sub(r'`([^`]+)`',r'\1',s)
    return re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',s)

def tree(spec):
    """Explicit child lists preserve missing left/right positions in binary trees."""
    roots=spec.get('roots',[spec.get('tree')]);width=465
    positions=[];edges=[];counter=0;maxdepth=0
    def walk(node,depth):
        nonlocal counter,maxdepth
        if node is None:
            counter+=1
            return (counter-1)*45
        if isinstance(node,str):node={'label':node}
        kids=node.get('children',[])
        child_ids=[];xs=[]
        for child in kids:
            before=len(positions);x=walk(child,depth+1);xs.append(x)
            child_ids.append(None if child is None else len(positions)-1)
        if not xs:
            x=counter*45;counter+=1
        else:x=(xs[0]+xs[-1])/2
        idx=len(positions);positions.append((x,depth,node));maxdepth=max(depth,maxdepth)
        for ci in child_ids:
            if ci is not None:edges.append((idx,ci))
        return x
    for root in roots:
        walk(root,0);counter+=1
    minx=min(x for x,_,_ in positions);maxx=max(x for x,_,_ in positions)
    span=max(1,maxx-minx)
    sx=min(1.55,(width-85)/span)
    depthgap=spec.get('gap',48);height=(maxdepth+1)*depthgap+24
    d=Drawing(width,height);ink=HexColor('#263544')
    def point(i):
        x,dep,n=positions[i]
        return ((x-(minx+maxx)/2)*sx+width/2,height-25-dep*depthgap)
    for i,j in edges:
        x,y=point(i);a,b=point(j)
        d.add(Line(x,y,a,b,strokeColor=ink,strokeWidth=1))
    for i,(_,dep,n) in enumerate(positions):
        x,y=point(i);label=str(n['label']);size=n.get('font_size',11)
        if spec.get('box') or len(label)>5:
            w=max(34,pdfmetrics.stringWidth(label,'Song',size)+14)
            d.add(Rect(x-w/2,y-12,w,24,fillColor=white,strokeColor=ink))
        else:d.add(Circle(x,y,15 if len(label)<4 else 20,fillColor=white,strokeColor=ink))
        d.add(String(x,y-3.5,label,fontName='Song',fontSize=size,textAnchor='middle',fillColor=ink))
    return d

def network(spec):
    width,height=spec.get('size',[465,230]);d=Drawing(width,height)
    ink=HexColor('#263544');nodes={n['id']:n for n in spec['nodes']}
    for e in spec['edges']:
        a,b=nodes[e[0]],nodes[e[1]];x,y=a['x'],a['y'];xx,yy=b['x'],b['y']
        length=math.hypot(xx-x,yy-y);ux,uy=(xx-x)/length,(yy-y)/length
        x+=15*ux;y+=15*uy;xx-=15*ux;yy-=15*uy
        d.add(Line(x,y,xx,yy,strokeColor=ink,strokeWidth=1.1))
        if spec.get('directed'):
            d.add(Polygon([xx,yy,xx-7*ux+3*uy,yy-7*uy-3*ux,xx-7*ux-3*uy,yy-7*uy+3*ux],fillColor=ink,strokeColor=ink))
        if len(e)>2:
            label=str(e[2]);lx,ly=(x+xx)/2,(y+yy)/2+7
            if len(e)>3:lx,ly=e[3]
            tw=pdfmetrics.stringWidth(label,'Song',10)
            d.add(Rect(lx-tw/2-2,ly-2,tw+4,12,fillColor=white,strokeColor=None))
            d.add(String(lx,ly,label,fontName='Song',fontSize=10,textAnchor='middle'))
    for e in spec.get('threads',[]):
        a,b=nodes[e['u']],nodes[e['v']]
        pts=[(a['x'],a['y'])]+[tuple(p) for p in e.get('via',[])]+[(b['x'],b['y'])]
        dx,dy=pts[1][0]-pts[0][0],pts[1][1]-pts[0][1];r=math.hypot(dx,dy)
        pts[0]=(pts[0][0]+15*dx/r,pts[0][1]+15*dy/r)
        dx,dy=pts[-1][0]-pts[-2][0],pts[-1][1]-pts[-2][1];r=math.hypot(dx,dy);ux,uy=dx/r,dy/r
        cut=7 if b.get('null') else 15;pts[-1]=(pts[-1][0]-cut*ux,pts[-1][1]-cut*uy)
        blue=HexColor('#356795')
        for aa,bb in zip(pts,pts[1:]):d.add(Line(*aa,*bb,strokeColor=blue,strokeWidth=.9,strokeDashArray=[4,3]))
        x,y=pts[-1];d.add(Polygon([x,y,x-7*ux+2.5*uy,y-7*uy-2.5*ux,x-7*ux-2.5*uy,y-7*uy+2.5*ux],fillColor=blue,strokeColor=blue))
    for n in nodes.values():
        if not n.get('null'):d.add(Circle(n['x'],n['y'],15,fillColor=white,strokeColor=ink))
        d.add(String(n['x'],n['y']-4,str(n.get('label',n['id'])),fontName='Song',fontSize=11,textAnchor='middle'))
    return d

def cells(spec):
    d=Drawing(*spec['size']);ink=HexColor('#263544')
    for n in spec['nodes']:
        x,y=n['x'],n['y'];texts=n['cells'];w=n.get('w',120);h=26
        d.add(Rect(x,y,w,h,fillColor=white,strokeColor=ink))
        for j,s in enumerate(texts):
            if j:d.add(Line(x+j*w/len(texts),y,x+j*w/len(texts),y+h,strokeColor=ink))
            d.add(String(x+(j+.5)*w/len(texts),y+9,str(s),fontName='Song',fontSize=9,textAnchor='middle'))
        d.add(String(x,y+31,n['id'],fontName='Song',fontSize=9))
    for pts in spec['edges']:
        for a,b in zip(pts,pts[1:]):d.add(Line(*a,*b,strokeColor=ink,strokeWidth=.8))
        a,b=pts[-2:];dx,dy=b[0]-a[0],b[1]-a[1];r=math.hypot(dx,dy);ux,uy=dx/r,dy/r
        x,y=b;d.add(Polygon([x,y,x-6*ux+2.5*uy,y-6*uy-2.5*ux,x-6*ux-2.5*uy,y-6*uy+2.5*ux],fillColor=ink,strokeColor=ink))
    return d

def figure(spec):
    return {'network':network,'cells':cells}.get(spec.get('kind'),tree)(spec)

def build(num):
    source=OUT/'源稿/可编辑答案'/f'押题卷{num}参考答案.md'
    specs=json.loads((OUT/'源稿/配图源稿.json').read_text(encoding='utf-8'))
    md=source.read_text(encoding='utf-8')
    assert not re.search(r'<!--(?:COMPREHENSIVE|FLOYD)-->|TODO|待补齐',md)
    assert len(re.findall(r'^### ',md,re.M))==24
    cmap=pdfmetrics.getFont('Song').face.charToGlyph
    missing=sorted({c for c in md if ord(c)>32 and ord(c) not in cmap})
    if missing:raise ValueError(f'Unsupported glyphs: {missing}')
    body=ParagraphStyle('body',fontName='Song',fontSize=10.5,leading=15.5,
                        wordWrap='CJK',spaceAfter=7,allowWidows=0,allowOrphans=0)
    title=ParagraphStyle('title',parent=body,fontName='Hei',fontSize=16,leading=24,alignment=1,spaceAfter=12)
    sec=ParagraphStyle('section',parent=body,fontName='Hei',fontSize=12.5,leading=19,spaceAfter=10,keepWithNext=True)
    qstyle=ParagraphStyle('question',parent=body,fontName='Hei',spaceBefore=7,spaceAfter=7,keepWithNext=True)
    cell=ParagraphStyle('cell',parent=body,fontSize=9.5,leading=13,spaceAfter=0)
    cap=ParagraphStyle('caption',parent=body,fontSize=9,leading=13,alignment=1)
    lead=ParagraphStyle('figureLead',parent=body,keepWithNext=True)
    width=A4[0]-38*72/25.4-12
    story=[];lines=md.splitlines();i=0;section='';question=0
    while i<len(lines):
        line=lines[i].strip();i+=1
        if not line:continue
        if line=='<!--pagebreak-->':story.append(PageBreak());continue
        if line.startswith('# '):story.append(Paragraph(rich(line[2:]),title));continue
        if line.startswith('## '):
            if section:story.append(PageBreak())
            section=line[3:];question=0;story.append(Paragraph(rich(section),sec));continue
        if line.startswith('### '):
            if question and section.startswith(('三','四')):story.append(PageBreak())
            question+=1;story.append(Paragraph(rich(line[4:]),qstyle));continue
        if line.startswith('{{FIG:'):
            key=line[6:-2];spec=specs[key];fig=figure(spec)
            story.append(KeepTogether([fig,Paragraph(rich(spec.get('caption','')),cap),Spacer(1,6)]));continue
        if line.startswith('```'):
            rows=[]
            while i<len(lines) and not lines[i].strip().startswith('```'):
                rows.append(lines[i]);i+=1
            i+=1
            maxw=max((pdfmetrics.stringWidth(x,'Song',9) for x in rows),default=0)
            size=min(9,9*width/max(maxw,1))
            if size<7.8:raise ValueError(f'Wrap long code line in {source}: {maxw}')
            style=ParagraphStyle('code',fontName='Song',fontSize=size,leading=size+2.5,spaceAfter=9)
            story.append(XPreformatted(html.escape('\n'.join(rows)),style));continue
        if line.startswith('|'):
            rows=[]
            while True:
                if not re.match(r'^\|[\s:|\-]+\|$',line):
                    rows.append([x.strip() for x in re.split(r'(?<!\\)\|',line.strip('|'))])
                if i>=len(lines) or not lines[i].strip().startswith('|'):break
                line=lines[i].strip();i+=1
            if any(len(r)!=len(rows[0]) for r in rows):raise ValueError('Malformed table: '+str(rows))
            weights=[max(3,min(34,max(len(r[j]) for r in rows))) for j in range(len(rows[0]))]
            table=Table([[Paragraph(rich(c.replace('\\|','|')),cell) for c in row] for row in rows],
                        colWidths=[width*w/sum(weights) for w in weights],repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.4,HexColor('#b5b5b5')),
                  ('BACKGROUND',(0,0),(-1,0),HexColor('#eeeeee')),('VALIGN',(0,0),(-1,-1),'TOP'),
                  ('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
                  ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
            story.extend([table,Spacer(1,8)]);continue
        chunks=[line]
        while i<len(lines) and lines[i].strip() and not lines[i].strip().startswith(('#','|','```','{{','<!--')):
            chunks.append(lines[i].strip());i+=1
        j=i
        while j<len(lines) and not lines[j].strip():j+=1
        style=lead if j<len(lines) and lines[j].strip().startswith('{{FIG:') else body
        story.append(Paragraph(rich(' '.join(chunks)),style))
    target=OUT/'成品'/f'押题卷{num}参考答案.pdf'
    def footer(c,doc):
        c.saveState();c.setFont('Song',8)
        c.drawString(19*72/25.4,24,f'重邮802数据结构 押题卷{num} 参考答案')
        c.drawRightString(A4[0]-19*72/25.4,24,f'第{doc.page}页');c.restoreState()
    doc=SimpleDocTemplate(str(target),pagesize=A4,leftMargin=19*72/25.4,rightMargin=19*72/25.4,
        topMargin=18*72/25.4,bottomMargin=18*72/25.4,title=f'重邮802押题卷{num}参考答案',author='',
        subject='source-sha256:'+hashlib.sha256(md.encode('utf-8')).hexdigest())
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(target)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('paper',choices=['一','二','三']);args=p.parse_args();build(args.paper)
