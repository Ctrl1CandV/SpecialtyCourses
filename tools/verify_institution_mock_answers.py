"""Check source bindings, PDF layout and executable algorithms for the mock keys."""
from pathlib import Path
import argparse
import hashlib
import json
import random
import re
import subprocess
import sys

import fitz
from PIL import Image, ImageDraw
from build_institution_mock_answers import ROOT, OUT, FIGURES, source_path, fingerprint

TEMP = ROOT / '_tmp/2026机构模拟答案'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_pdf(number, render):
    md = source_path(number).read_text(encoding='utf-8')
    expected = re.findall(r'^### (.+)$', md, re.M)
    assert len(expected) == 23
    pdf = OUT / '成品' / f'模拟卷{number}参考答案.pdf'
    doc = fitz.open(pdf)
    assert doc.metadata.get('subject') == 'source-sha256:' + fingerprint(number)
    errors, chars, thumbs = [], [], []
    dest = TEMP / f'模拟卷{number}成品预览'
    if render:
        dest.mkdir(parents=True, exist_ok=True)
        assert dest.resolve().is_relative_to(TEMP.resolve())
        for pattern in ('p[0-9][0-9].png', 'contact-*.png'):
            for previous in dest.glob(pattern):
                previous.unlink()
    all_text = ''
    for i, page in enumerate(doc):
        text = page.get_text(sort=True)
        all_text += text
        chars.append(len(text))
        if '\ufffd' in text:
            errors.append(f'page {i + 1}: replacement glyph')
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                for span in line['spans']:
                    x0, y0, x1, y1 = span['bbox']
                    if x0 < 29 or x1 > page.rect.width - 25 or y0 < 20 or y1 > page.rect.height - 18:
                        errors.append(f'page {i + 1}: bounds {span["text"]!r}')
        if render:
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            pix.save(dest / f'p{i+1:02}.png')
            image = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
            image.thumbnail((310, 438))
            thumb = Image.new('RGB', (330, 466), '#dddddd')
            thumb.paste(image, ((330 - image.width) // 2, 5))
            ImageDraw.Draw(thumb).text((12, 446), f'Page {i+1}', fill='black')
            thumbs.append(thumb)
    compact = re.sub(r'\s', '', all_text)
    for title in expected:
        if re.sub(r'\s', '', title) not in compact:
            errors.append('Missing question heading: ' + title)
    if render:
        for start in range(0, len(thumbs), 6):
            sheet = Image.new('RGB', (990, 932), 'white')
            for j, thumb in enumerate(thumbs[start:start+6]):
                sheet.paste(thumb, ((j % 3) * 330, (j // 3) * 466))
            sheet.save(dest / f'contact-{start // 6 + 1}.png')
    assert not errors, errors
    original = OUT / '原卷' / {'一':'模拟1.pdf','二':'模拟2.pdf','三':'模拟3.pdf'}[number]
    return {'paper': number, 'questions': 23, 'pages': len(doc), 'page_chars': chars,
            'source_pdf_sha256': sha(original), 'answer_md_sha256': sha(source_path(number)),
            'answer_pdf_sha256': sha(pdf), 'render_fingerprint': fingerprint(number), 'errors': errors}


def compile_program(name, code):
    dest = TEMP / '算法验算'
    dest.mkdir(parents=True, exist_ok=True)
    source = dest / (name + '.c')
    target = dest / (name + '.exe')
    source.write_bytes(code.encode('utf-8'))
    gcc = Path('D:/Program Files/mingw64/bin/gcc.exe')
    subprocess.run([str(gcc), '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                    str(source), '-o', str(target)], check=True, capture_output=True)
    return target


def run_program(path, data=''):
    return subprocess.run([str(path)], input=data, text=True, encoding='utf-8',
                          capture_output=True, check=True).stdout


def check_algorithms():
    blocks = {}
    for number in '一二三':
        md = source_path(number).read_text(encoding='utf-8').split('## 四、', 1)[1]
        blocks[number] = re.findall(r'```c\n(.*?)```', md, re.S)
        assert len(blocks[number]) == 2
    header = '#include <assert.h>\n#include <stdlib.h>\n#include <stdio.h>\n#define MAXV 32\n'
    results = []
    expr_test = r'''
int main(void) {
    BTree a={"a",0,0},b={"b",0,0},c={"c",0,0},d={"d",0,0};
    BTree neg={"-",0,&d},ab={"+",&a,&b},mul={"*",&c,&neg};
    BTree root={"*",&ab,&mul}; Infix(&root); puts("");
    BTree ab2={"*",&a,&b},cd={"-",&c,&d},neg2={"-",0,&cd};
    BTree root2={"+",&ab2,&neg2}; Infix(&root2); puts("");
    Infix(0); return 0;
}
'''
    exe = compile_program('M1-expression', header + blocks['一'][0] + expr_test)
    assert run_program(exe).splitlines() == ['(a+b)*(c*(-d))', '(a*b)+(-(c-d))']
    results.append('M1 expression: both original examples and null input')
    graph_type = 'typedef struct {int numVertices,numEdges; char VerticesList[MAXV]; int Edge[MAXV][MAXV];} MGraph;\n'
    euler_test = r'''
static int trail(int u,int mask,int all,int n,int edges[][2],int m){
    if(mask==all)return 1;
    for(int k=0;k<m;k++)if(!(mask&(1<<k))){
        int v=-1;
        if(edges[k][0]==u)v=edges[k][1];
        else if(edges[k][1]==u)v=edges[k][0];
        if(v>=0&&trail(v,mask|(1<<k),all,n,edges,m))return 1;
    }
    return 0;
}
int main(void){
    int tested=0;
    for(int n=2;n<=4;n++){
        int pairs[6][2],cnt=0;
        for(int i=0;i<n;i++)for(int j=i+1;j<n;j++){pairs[cnt][0]=i;pairs[cnt++][1]=j;}
        for(int mask=1;mask<(1<<cnt);mask++){
            MGraph g={0};g.numVertices=n;int edges[6][2],m=0;
            for(int k=0;k<cnt;k++)if(mask&(1<<k)){
                int u=pairs[k][0],v=pairs[k][1];g.Edge[u][v]=g.Edge[v][u]=1;
                edges[m][0]=u;edges[m++][1]=v;
            }
            int seen[4]={1,0,0,0};
            for(int t=0;t<n;t++)for(int i=0;i<n;i++)for(int j=0;j<n;j++)if(seen[i]&&g.Edge[i][j])seen[j]=1;
            int connected=1;for(int i=0;i<n;i++)if(!seen[i])connected=0;
            if(!connected)continue;
            int exists=0;for(int u=0;u<n;u++)if(trail(u,0,(1<<m)-1,n,edges,m))exists=1;
            assert(isExistEL(g)==exists);tested++;
        }
    }
    printf("%d\n",tested);return 0;
}
'''
    exe = compile_program('M1-euler', header + graph_type + blocks['一'][1] + euler_test)
    results.append('M1 Euler: all ' + run_program(exe).strip() + ' connected simple graphs on 2-4 vertices; edge-trail enumeration oracle')
    deletion_test = r'''
static int cmp(const void*a,const void*b){int x=*(const int*)a,y=*(const int*)b;return(x>y)-(x<y);}
int main(void){
    unsigned seed=23;
    for(int test=0;test<600;test++){
        int source[32],n=test%26;for(int i=0;i<n;i++){seed=seed*1664525u+1013904223u;source[i]=(int)(seed%11)-5;}
        qsort(source,n,sizeof(int),cmp);
        for(int x=-6;x<=6;x++)for(int y=-6;y<=6;y++){
            int a[32],want[32],len=n,k=0;
            for(int i=0;i<n;i++){a[i]=source[i];if(x>y||source[i]<x||source[i]>y)want[k++]=source[i];}
            int removed=DeleteRange(a,&len,x,y);assert(len==k&&removed==n-k);
            for(int i=0;i<k;i++)assert(a[i]==want[i]);
        }
    }
    puts("PASS");return 0;
}
'''
    exe = compile_program('M2-delete-range', header + blocks['二'][0] + deletion_test)
    assert run_program(exe).strip() == 'PASS'
    results.append('M2 deletion: 101400 sorted-array interval cases including repeats and empty/reversed ranges')
    path_driver = r'''
int main(void){
    int tests;assert(scanf("%d",&tests)==1);
    for(int c=0;c<tests;c++){
        ALGraph g={0};int s,t;assert(scanf("%d%d%d",&g.n,&s,&t)==3);
        ArcNode nodes[MAXV*MAXV];int used=0;ArcNode **tails[MAXV];
        for(int u=0;u<g.n;u++)tails[u]=&g.first[u];
        for(int u=0;u<g.n;u++)for(int v=0;v<g.n;v++){
            int edge;assert(scanf("%d",&edge)==1);if(edge){nodes[used]=(ArcNode){v,0};*tails[u]=&nodes[used];tails[u]=&nodes[used++].nextarc;}
        }
        printf("CASE %d\n",c);AllSimplePaths(&g,s,t);
    }
    return 0;
}
'''
    exe = compile_program('M2-simple-paths', header + blocks['二'][1] + path_driver)
    rng = random.Random(802)
    cases, expected = [], []
    for case in range(50):
        n = case % 6 + 1; s, t = rng.randrange(n), rng.randrange(n)
        matrix = [[int(u != v and rng.random() < .4) for v in range(n)] for u in range(n)]
        if case % 2:
            for u in range(n):
                for v in range(u): matrix[u][v] = matrix[v][u]
        paths = set()
        def search(u, path):
            if u == t:
                paths.add(tuple(path)); return
            for v in range(n):
                if matrix[u][v] and v not in path: search(v, path + [v])
        search(s, [s]); expected.append(paths)
        cases.append(f'{n} {s} {t}\n' + '\n'.join(' '.join(map(str,r)) for r in matrix))
    output = run_program(exe, str(len(cases)) + '\n' + '\n'.join(cases)).splitlines()
    actual = []
    for line in output:
        if line.startswith('CASE '): actual.append([])
        else: actual[-1].append(tuple(map(int,line.split())))
    assert len(actual) == len(expected)
    for got,want in zip(actual,expected): assert set(got) == want and len(got) == len(want)
    results.append('M2 all simple paths: 50 directed/undirected cyclic/disconnected cases, exact path-set oracle')
    lca_test = r'''
int main(void){
    for(int shape=0;shape<3;shape++)for(int n=1;n<=24;n++){
        Node nodes[24]={0};int parent[24];parent[0]=-1;
        for(int i=0;i<n;i++)nodes[i].INFO=7;
        for(int i=1;i<n;i++){
            int p=shape==0?(i-1)/2:i-1;parent[i]=p;
            if(shape==0){if(i%2)nodes[p].LLINK=&nodes[i];else nodes[p].RLINK=&nodes[i];}
            else if(shape==1)nodes[p].LLINK=&nodes[i];else nodes[p].RLINK=&nodes[i];
        }
        for(int p=0;p<n;p++)for(int q=0;q<n;q++){
            int marked[24]={0};for(int k=p;k>=0;k=parent[k])marked[k]=1;
            int want=q;while(!marked[want])want=parent[want];
            Node *r=0;ANCESTOR(&nodes[0],&nodes[p],&nodes[q],&r);assert(r==&nodes[want]);
        }
    }
    puts("PASS");return 0;
}
'''
    exe = compile_program('M3-lca', header + blocks['三'][0] + lca_test)
    assert run_program(exe).strip() == 'PASS'
    results.append('M3 LCA: all node pairs in complete/left-chain/right-chain trees of sizes 1-24, duplicated values')
    topo_driver = path_driver.replace('ALGraph g={0};int s,t;', 'Graph g={0};int s,t;')
    topo_driver = topo_driver.replace('ArcNode nodes[MAXV*MAXV];int used=0;ArcNode **tails[MAXV];', 'Arc nodes[MAXV*MAXV];int used=0;Arc **tails[MAXV];')
    topo_driver = topo_driver.replace('(ArcNode){v,0}', '(Arc){v,0}').replace('.nextarc', '.next')
    topo_driver = topo_driver.replace('AllSimplePaths(&g,s,t);', 'int ok=TopoDFS(&g);printf("STATUS %d\\n",ok);')
    exe = compile_program('M3-topological-dfs', header + blocks['三'][1] + topo_driver)
    cases, matrices, acyclic = [], [], []
    for case in range(50):
        n = case % 8 + 1
        matrix = [[int((u < v if case % 2 == 0 else u != v) and rng.random() < .35)
                   for v in range(n)] for u in range(n)]
        if case % 11 == 0: matrix[0][0] = 1
        deg = [sum(matrix[u][v] for u in range(n)) for v in range(n)]
        queue = [v for v in range(n) if not deg[v]]
        for u in queue:
            for v in range(n):
                if matrix[u][v]:
                    deg[v] -= 1
                    if deg[v] == 0: queue.append(v)
        acyclic.append(len(queue) == n); matrices.append(matrix)
        cases.append(f'{n} 0 0\n' + '\n'.join(' '.join(map(str,r)) for r in matrix))
    lines = run_program(exe, str(len(cases)) + '\n' + '\n'.join(cases)).splitlines()
    records = []
    for line in lines:
        if line.startswith('CASE '): records.append([])
        else: records[-1].append(line)
    for rows,matrix,valid in zip(records,matrices,acyclic):
        assert rows[-1] == 'STATUS ' + str(int(valid))
        if not valid: assert len(rows) == 1
        else:
            order = list(map(int,rows[0].split())); n=len(matrix)
            assert len(order) == n and set(order) == set(range(n))
            pos = {v:i for i,v in enumerate(order)}
            assert all(pos[u] < pos[v] for u in range(n) for v in range(n) if matrix[u][v])
    results.append('M3 DFS topo: 50 DAG/cyclic/self-loop/disconnected cases, Kahn cycle oracle and edge-order checks')
    return results


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser()
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--algorithms', action='store_true')
    args = parser.parse_args()
    algorithms = check_algorithms() if args.algorithms else []
    papers = [check_pdf(number, args.render) for number in '一二三']
    result = {'papers':papers, 'algorithms':algorithms, 'figure_source_sha256':sha(FIGURES)}
    if args.algorithms and args.render:
        (OUT / '审查/模拟卷成卷核对.json').write_bytes(
            json.dumps(result,ensure_ascii=False,indent=2).encode('utf-8'))
    print(json.dumps(result,ensure_ascii=False,indent=2))
