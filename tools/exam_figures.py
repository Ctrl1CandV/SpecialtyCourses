"""Deterministic, vector tree/graph illustrations for exams and answer keys."""
from __future__ import annotations
import json, math
from pathlib import Path
from reportlab.graphics.shapes import Drawing, Circle, Line, String, Polygon, Rect, Path as DrawPath
from reportlab.lib.colors import HexColor, white

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'试卷/六套模拟卷'
SPEC=OUT/'源稿/配图源稿.json'

def load_specs():
    return json.loads(SPEC.read_text(encoding='utf-8')) if SPEC.exists() else {}

def drawing(spec):
    """All geometry is explicit and reproducible; edge lists remain authoritative."""
    w,h=spec.get('size',[450,190]); d=Drawing(w,h)
    nodes={str(n['id']):n for n in spec['nodes']}
    ink=HexColor('#263544'); radius=spec.get('radius',12)
    for e in spec['edges']:
        u,v=nodes[str(e['u'])],nodes[str(e['v'])]
        points=[(u['x'],u['y'])]+[tuple(p) for p in e.get('via',[])]+[(v['x'],v['y'])]
        dx,dy=points[1][0]-points[0][0],points[1][1]-points[0][1]; length=math.hypot(dx,dy)
        points[0]=(points[0][0]+radius*dx/length,points[0][1]+radius*dy/length)
        dx,dy=points[-1][0]-points[-2][0],points[-1][1]-points[-2][1]; length=math.hypot(dx,dy)
        ux,uy=dx/length,dy/length
        points[-1]=(points[-1][0]-radius*ux,points[-1][1]-radius*uy)
        for a,b in zip(points,points[1:]): d.add(Line(*a,*b,strokeColor=ink,strokeWidth=1.1))
        if e.get('directed',spec.get('directed',False)):
            x,y=points[-1]; back=6; half=2.5
            d.add(Polygon([x,y,x-back*ux+half*uy,y-back*uy-half*ux,x-back*ux-half*uy,y-back*uy+half*ux],fillColor=ink,strokeColor=ink))
        label=e.get('label','')
        if label!='':
            default=[(u['x']+v['x'])/2,(u['y']+v['y'])/2+6]
            if spec.get('huffman'):
                sx,sy=v['x']-u['x'],v['y']-u['y'];sl=math.hypot(sx,sy)
                sign=1 if sx>=0 else -1
                default=[(u['x']+v['x'])/2-sign*11*sy/sl,(u['y']+v['y'])/2+sign*11*sx/sl-3]
            x,y=e.get('label_pos',default)
            from reportlab.pdfbase.pdfmetrics import stringWidth
            tw=stringWidth(str(label),'ExamSong',10)
            d.add(Rect(x-tw/2-3,y-2,tw+6,13,fillColor=white,strokeColor=None))
            d.add(String(x,y,str(label),fontName='ExamSong',fontSize=10,textAnchor='middle',fillColor=ink))
    for n in nodes.values():
        r=n.get('radius',radius)
        d.add(Circle(n['x'],n['y'],r,fillColor=white,strokeColor=ink,strokeWidth=1.2))
        d.add(String(n['x'],n['y']-3.8,str(n.get('label',n['id'])),fontName='ExamSong',fontSize=n.get('font_size',11),textAnchor='middle',fillColor=ink))
    return d

def export_figures():
    from reportlab.graphics import renderSVG,renderPM
    from build_exam_papers import init_pdf
    init_pdf(); dest=OUT/'源稿/配图/试题'; dest.mkdir(exist_ok=True)
    import pypdfium2 as pdfium
    from reportlab.graphics import renderPDF
    import io
    for qid,spec in load_specs().items():
        d=drawing(spec)
        renderSVG.drawToFile(d,str(dest/f'{qid}.svg'))
        pdf=pdfium.PdfDocument(renderPDF.drawToString(d))
        page=pdf[0]; bitmap=page.render(scale=2)
        bitmap.to_pil().save(dest/f'{qid}.png')
        bitmap.close();page.close();pdf.close()

if __name__=='__main__': export_figures()
