"""Independent, deterministic checks for papers 5 and 6 answer audit."""
from __future__ import annotations

import bisect
import heapq
import itertools
import json
import re
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DIAGRAMS = json.loads((ROOT / "资料整理/六套模拟卷成稿/答案配图源稿.json").read_text(encoding="utf-8"))
log = {}


def check(key, got, expected):
    assert got == expected, f"{key}: got={got!r}, expected={expected!r}"
    log[key] = got


def bst_insert(root, x):
    if root is None:
        return [x, None, None]
    bst_insert_ref = root
    while True:
        side = 1 if x < bst_insert_ref[0] else 2
        if bst_insert_ref[side] is None:
            bst_insert_ref[side] = [x, None, None]
            return root
        bst_insert_ref = bst_insert_ref[side]


def traverse(t, order):
    if t is None:
        return []
    x, left, right = t
    return (traverse(left, order) + [x] + traverse(right, order) if order == "in" else
            [x] + traverse(left, order) + traverse(right, order) if order == "pre" else
            traverse(left, order) + traverse(right, order) + [x])


def depths(t, depth=1):
    if t is None:
        return []
    return [depth] + depths(t[1], depth + 1) + depths(t[2], depth + 1)


def mid_tree(lo, hi):
    if lo > hi:
        return None
    mid = (lo + hi) // 2
    return [mid, mid_tree(lo, mid - 1), mid_tree(mid + 1, hi)]


def huffman(weights):
    heap = [(w, (ch,)) for ch, w in weights.items()]
    heapq.heapify(heap)
    merges = []
    while len(heap) > 1:
        a, ca = heapq.heappop(heap)
        b, cb = heapq.heappop(heap)
        merges.append(a + b)
        heapq.heappush(heap, (a + b, ca + cb))
    return merges


def hash_insert(keys, m, stepf):
    table = [None] * m
    probes = []
    for x in keys:
        k = 0
        while True:
            p = stepf(x, k) % m
            k += 1
            if table[p] is None:
                table[p] = x
                probes.append(k)
                break
            assert k <= m
    return table, probes


def topo_count(v, edges):
    ans = 0
    for perm in itertools.permutations(range(v)):
        loc = {x: i for i, x in enumerate(perm)}
        if all(loc[a] < loc[b] for a, b in edges):
            ans += 1
    return ans


def avl_insert(root, key):
    def h(node):
        return 0 if node is None else 1 + max(h(node[1]), h(node[2]))
    def rot_right(y):
        x = y[1]
        y[1] = x[2]
        x[2] = y
        return x
    def rot_left(x):
        y = x[2]
        x[2] = y[1]
        y[1] = x
        return y
    if root is None:
        return [key, None, None]
    side = 1 if key < root[0] else 2
    root[side] = avl_insert(root[side], key)
    balance = h(root[1]) - h(root[2])
    if balance > 1:
        if key > root[1][0]:
            root[1] = rot_left(root[1])
        return rot_right(root)
    if balance < -1:
        if key < root[2][0]:
            root[2] = rot_right(root[2])
        return rot_left(root)
    return root


def aoe(v, edges):
    out = [[] for _ in range(v)]
    indeg = [0] * v
    for u, w, d in edges:
        out[u].append((w, d)); indeg[w] += 1
    q = deque(i for i in range(v) if indeg[i] == 0)
    topo = []
    while q:
        u = q.popleft(); topo.append(u)
        for w, _ in out[u]:
            indeg[w] -= 1
            if indeg[w] == 0: q.append(w)
    assert len(topo) == v
    ve = [0] * v
    for u in topo:
        for w, d in out[u]: ve[w] = max(ve[w], ve[u] + d)
    vl = [ve[topo[-1]]] * v
    for u in reversed(topo):
        for w, d in out[u]: vl[u] = min(vl[u], vl[w] - d)
    return ve, vl, [ve[u] for u, _, _ in edges], [vl[w] - d for _, w, d in edges]


def dijkstra(v, edges, src):
    adj = [[] for _ in range(v)]
    for a,b,w in edges: adj[a].append((b,w)); adj[b].append((a,w))
    d = [float("inf")] * v; d[src] = 0
    pq = [(0,src)]
    while pq:
        du,u = heapq.heappop(pq)
        if du != d[u]: continue
        for w,c in adj[u]:
            if du+c < d[w]: d[w]=du+c; heapq.heappush(pq,(d[w],w))
    return d


def kruskal(v, edges):
    parent = list(range(v))
    def find(x):
        while parent[x] != x: x = parent[x]
        return x
    chosen = []; total = 0
    for u,w,c in sorted(edges, key=lambda e: e[2]):
        a,b=find(u),find(w)
        if a != b:
            parent[a]=b; chosen.append((u,w,c)); total += c
    return chosen,total


# Paper 5, II.
a = [6,2,5,1,4,3,7]; swaps=0; passes=[]
for end in (6,5):
    for j in range(end):
        if a[j]>a[j+1]: a[j],a[j+1]=a[j+1],a[j]; swaps+=1
    passes.append(tuple(a))
check("S5-II01", (passes,swaps), ([(2,5,1,4,3,6,7),(2,1,4,3,5,6,7)],8))
p = "abcabca"
next_vals = [0]
for j in range(2,len(p)+1):
    prefix = p[:j-1]
    maxlen = max((k for k in range(1,len(prefix)) if prefix[:k]==prefix[-k:]), default=0)
    next_vals.append(maxlen+1)
check("S5-II04", next_vals, [0,1,1,1,2,3,4])
check("S5-II07", topo_count(6,[(0,2),(0,3),(1,3),(1,4),(2,5),(3,5),(4,5)]),16)
arr=list(range(2,31,2)); target=26; lo=0; hi=len(arr)-1; mids=[]
while lo<=hi:
    m=(lo+hi)//2; mids.append(m+1)
    if arr[m]==target:break
    if arr[m]<target:lo=m+1
    else:hi=m-1
check("S5-II08",mids,[8,12,14,13])
h=[3,7,5,10,9,8];heapq.heapify(h);heapq.heappush(h,2)
check("S5-II09",h,[2,7,3,10,9,8,5])
check("S5-I01-work8",sum(8 for _ in range(3)),24)
check("S5-II05-columns",((246-200)//2-3)//2,10)
check("S5-II06-nodes",8+3+(8-1),18)
check("S5-II10-leaves",(217+1)//2,109)

# Paper 5, III and diagram structures.
t=DIAGRAMS["S5-III01"][0]["tree"]
check("S5-III01-pre",traverse(t,"pre"),list("ABDECFG"))
check("S5-III01-in",traverse(t,"in"),list("DBEAFCG"))
check("S5-III01-post",traverse(t,"post"),list("DEBFGCA"))
t=mid_tree(1,10)
keys=[5,12,18,23,31,42,57,66,74,89]
def map_indices(node):
    if node is None: return None
    return [keys[node[0]-1],map_indices(node[1]),map_indices(node[2])]
check("S5-III02-diagram",map_indices(t),DIAGRAMS["S5-III02"][0]["tree"])
check("S5-III02-ASL",sum(depths(t)),29)
check("S5-III03-old-merges",huffman(dict(zip("ABCDEF",(2,4,7,10,15,25)))),[6,13,23,38,63])
check("S5-III03-new-merges",huffman(dict(zip("ABCDEF",(9,4,7,10,15,25)))),[11,19,26,44,70])
check("S5-III03-old-WPL",sum(huffman(dict(zip("ABCDEF",(2,4,7,10,15,25))))),143)
check("S5-III03-new-WPL",sum(huffman(dict(zip("ABCDEF",(9,4,7,10,15,25))))),170)
def codes_from_diagram(t, prefix=""):
    if t[1] is None and t[2] is None:
        return {str(t[0]).split(":")[0]: prefix}
    result = {}
    result.update(codes_from_diagram(t[1], prefix+"0"))
    result.update(codes_from_diagram(t[2], prefix+"1"))
    return result
check("S5-III03-original-A-length",len(codes_from_diagram(DIAGRAMS["S5-III03"][0]["tree"])["A"]),5)
for index, weights, wpl in [(0,dict(zip("ABCDEF",(2,4,7,10,15,25))),143),(1,dict(zip("ABCDEF",(9,4,7,10,15,25))),170)]:
    codes=codes_from_diagram(DIAGRAMS["S5-III03"][index]["tree"])
    check(f"S5-III03-diagram-{index}-WPL",sum(weights[ch]*len(code) for ch,code in codes.items()),wpl)
bst=None
for x in (40,20,60,10,30,50,70):bst=bst_insert(bst,x)
check("S5-III04-diagram",bst,DIAGRAMS["S5-III04"][0]["tree"])
check("S5-III04-ASL",sum(depths(bst)),17)
table,probes=hash_insert((22,1,13,11,24,35,46),11,lambda x,k:x%11 + k*(1+x%10))
check("S5-III05-table",table,[22,1,13,None,11,None,None,24,35,46,None])
check("S5-III05-probes",probes,[1,1,1,3,2,2,2])
graph={0:[1,2],1:[0,2],2:[0,1],3:[4],4:[3,5],5:[4],6:[]}
def forest_traverse(mode):
    visited=set(); seq=[]; edges=[]
    for start in graph:
        if start in visited:continue
        if mode=="BFS":
            q=deque([start]);visited.add(start);seq.append(start)
            while q:
                u=q.popleft()
                for w in graph[u]:
                    if w not in visited:visited.add(w);seq.append(w);edges.append((u,w));q.append(w)
        else:
            def visit(u):
                visited.add(u);seq.append(u)
                for w in graph[u]:
                    if w not in visited:edges.append((u,w));visit(w)
            visit(start)
    return seq,edges
check("S5-III06-DFS",forest_traverse("DFS"),([0,1,2,3,4,5,6],[(0,1),(1,2),(3,4),(4,5)]))
check("S5-III06-BFS",forest_traverse("BFS"),([0,1,2,3,4,5,6],[(0,1),(0,2),(3,4),(4,5)]))
records=[("a","C",2),("b","A",1),("c","B",2),("d","A",2),("e","B",1),("f","A",1)]
by2=sorted(records,key=lambda z:z[2]);then1=sorted(by2,key=lambda z:z[1]);by1=sorted(records,key=lambda z:z[1]);then2=sorted(by1,key=lambda z:z[2])
check("S5-III07",([[x[0] for x in seq] for seq in (by2,then1,then2)]),[list("befacd"),list("bfdeca"),list("bfedca")])

# Paper 6, II and III.
def stack_permutations(n):
    ans=set()
    def rec(nextin, stack, out):
        if len(out)==n:ans.add(tuple(out));return
        if nextin<=n:rec(nextin+1,stack+(nextin,),out)
        if stack:rec(nextin,stack[:-1],out+(stack[-1],))
    rec(1,(),());return ans
check("S6-II03-stackcount",sum(p[0]==3 for p in stack_permutations(4)),3)
check("S6-II01-queuecount",(2-5)%7,4)
check("S6-II02-address",100+4*(2*5+3),152)
text="ababa";pat="aba";matches=[];comparisons=0
for i in range(len(text)-len(pat)+1):
    for j in range(len(pat)):
        comparisons+=1
        if text[i+j]!=pat[j]:break
    else:matches.append(i)
check("S6-II04",(matches,comparisons),([0,2],7))
check("S6-II06",(13-7)+1,7)
check("S6-II07",(2**4-1)+2*(2**3-2),27)
heap=[2,7,4,9,8,6];heapq.heapify(heap);heapq.heappush(heap,1)
check("S6-II08",heap,[1,7,2,9,8,6,4])
check("S6-II09",2*18-(18-1),19)
check("S6-II10",len(bin(180))-2,8)
check("S6-III01-merges",huffman(dict(zip("ABCDEF",(3,5,7,11,13,18)))),[8,15,24,33,57])
check("S6-III01-WPL",sum(huffman(dict(zip("ABCDEF",(3,5,7,11,13,18))))),137)
check("S6-III01-diagram-codes",codes_from_diagram(DIAGRAMS["S6-III01"][0]["tree"]),dict(zip("ABCDEF",("1010","1011","100","00","01","11"))))
forest_edges=sorted((e["u"],e["v"]) for e in DIAGRAMS["S6-III02"][0]["edges"])
check("S6-III02-forest-diagram",forest_edges,sorted({("A","B"),("A","D"),("B","C"),("D","E"),("F","G")}))
check("S6-III03-diagram",mid_tree(1,11),DIAGRAMS["S6-III03"][0]["tree"])
check("S6-III03-ASL",sum(depths(mid_tree(1,11))),33)
bst=None;avl=None
for x in (30,10,20,50,40,60,70):
    bst=bst_insert(bst,x); avl=avl_insert(avl,x)
check("S6-III04-BST-diagram",bst,DIAGRAMS["S6-III04"][0]["tree"])
check("S6-III04-AVL-diagram",avl,DIAGRAMS["S6-III04"][1]["tree"])
check("S6-III04-binary-diagram",mid_tree(1,7),DIAGRAMS["S6-III04"][2]["tree"])
check("S6-III04-ASLs",(sum(depths(bst)),sum(depths(avl)),sum(depths(mid_tree(1,7)))),(18,17,17))
aoe_edges=[(0,1,2),(0,2,3),(1,3,4),(2,3,1),(2,4,4),(3,5,3),(4,5,2),(1,4,1)]
check("S6-III05",aoe(6,aoe_edges),([0,2,3,6,7,9],[0,2,3,6,7,9],[0,0,2,3,3,6,7,2],[0,0,2,5,3,6,7,6]))
edges=[(0,1,2),(0,2,3),(1,2,2),(1,3,5),(2,3,3),(2,4,6),(3,4,1)]
check("S6-III06-MST-weight",kruskal(5,edges)[1],8)
check("S6-III06-distances",dijkstra(5,edges,0),[0,2,3,6,7])
table,probes=hash_insert((18,29,40,7,22,35,46),11,lambda x,k:x+k)
check("S6-III07-table",table,[22,None,35,46,None,None,None,18,29,40,7])
check("S6-III07-probes",probes,[1,2,3,4,1,1,2])

# Exact subpart point allocation and coverage; IV points are printed at question header.
for paper in (5,6):
    source=json.loads((ROOT/f"资料整理/六套模拟卷成稿/试题源稿/第{paper}套.json").read_text(encoding="utf-8"))
    answer=json.loads((ROOT/f"资料整理/六套模拟卷成稿/答案源稿/第{paper}套.json").read_text(encoding="utf-8"))
    assert [q["id"] for q in source["questions"]]==[q["id"] for q in answer["questions"]]
    for q in source["questions"]:
        pts=sum(int(x) for x in re.findall(r"（(\d+)分）",q["content"]))
        if q["section"] in ("I","II","III"):
            check(f"{q['id']}-points",pts,q["points"])
        else:
            check(f"{q['id']}-points",(pts,q["points"]),(0,{1:8,2:10,3:12}[q["number"]]))

OUT=Path(__file__).with_name("oracle56.json")
OUT.write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding="utf-8")
print(f"PASS {len(log)} independent checks -> {OUT}")
