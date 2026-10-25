"""Reconstruct reference solution trees from final question data, then draw them."""
from __future__ import annotations
import json, heapq
from pathlib import Path
from exam_figures import drawing,OUT
from build_exam_papers import init_pdf

def node(key,left=None,right=None): return [key,left,right]
def reconstruct(pre,ino):
    if not pre:return None
    k=ino.index(pre[0]);return node(pre[0],reconstruct(pre[1:k+1],ino[:k]),reconstruct(pre[k+1:],ino[k+1:]))
def balanced(a):
    if not a:return None
    k=(len(a)-1)//2;return node(a[k],balanced(a[:k]),balanced(a[k+1:]))
def height(t):return 0 if t is None else 1+max(height(t[1]),height(t[2]))
def rotate_right(t):
    a=t[1];t[1]=a[2];a[2]=t;return a
def rotate_left(t):
    a=t[2];t[2]=a[1];a[1]=t;return a
def insert(t,k,avl=False):
    if t is None:return node(k)
    side=1 if k<t[0] else 2;t[side]=insert(t[side],k,avl)
    if avl:
        b=height(t[1])-height(t[2])
        if b>1:
            if k>t[1][0]:t[1]=rotate_left(t[1])
            t=rotate_right(t)
        elif b< -1:
            if k<t[2][0]:t[2]=rotate_right(t[2])
            t=rotate_left(t)
    return t
def bst(a,avl=False):
    t=None
    for k in a:t=insert(t,k,avl)
    return t
def huffman(weights):
    heap=[(w,chr(65+i),node(f'{chr(65+i)}:{w}')) for i,w in enumerate(weights)];heapq.heapify(heap)
    while len(heap)>1:
        a,b=heapq.heappop(heap),heapq.heappop(heap)
        heapq.heappush(heap,(a[0]+b[0],min(a[1],b[1]),node(a[0]+b[0],a[2],b[2])))
    return heap[0][2]
def tree_spec(t,caption,huff=False):
    nodes=[];edges=[];order=[]; depth=height(t)
    def visit(t,d,parent=None,side=None):
        if t is None:return
        uid=str(len(nodes));nodes.append({'id':uid,'label':str(t[0]),'depth':d,'radius':13,'font_size':10})
        if parent is not None:edges.append({'u':parent,'v':uid,**({'label':str(side-1)} if huff else {})})
        visit(t[1],d+1,uid,1);order.append(uid);visit(t[2],d+1,uid,2)
    visit(t,0)
    width=min(450,max(230,len(nodes)*34+30))
    gap=32 if huff else 44
    for n in nodes:
        n['x']=15+(order.index(n['id'])+.5)*(width-30)/len(nodes)
        n['y']=25+(depth-1-n.pop('depth'))*gap
    return {'size':[width,depth*gap+9],'nodes':nodes,'edges':edges,'caption':caption,'tree':t,'huffman':huff}
def build():
    out={}
    def add(q,t,caption,huff=False):out.setdefault(q,[]).append(tree_spec(t,caption,huff))
    add('S1-III01',reconstruct(list('ABDECFG'),list('DBEACGF')),'重建二叉树')
    add('S1-III02',huffman([3,5,7,9,20]),'一组Huffman树（叶结点为字符:频率，左0右1）',True)
    add('S1-III04',balanced([4,9,13,18,25,29,35,41,50,58]),'折半查找判定树')
    for avl in (False,True):add('S1-III06',bst([30,10,20,40,35],avl),'最终AVL树' if avl else '普通BST')
    add('S2-III01',node('A',node('B',node('D',None,node('E')),node('C')),node('F',node('G',node('H'),node('I')))),'转换后的孩子兄弟二叉树')
    add('S2-III02',balanced([3,8,12,17,21,26,31,44]),'折半查找判定树')
    add('S2-III06',huffman([2,3,4,7,8,12]),'一组Huffman树（叶结点为字符:频率，左0右1）',True)
    add('S3-III01',reconstruct(list('MFCHTQW'),list('CFHMQTW')),'重建二叉树')
    for avl in (False,True):add('S3-III02',bst([30,20,40,10,25,22],avl),'最终AVL树' if avl else '普通BST')
    add('S3-III06',balanced([3,8,11,18,21,27,30]),'折半查找判定树')
    for avl in (False,True):add('S4-III06',bst([40,20,60,50,70,45],avl),'最终AVL树' if avl else '普通BST')
    add('S5-III01',reconstruct(list('ABDECFG'),list('DBEAFCG')),'重建二叉树')
    add('S5-III02',balanced([5,12,18,23,31,42,57,66,74,89]),'折半查找判定树')
    add('S5-III03',huffman([2,4,7,10,15,25]),'原频率Huffman树（叶结点为字符:频率）',True)
    add('S5-III03',huffman([9,4,7,10,15,25]),'新频率Huffman树（叶结点为字符:频率）',True)
    add('S5-III04',bst([40,20,10,30,60,50,70]),'普通BST')
    add('S6-III01',huffman([3,5,7,11,13,18]),'Huffman树（叶结点为字符:频率，左0右1）',True)
    forest={'size':[450,160],'nodes':[{'id':k,'x':x,'y':y} for k,x,y in [('A',160,130),('B',100,75),('C',100,20),('D',220,75),('E',220,20),('F',355,130),('G',355,75)]],'edges':[{'u':u,'v':v} for u,v in [('A','B'),('A','D'),('B','C'),('D','E'),('F','G')]],'caption':'恢复后的有序森林'}
    out['S6-III02']=[forest]
    add('S6-III03',balanced(list(range(1,12))),'完整下标判定树')
    for avl in (False,True):add('S6-III04',bst([30,10,20,50,40,60,70],avl),'最终AVL树' if avl else '普通BST')
    add('S6-III04',balanced(list(range(1,8))),'下标判定树')
    return out

def main():
    specs=build();init_pdf();dest=OUT/'答案配图';dest.mkdir(exist_ok=True)
    from reportlab.graphics import renderPDF,renderSVG
    import pypdfium2 as pdfium
    for qid,items in specs.items():
        for i,s in enumerate(items,1):
            d=drawing(s);stem=f'{qid}-{i}'
            renderSVG.drawToFile(d,str(dest/f'{stem}.svg'))
            pdf=pdfium.PdfDocument(renderPDF.drawToString(d));page=pdf[0];bitmap=page.render(scale=2)
            bitmap.to_pil().save(dest/f'{stem}.png');bitmap.close();page.close();pdf.close()
    (OUT/'答案配图源稿.json').write_text(json.dumps(specs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(sum(map(len,specs.values())),'answer diagrams')
if __name__=='__main__':main()
