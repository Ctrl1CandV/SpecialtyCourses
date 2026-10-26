from pathlib import Path
import fitz, json, re, sys, hashlib
from PIL import Image, ImageOps, ImageDraw
root=Path(__file__).resolve().parents[1]
out=root/'试卷/2026机构押题'
paper=sys.argv[1]
p=out/'成品'/f'押题卷{paper}参考答案.pdf'
md=(out/'源稿/可编辑答案'/f'押题卷{paper}参考答案.md').read_text(encoding='utf-8')
assert not re.search(r'<!--(?:COMPREHENSIVE|FLOYD)-->|TODO|待补齐',md)
assert len(re.findall(r'^### ',md,re.M))==24
doc=fitz.open(p); dest=root/'_tmp/押题卷答案制作'/f'卷{paper}成品预览';dest.mkdir(parents=True,exist_ok=True)
assert doc.metadata.get('subject')=='source-sha256:'+hashlib.sha256(md.encode('utf-8')).hexdigest(), 'PDF is stale'
for old in list(dest.glob('p[0-9][0-9].png'))+list(dest.glob('contact-*.png')):
    old.unlink()
errors=[];sizes=[];thumbs=[]
for i,page in enumerate(doc):
    text=page.get_text();sizes.append(len(text))
    if '\ufffd' in text:errors.append(f'page {i+1}: replacement glyph')
    for b in page.get_text('dict')['blocks']:
        for line in b.get('lines',[]):
            for sp in line['spans']:
                x0,y0,x1,y1=sp['bbox']
                if x0<30 or x1>page.rect.width-26 or y0<20 or y1>page.rect.height-18:
                    errors.append(f'page {i+1}: bounds {sp["text"]!r} {sp["bbox"]}')
    img=page.get_pixmap(matrix=fitz.Matrix(1.5,1.5));img.save(dest/f'p{i+1:02d}.png')
    im=Image.frombytes('RGB',[img.width,img.height],img.samples)
    im.thumbnail((310,438));thumb=Image.new('RGB',(330,466),'#dddddd');thumb.paste(im,((330-im.width)//2,5))
    ImageDraw.Draw(thumb).text((12,446),f'Page {i+1}',fill='black');thumbs.append(thumb)
for start in range(0,len(thumbs),8):
    group=thumbs[start:start+8];sheet=Image.new('RGB',(330*4,466*2),'white')
    for j,t in enumerate(group):sheet.paste(t,((j%4)*330,(j//4)*466))
    sheet.save(dest/f'contact-{start//8+1}.png')
result={'paper':paper,'pages':len(doc),'question_count':24,'page_chars':sizes,'errors':errors}
(dest/'checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
assert not errors,errors
print(json.dumps(result,ensure_ascii=False))
