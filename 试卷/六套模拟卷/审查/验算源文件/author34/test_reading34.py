import json
import re
import subprocess
from pathlib import Path

ROOT=Path('_tmp/exam_final/author34')
BASE=Path('资料整理/六套模拟卷成稿/试题源稿')
GCC=r'D:/Program Files/mingw64/bin/gcc.exe'
fill={
 'S3-I02':['head->next','p->next','q->key < best->key'],
 'S3-I03':['q->rear->next = p','q->rear = q->front','q->front == q->rear'],
 'S3-I04':['g[u][v] && !seen[v]','dfs(v)','!seen[u]'],
 'S4-I02':['pa','free(pa)','pb = pb->next'],
 'S4-I03':['q->count == 4','(q->rear + 1) % 4','--q->count'],
 'S4-I04':['t == NULL','t->left == NULL && t->right == NULL','leafCount(t->left) + leafCount(t->right)'],
}
expected={
 'S3-I01':'n=8, count=32',
 'S3-I02':'(1,-) (2,-) (4,b) (4,a)',
 'S3-I03':'4 7',
 'S3-I04':'components=2',
 'S4-I01':'minimum=16',
 'S4-I03':'first=10',
 'S4-I04':'leaves=3',
}
results={}
for n in (3,4):
    data=json.loads((BASE/f'第{n}套.json').read_text(encoding='utf-8'))
    for q in data['questions']:
        if q['section']!='I':continue
        id=q['id'];m=re.search(r'```c\n(.*?)\n```',q['content'],re.S);assert m,id
        code=m.group(1)
        for i,v in enumerate(fill.get(id,[]),1):
            code=code.replace(f'__{i}__',v)
        assert not re.search(r'__\d+__',code),id
        source=ROOT/f'{id}-filled.c';source.write_text(code+'\n',encoding='utf-8')
        if 'int main' in code:
            exe=ROOT/f'{id}-filled.exe'
            p=subprocess.run([GCC,'-std=c11','-Wall','-Wextra','-Werror','-O1',str(source),'-o',str(exe)],capture_output=True,text=True)
            assert p.returncode==0,(id,p.stderr)
            run=subprocess.run([str(exe.resolve())],capture_output=True,text=True)
            assert run.returncode==0,(id,run.stderr)
            out=run.stdout.strip()
            assert expected[id] in out,(id,out)
            results[id]={'compiled':True,'output':out}
        else:
            p=subprocess.run([GCC,'-std=c11','-Wall','-Wextra','-Werror','-fsyntax-only',str(source)],capture_output=True,text=True)
            assert p.returncode==0,(id,p.stderr)
            results[id]={'compiled':True,'output':'无main，语法编译通过'}
(ROOT/'reading_checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for k,v in results.items():print(k,v['output'].replace('\n',' | '))
