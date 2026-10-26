import ctypes as ct
import itertools
import json
import random
import re
import subprocess
from pathlib import Path

ROOT = Path('_tmp/exam_final/author34')
GCC = r'D:/Program Files/mingw64/bin/gcc.exe'
random.seed(80234)
answers = {}
for paper in (3, 4):
    p = Path(f'资料整理/六套模拟卷成稿/答案源稿/第{paper}套.json')
    answers.update({q['id']: q for q in json.loads(p.read_text(encoding='utf-8'))['questions']})

def lib(id):
    m = re.search(r'```c\n(.*?)\n```', answers[id]['content'], re.S)
    assert m, id
    src = ROOT / f'{id}.c'
    dll = ROOT / f'{id}.dll'
    src.write_text(m.group(1) + '\n', encoding='utf-8')
    p = subprocess.run([GCC, '-std=c11', '-Wall', '-Wextra', '-Werror', '-O1', '-shared', str(src), '-o', str(dll)], capture_output=True, text=True)
    assert p.returncode == 0, (id, p.stderr)
    return ct.CDLL(str(dll.resolve()))

def run_merge():
    L = lib('S3-IV01')
    class Node(ct.Structure): pass
    Node._fields_ = [('key', ct.c_int), ('next', ct.POINTER(Node))]
    Ptr = ct.POINTER(Node)
    f = L.mergeThree; f.argtypes = [Ptr, Ptr, Ptr]; f.restype = Ptr
    for _ in range(300):
        lists = [sorted(random.randrange(-5, 6) for _ in range(random.randrange(0, 8))) for _ in range(3)]
        keep = []; heads = []; expected_addr = set()
        for seq in lists:
            nodes = [Node(v, Ptr()) for v in seq]; keep.extend(nodes)
            for i in range(len(nodes)-1): nodes[i].next = ct.pointer(nodes[i+1])
            heads.append(ct.pointer(nodes[0]) if nodes else Ptr())
            expected_addr.update(ct.addressof(n) for n in nodes)
        p = f(*heads); got = []; got_addr = set()
        while p:
            address = ct.addressof(p.contents)
            assert address not in got_addr, 'cycle'
            got_addr.add(address); got.append(p.contents.key); p = p.contents.next
        assert got == sorted(sum(lists, [])) and got_addr == expected_addr
    return '300随机三链：键序/原结点身份/空链/并列键通过'

def run_marked():
    L = lib('S3-IV02')
    class Node(ct.Structure): pass
    Ptr = ct.POINTER(Node)
    Node._fields_ = [('data', ct.c_int), ('mark', ct.c_bool), ('left', Ptr), ('right', Ptr)]
    f = L.longestMarkedPath; f.argtypes = [Ptr, ct.POINTER(Ptr), ct.POINTER(ct.c_int)]; f.restype = ct.c_bool
    for _ in range(300):
        n = random.randrange(0, 15)
        nodes = [Node(i, bool(random.randrange(2)), Ptr(), Ptr()) for i in range(n)]
        open_slots = [(i, side) for i in range(n) for side in ('left','right')]
        for i in range(1,n):
            choices = [(j,side) for j,side in open_slots if j < i]
            j,side = random.choice(choices)
            setattr(nodes[j], side, ct.pointer(nodes[i]))
            open_slots.remove((j,side))
        expected = []
        def walk(p, path, marked):
            if not p: return
            q = p.contents; path = path+[q.data]; marked |= q.mark
            if not q.left and not q.right:
                if marked: expected.append(path)
            else:
                walk(q.left,path,marked); walk(q.right,path,marked)
        root = ct.pointer(nodes[0]) if n else Ptr()
        walk(root,[],False)
        out = (Ptr * max(1,n))(); outlen = ct.c_int(-1)
        ok = bool(f(root,out,ct.byref(outlen)))
        if expected:
            got = [out[i].contents.data for i in range(outlen.value)]
            assert ok and got in expected and outlen.value == max(map(len,expected))
        else:
            assert not ok and outlen.value == 0
    return '300随机二叉树：最长合格根叶路径、空树/无标记/并列通过'

def run_count():
    L = lib('S3-IV03')
    Row = ct.c_int * 12; Mat = Row * 12
    f = L.countPaths; f.argtypes = [ct.POINTER(Row),ct.c_int,ct.c_int,ct.c_int,ct.c_int]; f.restype = ct.c_int
    for _ in range(400):
        V = random.randrange(1,9); g = Mat()
        for u in range(V):
            for v in range(u+1,V):
                if random.randrange(2): g[u][v]=g[v][u]=1
        s=random.randrange(V);t=random.randrange(V);k=random.randrange(V)
        def ref(u,depth,seen):
            if depth==k: return int(u==t)
            if u==t: return 0
            return sum(ref(v,depth+1,seen|{v}) for v in range(V) if g[u][v] and v not in seen)
        assert f(g,V,s,t,k) == ref(s,0,{s})
    return '400随机无向图：恰k边简单路径数与独立DFS一致（含s=t、k=0）'

def run_delete():
    m = re.search(r'```c\n(.*?)\n```', answers['S4-IV01']['content'], re.S)
    src = ROOT/'S4-IV01-test.c'; exe = ROOT/'S4-IV01-test.exe'
    harness = r'''
#include <assert.h>
#include <stdio.h>
int main(void) {
  unsigned seed = 12345;
  for (int trial=0; trial<2000; ++trial) {
    seed=seed*1664525u+1013904223u; int n=(int)(seed%21);
    int values[21], kept[21], kc=0;
    Node *tail=NULL;
    for (int i=0;i<n;++i) {
      seed=seed*1664525u+1013904223u;
      values[i]=(int)(seed%11)-5;
      Node *p=malloc(sizeof *p); assert(p); p->key=values[i];
      if (!tail) { p->next=p; tail=p; }
      else { p->next=tail->next; tail->next=p; tail=p; }
    }
    seed=seed*1664525u+1013904223u; int a=(int)(seed%11)-5;
    seed=seed*1664525u+1013904223u; int b=(int)(seed%11)-5;
    if (a>b) {int z=a;a=b;b=z;}
    for(int i=0;i<n;++i) if(values[i]<a || values[i]>b) kept[kc++]=values[i];
    int removed=deleteRange(&tail,n,a,b);
    assert(removed==n-kc);
    if(kc==0) assert(tail==NULL);
    else {
      assert(tail!=NULL); Node *p=tail->next;
      for(int i=0;i<kc;++i) { assert(p->key==kept[i]); p=p->next; }
      assert(p==tail->next);
      p=tail->next;
      for(int i=0;i<kc;++i) {Node *next=p->next;free(p);p=next;}
    }
  }
  puts("2000 random circular lists passed"); return 0;
}
'''
    src.write_text(m.group(1)+'\n'+harness,encoding='utf-8')
    p=subprocess.run([GCC,'-std=c11','-Wall','-Wextra','-Werror','-O1',str(src),'-o',str(exe)],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    p=subprocess.run([str(exe.resolve())],capture_output=True,text=True)
    assert p.returncode==0,(p.stdout,p.stderr)
    return p.stdout.strip()

def run_closest():
    L=lib('S4-IV02')
    class Node(ct.Structure): pass
    Ptr=ct.POINTER(Node)
    Node._fields_=[('key',ct.c_int),('left',Ptr),('right',Ptr)]
    f=L.closestKey;f.argtypes=[Ptr,ct.c_int,ct.POINTER(ct.c_int)];f.restype=ct.c_bool
    for _ in range(400):
        n=random.randrange(0,25);keys=random.sample(range(-100,101),n);nodes=[Node(k,Ptr(),Ptr()) for k in keys]
        root=Ptr()
        for node in nodes:
            if not root:root=ct.pointer(node);continue
            p=root
            while True:
                side='left' if node.key<p.contents.key else 'right'
                q=getattr(p.contents,side)
                if q:p=q
                else:setattr(p.contents,side,ct.pointer(node));break
        x=random.randrange(-110,111);out=ct.c_int(987654)
        ok=bool(f(root,x,ct.byref(out)))
        if n:assert ok and out.value==min(keys,key=lambda k:(abs(k-x),k))
        else:assert not ok and out.value==987654
    # int endpoints and tie
    a=Node(-2147483647,Ptr(),Ptr()); b=Node(2147483647,Ptr(),Ptr()); a.right=ct.pointer(b)
    out=ct.c_int(0);assert f(ct.pointer(a),0,ct.byref(out)) and out.value==-2147483647
    return '400随机BST及int极值/并列/空树，与全键比较一致'

def run_repair():
    L=lib('S4-IV03')
    class Edge(ct.Structure):_fields_=[('u',ct.c_int),('v',ct.c_int),('weight',ct.c_int)]
    Row=ct.c_int*100;Mat=Row*100
    f=L.repairMST;f.argtypes=[ct.POINTER(Row),ct.c_int,ct.POINTER(Edge),ct.c_int,ct.POINTER(Edge),ct.POINTER(ct.c_longlong)];f.restype=ct.c_bool
    INF=2147483647
    def kruskal(V,edges):
        p=list(range(V))
        def find(x):
            while p[x]!=x:x=p[x]
            return x
        ans=[]
        for u,v,w in sorted(edges,key=lambda z:z[2]):
            a,b=find(u),find(v)
            if a!=b:p[a]=b;ans.append((u,v,w))
            if len(ans)==V-1:break
        return ans if len(ans)==V-1 else None
    tested=0
    for _ in range(600):
        V=random.randrange(2,8);edge={}
        for v in range(1,V):
            u=random.randrange(v);edge[(u,v)]=random.randrange(0,20)
        for u in range(V):
            for v in range(u+1,V):
                if (u,v) not in edge and random.randrange(3)==0:edge[(u,v)]=random.randrange(0,20)
        edges=[(u,v,w) for (u,v),w in edge.items()]
        tree=kruskal(V,edges);assert tree
        idx=random.randrange(V-1);a,b,_=tree[idx]
        mat=Mat()
        for u in range(V):
            for v in range(V):mat[u][v]=0 if u==v else INF
        for u,v,w in edges:mat[u][v]=mat[v][u]=w
        arr=(Edge*(V-1))(*[Edge(*x) for x in tree]);rep=Edge(-7,-7,-7);total=ct.c_longlong(-123)
        ok=bool(f(mat,V,arr,idx,ct.byref(rep),ct.byref(total)))
        after=[x for x in edges if (x[0],x[1])!=(a,b)]
        optimum=kruskal(V,after)
        if optimum is None:
            assert not ok and (rep.u,rep.v,rep.weight)==(-7,-7,-7) and total.value==-123
        else:
            assert ok and total.value==sum(x[2] for x in optimum)
            assert (rep.u,rep.v,rep.weight) in after
            rebuilt=tree[:idx]+tree[idx+1:]+[(rep.u,rep.v,rep.weight)]
            assert kruskal(V,rebuilt) is not None
        tested+=1
    # 64位总权值、仍在矩阵中的失效边、V=2断连的定向边界。
    mat=Mat()
    for u in range(3):
        for v in range(3):mat[u][v]=0 if u==v else INF
    mat[0][1]=mat[1][0]=INF-2
    mat[1][2]=mat[2][1]=INF-3
    mat[0][2]=mat[2][0]=INF-4
    arr=(Edge*2)(Edge(0,2,INF-4),Edge(1,2,INF-3))
    rep=Edge(-7,-7,-7);total=ct.c_longlong(-123)
    assert f(mat,3,arr,0,ct.byref(rep),ct.byref(total))
    assert (rep.u,rep.v,rep.weight)==(0,1,INF-2)
    assert total.value==(INF-3)+(INF-2)>INF
    mat2=Mat()
    for u in range(2):
        for v in range(2):mat2[u][v]=0 if u==v else 0
    one=(Edge*1)(Edge(0,1,0));rep=Edge(-7,-7,-7);total=ct.c_longlong(-123)
    assert not f(mat2,2,one,0,ct.byref(rep),ct.byref(total))
    assert (rep.u,rep.v,rep.weight)==(-7,-7,-7) and total.value==-123
    return f'{tested}随机带权图+64位权值/V=2定向边界：最优权值、断连输出不变、零权/并列及可用替换边通过'

results = {
    'S3-IV01': run_merge(),
    'S3-IV02': run_marked(),
    'S3-IV03': run_count(),
    'S4-IV01': run_delete(),
    'S4-IV02': run_closest(),
    'S4-IV03': run_repair(),
}
(ROOT/'algorithm_checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for k,v in results.items():print(k,v)
