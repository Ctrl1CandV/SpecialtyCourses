"""Fill code blanks independently, compile all eight reading programs, run self-contained ones."""
from __future__ import annotations
import json, re, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
GCC=Path('D:/Program Files/mingw64/bin/gcc.exe')
BLANKS={
 'S5-I02': {'1':'pre->next','2':'p','3':'p->next'},
 'S5-I03': {'1':'CAP','2':'s->top0 + 1 == s->top1','3':'s->top1 == CAP'},
 'S5-I04': {'1':'key % m','2':'(pos + 1) % m'},
 'S6-I02': {'1':'a != NULL || b != NULL','2':'a->key <= b->key'},
 'S6-I03': {'1':'size(q)','2':'p->left == NULL && p->right == NULL'},
 'S6-I04': {'1':'!empty(q)','2':'--indeg[e->to] == 0'},
}
EXPECTED={
 'S5-I01':'2 -> 2\n4 -> 8\n8 -> 24',
 'S5-I02':'3 5 7',
 'S5-I03':'72',
 'S5-I04':'-1 -1 -1 3 -1 -1 -1 7 18 29 -1',
 'S6-I01':'n=65536 x=65536 count=4',
 'S6-I02':'4 3 3 3 2 1',
}
for paper in (5,6):
  source=json.loads((ROOT/f'资料整理/六套模拟卷成稿/试题源稿/第{paper}套.json').read_text(encoding='utf-8'))
  for q in source['questions']:
    qid=q['id']
    if not re.fullmatch(r'S[56]-I\d\d',qid): continue
    c=re.search(r'```c\n(.*?)\n```',q['content'],re.S).group(1)
    for idx,value in BLANKS.get(qid,{}).items():c=c.replace(f'__{idx}__',value)
    assert not re.search(r'__\d+__',c),qid
    path=HERE/f'{qid}-filled.c';path.write_text(c+'\n',encoding='utf-8')
    result=subprocess.run([str(GCC),'-std=c11','-Wall','-Wextra','-Werror','-fsyntax-only',str(path)],capture_output=True,text=True)
    assert result.returncode==0,(qid,result.stderr)
    if qid in EXPECTED:
      exe=HERE/f'{qid}-filled.exe'
      result=subprocess.run([str(GCC),'-std=c11','-Wall','-Wextra','-Werror',str(path),'-o',str(exe)],capture_output=True,text=True)
      assert result.returncode==0,(qid,result.stderr)
      actual=subprocess.run([str(exe)],capture_output=True,text=True,check=True).stdout.strip()
      assert actual==EXPECTED[qid],(qid,actual,EXPECTED[qid])
      print(qid,'compile/run PASS',repr(actual))
    else:print(qid,'C11 syntax PASS; external queue operations per question')
