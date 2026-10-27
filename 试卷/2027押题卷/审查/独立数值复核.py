"""Independent recomputation of all three papers sections II and III.

Reads current JSON; does not import authoring/build helpers. Inputs come from
question text and tree figure data. Assertions compare recomputed values with
current answer text/tables. Run from any working directory with Python 3.
"""
from pathlib import Path
import json,re,heapq,itertools
from fractions import Fraction

BASE=Path(__file__).resolve().parents[1]
Q={q['id']:q for n in (1,2,3) for q in json.loads((BASE/f'源稿/第{n}套.json').read_text(encoding='utf-8'))['questions']}
PASSED=[]
def nums(s):return [int(x) for x in re.findall(r'-?\d+',s)]
def seq(s):return '，'.join(map(str,s))
def contains(q,s):assert s in q['answer'],(q['id'],s)
def row(q,values):contains(q,'|'+'|'.join(map(str,values))+'|')
def finish(q):PASSED.append(q['id'])
def table_edges(c):return [(a,b,int(w)) for a,b,w in re.findall(r'^\|([A-Z])\|([A-Z])\|(\d+)\|$',c,re.M)]
def initial_sequence(c,pattern=r'序列[（(]([^）)]+)[）)]'):return nums(re.search(pattern,c).group(1))

def postfix(tokens):
 st=[];mx=0
 for t in tokens:
  if t in '+-*/':
   b=st.pop();a=st.pop();st.append({'+':lambda:a+b,'-':lambda:a-b,'*':lambda:a*b,'/':lambda:int(a/b)}[t]())
  else:st.append(int(t));mx=max(mx,len(st))
 assert len(st)==1
 return st[0],mx

def genparse(s):
 pos=0
 def value():
  nonlocal pos
  if s[pos]!='(':
   v=s[pos];pos+=1;return v
  pos+=1;a=[]
  while s[pos]!=')':
   a.append(value())
   if s[pos]==',':pos+=1
  pos+=1;return a
 result=value();assert pos==len(s);return result
def gprint(v):return '('+','.join(map(gprint,v))+')' if isinstance(v,list) else v
def geval(expr,L):
 if expr=='L':return L
 op,inner=re.fullmatch(r'(Head|Tail)\((.*)\)',expr).groups();v=geval(inner,L);return v[0] if op=='Head' else v[1:]

def all_stack(n):
 out=[]
 def walk(next_in,st,p):
  if len(p)==n:out.append(tuple(p));return
  if next_in<=n:walk(next_in+1,st+[next_in],p)
  if st:walk(next_in,st[:-1],p+[st[-1]])
 walk(1,[],[]);return out

def revised_fill(q):
 """Independently recompute the revised questions from the current text."""
 id=q['id'];c=q['content']
 if id=='P1-II01':
  limit=int(re.search(r'1≤i≤j≤k≤(\d+)',c).group(1))
  stored=[(i,j,k) for i in range(1,limit+1) for j in range(i,limit+1) for k in range(j,limit+1)]
  target=tuple(map(int,re.findall(r'A\[(\d+)\]\[(\d+)\]\[(\d+)\]',c)[-1]))
  size=int(re.search(r'占(\d+)字节',c).group(1));base=int(re.search(r'地址为(\d+)',c).group(1))
  contains(q,f'{len(stored)}；{base+stored.index(target)*size}。')
 elif id=='P1-II05':
  total=int(re.search(r'有(\d+)个顶点',c).group(1))
  groups=[tuple(map(int,x)) for x in re.findall(r'(\d+)个顶点的度为(\d+)',c)]
  remaining=int(re.search(r'其余顶点的度均为(\d+)',c).group(1))
  degrees=[d for count,d in groups for _ in range(count)]+[remaining]*(total-sum(count for count,d in groups))
  # Havel-Hakimi verifies that the stated simple-graph degrees are realizable.
  pending=degrees[:]
  while pending:
   pending.sort(reverse=True);d=pending.pop(0)
   assert 0<=d<=len(pending)
   for k in range(d):pending[k]-=1;assert pending[k]>=0
  removed=int(re.search(r'删除任意一个度为(\d+)',c).group(1));edge=sum(degrees)//2
  contains(q,f'{edge}；{2*(edge-removed)}。')
 elif id=='P1-II08':
  layers=int(re.search(r'有(\d+)层',c).group(1));maxkey=int(re.search(r'最多(\d+)个关键字',c).group(1));minkey=int(re.search(r'至少(\d+)个关键字',c).group(1));root=int(re.search(r'根恰有(\d+)个关键字',c).group(1))
  low=high=root;ln=hn=root+1
  for level in range(2,layers+1):
   low+=ln*minkey;high+=hn*maxkey
   if level<layers:ln*=minkey+1;hn*=maxkey+1
  contains(q,f'{ln}；{low}；{high}。')
 elif id=='P1-II10':
  pre=re.search(r'先序为([A-Z,]+)',c).group(1).split(',');ino=re.search(r'中序为([A-Z,]+)',c).group(1).split(',')
  def solve(pre,ino):
   if not pre:return [],0
   at=ino.index(pre[0]);lp,lh=solve(pre[1:at+1],ino[:at]);rp,rh=solve(pre[at+1:],ino[at+1:])
   return lp+rp+[pre[0]],1+max(lh,rh)
  post,h=solve(pre,ino);contains(q,','.join(post)+f'；{h}。')
 elif id=='P2-II03':
  arcs=re.findall(r'([A-Z])→([A-Z])',re.search(r'弧集为\{(.*?)\}',c).group(1));vertices=sorted(set(itertools.chain.from_iterable(arcs)))
  valid=[p for p in itertools.permutations(vertices) if all(p.index(u)<p.index(v) for u,v in arcs)]
  prefix=tuple(re.search(r'固定为([A-Z]),([A-Z])',c).groups())
  contains(q,f'{len(valid)}；{sum(p[:2]==prefix for p in valid)}。')
  for p in valid:contains(q,','.join(p))
 elif id=='P2-II05':
  leaf=int(re.search(r'叶结点(\d+)个',c).group(1));one=int(re.search(r'1个孩子的结点(\d+)个',c).group(1));three=int(re.search(r'3个孩子的结点(\d+)个',c).group(1))
  possibilities=[x for x in range(leaf+1) if leaf+one+x+three-1==one+2*x+3*three]
  assert len(possibilities)==1;two=possibilities[0];contains(q,f'{two}；{leaf+one+two+three}。')
 elif id=='P2-II10':
  total,edges=map(int,re.search(r'有(\d+)个顶点、(\d+)条边',c).groups())
  def partitions(n,low=1):
   if n==0:yield [];return
   for first in range(low,n+1):
    for tail in partitions(n-first,first):yield [first]+tail
  counts=[len(p) for p in partitions(total) if total-len(p)<=edges<=sum(x*(x-1)//2 for x in p)]
  contains(q,f'{min(counts)}；{max(counts)}。')
 elif id=='P3-II02':
  edges=re.findall(r'([A-Z])-([A-Z])',re.search(r'边集为\{(.*?)\}',c).group(1));start=re.search(r'从([A-Z])开始',c).group(1);adj={x:[] for x in set(itertools.chain.from_iterable(edges))}
  for u,v in edges:adj[u].append(v);adj[v].append(u)
  order=[];height=0
  def visit(u,depth):
   nonlocal height
   order.append(u);height=max(height,depth)
   for v in sorted(adj[u]):
    if v not in order:visit(v,depth+1)
  visit(start,1);contains(q,','.join(order)+f'；{height}。')
 elif id=='P3-II04':
  assert int(re.search(r'高为(\d+)层',c).group(1))==3
  maximum=int(re.search(r'最多(\d+)个孩子',c).group(1));minimum=int(re.search(r'非根内部结点至少(\d+)个孩子',c).group(1));rootmin=int(re.search(r'根至少(\d+)个孩子',c).group(1));capacity=int(re.search(r'恰存(\d+)条记录',c).group(1));records=int(re.search(r'共(\d+)条记录',c).group(1))
  assert records%capacity==0;leaves=records//capacity
  possible=[]
  for r in range(rootmin,maximum+1):
   for children in itertools.product(range(minimum,maximum+1),repeat=r):
    if sum(children)==leaves:possible.append(r+sum(children))
  contains(q,f'{leaves}；{min(possible)}；{max(possible)}。')
 elif id=='P3-II09':
  pre=re.search(r'先序为([A-Z,]+)',c).group(1).split(',');post=re.search(r'后序为([A-Z,]+)',c).group(1).split(',')
  def solve(pre,post):
   assert pre[0]==post[-1]
   if len(pre)==1:return 1,0
   count=post.index(pre[1])+1
   if count==len(pre)-1:
    ways,two=solve(pre[1:],post[:-1]);return ways*2,two
   a,x=solve(pre[1:count+1],post[:count]);b,y=solve(pre[count+1:],post[count:-1]);return a*b,x+y+1
  ways,two=solve(pre,post);contains(q,f'{ways}；{two}。')
 else:return False
 return True

def fills(n):
 for i in range(1,11):
  q=Q[f'P{n}-II{i:02d}'];c=q['content'];a=q['answer']
  if revised_fill(q):pass
  elif i==1 and n in (1,2):
   dims=[tuple(nums(x)) for x in re.findall(r'\[(-?\d+\.\.-?\d+)\]',c)]
   target=nums(re.findall(r'A((?:\[-?\d+\]){'+str(len(dims))+r'})',c)[-1]);offset=0
   for (low,hi),index in zip(dims,target):offset=offset*(hi-low+1)+index-low
   size=int(re.search(r'占(\d+)字节',c).group(1));base=int(re.search(r'地址为(\d+)',c).group(1));contains(q,str(base+offset*size)+'。')
  elif i==1:
   p=re.findall(r'A\[(-?\d+)\]\[(-?\d+)\]',c);lo=int(re.search(r'\[(-?\d+)\.\.b\]',c).group(1));ad=nums(re.search(r'分别为(\d+)与(\d+)',c).group());size=int(re.search(r'每元素(\d+)字节',c).group(1));width=(ad[1]-ad[0])//((int(p[1][0])-int(p[0][0]))*size);contains(q,f'列数{width}，b={lo+width-1}')
  elif i==2:
   val,mx=postfix(re.search('“([^”]+)”',c).group(1).split());contains(q,f'{val}；{mx}。')
  elif i==3:
   cap=int(re.search(r'长度为(\d+)',c).group(1));front,rear=map(int,re.search(r'初始front=(\d+)、rear=(\d+)',c).groups());size=(rear-front)%cap
   for op,num in re.findall(r'(入队|出队)(\d+)个',c):
    num=int(num)
    if op=='入队':assert size+num<cap;size+=num;rear=(rear+num)%cap
    else:assert size>=num;size-=num;front=(front+num)%cap
   contains(q,f'{front}，{rear}，{size}。')
  elif i==4:
   pat=re.search('“([^”]+)”',c).group(1);ans=[0]
   for j in range(1,len(pat)):
    prefix=pat[:j];match=max([0]+[k for k in range(1,j) if prefix[:k]==prefix[-k:]]);ans.append(match+1)
   contains(q,'next数组为'+seq(ans)+'。')
  elif i==5:
   L=genparse(re.search(r'L=(.+?)，Head',c).group(1));expr=re.findall(r'((?:Head|Tail)\([^=]+\))=____',c)
   out=[gprint(geval(x,L)) for x in expr];contains(q,'；'.join(out)+'。')
  elif i==6 and n==1:
   h=int(re.search(r'高度为(\d+)',c).group(1));leaf=int(re.search(r'倒数第二层有(\d+)',c).group(1));possible=[]
   for total in range(2**(h-1),2**h):
    layer=range(2**(h-2),2**(h-1))
    if sum(2*x>total for x in layer)==leaf:possible.append(total)
   contains(q,f'{min(possible)}；{max(possible)}。')
  elif i==6 and n==2:
   total=int(re.search(r'有(\d+)个结点',c).group(1));r=int(re.search(r'以编号(\d+)为根',c).group(1));desc=[]
   for x in range(1,total+1):
    y=x
    while y>r:y//=2
    if y==r:desc.append(x)
   contains(q,f'{len(desc)}；{sum(2*x>total for x in desc)}。')
  elif i==6:
   empty=int(re.search(r'共有(\d+)个空',c).group(1));right=int(re.search(r'右孩子空指针(\d+)个',c).group(1));two=int(re.search(r'度为2的结点有(\d+)个',c).group(1));leaf=two+1;leftonly=right-leaf;rightonly=empty-right-leaf;contains(q,f'{leftonly}；{rightonly}；{leaf}。')
  elif i==7 and n==1:
   total,edges=map(int,re.search(r'有(\d+)个结点、(\d+)条边',c).groups());left=int(re.search(r'有(\d+)个结点的左',c).group(1));contains(q,f'{total-edges}；{total-left}；{left+1}。')
  elif i==7 and n==2:
   total,edges=map(int,re.search(r'有(\d+)个结点、(\d+)条边',c).groups());nullr=int(re.search(r'共有(\d+)个空右',c).group(1));nonleaf=(total-1)-(total-nullr);contains(q,f'{total-edges}；{nonleaf}；{total-nonleaf}。')
  elif i==7:
   total=int(re.search(r'共有(\d+)个结点',c).group(1));d=nums(re.search(r'分别为(.*?)个，无',c).group(1));roots=total-sum((i+1)*x for i,x in enumerate(d));leaf=total-sum(d);nullr=sum(d)+1;contains(q,f'{roots}；{leaf}；{nullr}。')
  elif i==8 and n==3:
   keys=nums(re.search(r'关键字\((.*?)\)',c).group(1));events=[]
   def insert(t,key):
    if t is None:return Node(key)
    if key<t.k:t.l=insert(t.l,key)
    else:t.r=insert(t.r,key)
    b=height(t.l)-height(t.r)
    if b>1:
     events.append((key,t.k))
     if key>t.l.k:t.l=rotate_left(t.l)
     return rotate_right(t)
    if b< -1:
     events.append((key,t.k))
     if key<t.r.k:t.r=rotate_right(t.r)
     return rotate_left(t)
    return t
   tree=None
   for key in keys:tree=insert(tree,key)
   def zero(t):return 0 if t is None else (height(t.l)==height(t.r))+zero(t.l)+zero(t.r)
   contains(q,f'{events[-1][1]}；{zero(tree)}。')
  elif i==8:
   heap=[None]+nums(re.search(r'存储为\((.*?)\)',c).group(1));ins=nums(re.search(r'依次插入(.*?)，',c).group(1));count=0
   for x in ins:
    heap.append(x);j=len(heap)-1
    while j>1:
     count+=1
     if heap[j//2]<=x:break
     heap[j]=heap[j//2];j//=2
    heap[j]=x
   contains(q,f'{count}次；('+seq(heap[1:])+')')
  elif i==9 and n==1:
   total=int(re.search(r'元素1～(\d+)',c).group(1));cap=int(re.search(r'容量为(\d+)',c).group(1));prefix=nums(re.search(r'依次为(.*?)，',c).group(1));count=0
   for order in all_stack(total):
    if order[:len(prefix)]!=tuple(prefix):continue
    st=[];k=1;maximum=0
    for x in order:
     while not st or st[-1]!=x:st.append(k);k+=1;maximum=max(maximum,len(st))
     st.pop()
    if maximum<=cap:count+=1
   contains(q,f'{count}种。')
  elif i==9 and n==2:
   total=int(re.search(r'元素1～(\d+)',c).group(1));prefix=nums(re.search(r'依次为(.*?)，',c).group(1));count=sum(x[:2]==tuple(prefix) for x in all_stack(total));contains(q,f'{count}种。')
  elif i==9:
   target=nums(re.search(r'出栈序列\((.*?)\)',c).group(1));st=[];k=1;mx=0
   for x in target:
    while not st or st[-1]!=x:st.append(k);k+=1;mx=max(mx,len(st));assert k<=len(target)+1
    assert st.pop()==x
   contains(q,str(mx)+'。')
  elif i==10:
   arr=nums(re.search(r'有序表\((.*?)\)',c).group(1));target=int(re.search(r'查找关键字(\d+)',c).group(1));lo=0;hi=len(arr)-1;trace=[]
   while lo<=hi:
    m=(lo+hi)//2;trace.append(arr[m])
    if arr[m]==target:break
    if arr[m]<target:lo=m+1
    else:hi=m-1
   contains(q,seq(trace)+f'；{len(trace)}次。')
  finish(q)

def trees(n):
 q=Q[f'P{n}-III01'];f=q['figure'];ch=f['children'];ino=[];post=[]
 def dfs(u):
  if u is None:return
  left,right=ch.get(u,[None,None]);dfs(left);ino.append(u);dfs(right);post.append(u)
 dfs(f['root']);contains(q,'中序：'+seq(ino)+'。');contains(q,'后序：'+seq(post)+'。')
 leaves=re.search(r'叶结点(.*?)的左',q['content']).group(1).split('，')
 for leaf in leaves:
  assert ch.get(leaf,[None,None])==[None,None];i=ino.index(leaf);row(q,[leaf,ino[i-1] if i else 'NULL',ino[i+1] if i+1<len(ino) else 'NULL'])
 roots=[];u=f['root']
 while u is not None:roots.append(u);u=ch.get(u,[None,None])[1]
 contains(q,'根依次为'+seq(roots))
 for u in ino:
  children=[];v=ch.get(u,[None,None])[0]
  while v is not None:children.append(v);v=ch.get(v,[None,None])[1]
  if children:row(q,[u,seq(children)])
 finish(q)

def hashes(n):
 q=Q[f'P{n}-III02'];c=q['content'];m=int(re.search(r'表长(\d+)',c).group(1));keys=nums(re.search(r'依次插入\((.*?)\)',c).group(1));tab=[None]*m;total=0
 for k in keys:
  d=1+(k%11) if n==2 else 1;trace=[];i=0
  while True:
   addr=(k%m+i*d)%m;trace.append(addr);i+=1
   if tab[addr] is None:tab[addr]=k;break
  row(q,[k,'→'.join(map(str,trace)),len(trace)]);total+=len(trace)
 row(q,['关键字']+[x if x is not None else '空' for x in tab]);contains(q,f'成功ASL={total}/{len(keys)}')
 if n==2:
  key=int(re.search(r'查找(\d+)的探测',c).group(1));trace=[];i=0
  while True:
   addr=(key%m+i*(1+key%11))%m;trace.append(addr);i+=1
   if tab[addr] is None:break
  contains(q,'查找'+str(key)+'：'+'→'.join(map(str,trace)));contains(q,f'失败比较{len(trace)}次')
 else:
  counts=[]
  for start in range(m):
   j=start;count=1
   while tab[j] is not None:j=(j+1)%m;count+=1
   counts.append(count)
  row(q,['次数']+counts);contains(q,f'失败ASL={sum(counts)}/{m}')
 finish(q)

def huffman(n):
 q=Q[f'P{n}-III03'];weights=nums(re.search(r'^\|频数\|(.+?)\|$',q['content'],re.M).group(1));heap=[(w,i,chr(97+i)) for i,w in enumerate(weights)];heapq.heapify(heap);serial=len(heap);merges=[]
 while len(heap)>1:
  a=heapq.heappop(heap);b=heapq.heappop(heap);merges.append((a[0],b[0],a[0]+b[0]));heapq.heappush(heap,(a[0]+b[0],serial,(a[2],b[2])));serial+=1
 codes={}
 def walk(t,p):
  if isinstance(t,str):codes[t]=p
  else:walk(t[0],p+'0');walk(t[1],p+'1')
 walk(heap[0][2],'')
 for a,b,c in merges:row(q,[a,b,c])
 for char,code in codes.items():row(q,[char,code,len(code)])
 wpl=sum(weights[ord(c)-97]*len(code) for c,code in codes.items());contains(q,f'WPL={wpl}');contains(q,f'节省{sum(weights)*3-wpl}位')
 finish(q)

class Node:
 def __init__(self,k):self.k=k;self.l=None;self.r=None
def height(t):return 0 if t is None else 1+max(height(t.l),height(t.r))
def rotate_right(t):v=t.l;t.l=v.r;v.r=t;return v
def rotate_left(t):v=t.r;t.r=v.l;v.l=t;return v
def reprtree(t):return '∅' if t is None else str(t.k) if t.l is None and t.r is None else f'{t.k}({reprtree(t.l)},{reprtree(t.r)})'
def depths(t,d=1):return [] if t is None else [(t.k,d)]+depths(t.l,d+1)+depths(t.r,d+1)
def searchtrees(n):
 q=Q[f'P{n}-III04'];keys=nums(re.search(r'关键字\((.*?)\)',q['content']).group(1));events=[]
 def insert(t,k,balance):
  if t is None:return Node(k)
  if k<t.k:t.l=insert(t.l,k,balance)
  else:t.r=insert(t.r,k,balance)
  bf=height(t.l)-height(t.r)
  if balance and bf>1:
   typ='LL' if k<t.l.k else 'LR';events.append((k,t.k,typ))
   if typ=='LR':t.l=rotate_left(t.l)
   return rotate_right(t)
  if balance and bf< -1:
   typ='RR' if k>t.r.k else 'RL';events.append((k,t.k,typ))
   if typ=='RL':t.r=rotate_right(t.r)
   return rotate_left(t)
  return t
 t=None
 for k in keys:t=insert(t,k,n==2)
 contains(q,reprtree(t));ds=depths(t)
 for k,d in ds:row(q,[k,d])
 contains(q,f'ASL={sum(d for _,d in ds)}/{len(ds)}')
 if n==2:
  for event in events:row(q,event)
  zero=[]
  def visit(t):
   if not t:return
   if height(t.l)==height(t.r):zero.append(t.k)
   visit(t.l);visit(t.r)
  visit(t);claimed=nums(re.search(r'平衡因子0的结点：(.*?)。',q['answer']).group(1));assert set(zero)==set(claimed),(q['id'],zero,claimed)
 else:
  keys.sort();success=[];failure=[]
  def make(lo,hi,d):
   if lo>hi:failure.append(d-1);return None
   m=(lo+hi)//2;u=Node(keys[m]);success.append((u.k,d));u.l=make(lo,m-1,d+1);u.r=make(m+1,hi,d+1);return u
  tree=make(0,len(keys)-1,1);contains(q,'折半判定树：'+reprtree(tree));contains(q,f'折半成功ASL={sum(x[1] for x in success)}/{len(keys)}');contains(q,seq(failure));contains(q,f'失败ASL={sum(failure)}/{len(failure)}')
  for pair in success:row(q,pair)
 finish(q)

def shortest(n):
 q=Q[f'P{n}-III05'];edges=table_edges(q['content']);vertices=sorted(set(itertools.chain.from_iterable((a,b) for a,b,w in edges)));adj={u:{} for u in vertices}
 for u,v,w in edges:adj[u][v]=w
 inf=float('inf')
 if n==1:
  # Enumerate all edge subsets to verify the optimum independently of both greedy methods.
  def connected(es):
   seen={vertices[0]}
   for _ in vertices:
    for u,v,w in es:
     if u in seen or v in seen:seen.update((u,v))
   return len(seen)==len(vertices)
  best=min(sum(e[2] for e in es) for es in itertools.combinations(edges,len(vertices)-1) if connected(es))
  contains(q,f'总权值={best}')
  done={'A'};weight=0
  while len(done)<len(vertices):
   candidates=[(w,u,v) if u in done else (w,v,u) for u,v,w in edges if (u in done)!=(v in done)]
   w,u,v=min(candidates);done.add(v);weight+=w;row(q,[v,''.join(sorted([u,v])),w,''.join(sorted(done))])
  assert weight==best
  components={v:{v} for v in vertices};picked=0;weight=0
  for u,v,w in sorted(edges,key=lambda e:e[2]):
   accept=components[u] is not components[v]
   row(q,[u+v,w,'选取' if accept else '舍弃'])
   if accept:
    combined=components[u]|components[v]
    for x in combined:components[x]=combined
    picked+=1;weight+=w
    if picked==len(vertices)-1:break
  assert weight==best
  finish(q);return
 if n==2:
  dist={v:inf for v in vertices};dist['A']=0;done=[]
  while len(done)<len(vertices):
   u=min((v for v in vertices if v not in done),key=lambda v:(dist[v],v));done.append(u)
   for v,w in adj[u].items():dist[v]=min(dist[v],dist[u]+w)
   row(q,[u,''.join(done)]+['∞' if dist[v]==inf else dist[v] for v in vertices])
 else:
  d={(u,v):0 if u==v else adj[u].get(v,inf) for u in vertices for v in vertices}
  matrix_parts=re.split(r'D⁽(\d)⁾：',q['answer']+'\n'+q['guide'])
  matrices={int(matrix_parts[i]):matrix_parts[i+1] for i in range(1,len(matrix_parts),2)}
  assert len(matrices)==len(vertices)
  for k,mid in enumerate(vertices):
   old=d.copy();d={(u,v):min(old[u,v],old[u,mid]+old[mid,v]) for u in vertices for v in vertices}
   for u in vertices:assert '|'+'|'.join(map(str,[u]+['∞' if d[u,v]==inf else d[u,v] for v in vertices]))+'|' in matrices[k+1],(q['id'],k,u)
 # Independent enumeration of all simple paths also verifies final requested lengths.
 def lengths(s,t):
  result=[]
  def walk(u,path,w):
   if u==t:result.append((w,path));return
   for v,weight in adj[u].items():
    if v not in path:walk(v,path+[v],w+weight)
  walk(s,[s],0);return sorted(result)
 for s,t in ([('A','F')] if n==2 else [('A','E'),('D','C')]):
  best=lengths(s,t)[0][0];paths=[p for w,p in lengths(s,t) if w==best];assert any('→'.join(p) in q['answer'] for p in paths);assert str(best) in q['answer']
 finish(q)

def aoe(n):
 q=Q[f'P{n}-III06'];edges=table_edges(q['content']);verts=sorted(set(itertools.chain.from_iterable((u,v) for u,v,w in edges)));out={u:[] for u in verts};inc={u:[] for u in verts}
 for u,v,w in edges:out[u].append((v,w));inc[v].append((u,w))
 # For this small DAG, enumerate all source-sink paths instead of the author's forward/backward formula.
 paths=[]
 def visit(u,p,total):
  if not out[u]:paths.append((p,total));return
  for v,w in out[u]:assert v not in p;visit(v,p+[v],total+w)
 visit('A',['A'],0);duration=max(w for p,w in paths);ve={};remain={}
 def prefix(u):return max([0]+[prefix(v)+w for v,w in inc[u]])
 def suffix(u):return max([0]+[suffix(v)+w for v,w in out[u]])
 for u in verts:ve[u]=prefix(u);remain[u]=suffix(u)
 vl={u:duration-remain[u] for u in verts}
 row(q,['ve']+[ve[u] for u in verts]);row(q,['vl']+[vl[u] for u in verts])
 for u,v,w in edges:row(q,[u+'→'+v,w,ve[u],vl[v]-w,vl[v]-w-ve[u]])
 critical={'→'.join(p) for p,w in paths if w==duration};claim=set(re.findall(r'[A-H](?:→[A-H])+',re.search(r'全部关键路径：(.*?)。',q['answer']).group(1)));assert claim==critical,(q['id'],claim,critical);contains(q,f'最短工期{duration}')
 finish(q)

def sorts(n):
 q=Q[f'P{n}-III07'];arr=initial_sequence(q['content'])
 if n==1:
  a=arr[:]
  for i in range(1,len(a)):
   x=a[i];j=i
   while j and a[j-1]>x:a[j]=a[j-1];j-=1
   a[j]=x;row(q,[i,seq(a)])
  a=arr[:]
  for i in range(len(a)-1):
   changed=False
   for j in range(len(a)-1,i,-1):
    if a[j]<a[j-1]:a[j],a[j-1]=a[j-1],a[j];changed=True
   row(q,[i+1,seq(a)])
   if not changed:contains(q,f'第{i+1}趟没有发生交换');break
 elif n==2:
  a=arr[:];width=1
  while width<len(a):
   b=a[:]
   for lo in range(0,len(a),2*width):b[lo:lo+2*width]=sorted(a[lo:lo+2*width])
   a=b;row(q,[width,seq(a)]);width*=2
  total=int(re.search(r'共有(\d+)个数据块',q['content']).group(1));buffers=int(re.search(r'提供(\d+)个同样',q['content']).group(1))
  runs=(total+buffers-1)//buffers;k=buffers-1;levels=[runs]
  while runs>1:runs=(runs+k-1)//k;levels.append(runs)
  passes=len(levels)-1;io=total*2*(passes+1)
  contains(q,'→'.join(map(str,levels)));contains(q,f'共{passes}趟归并');contains(q,f'={io}')
 else:
  a=arr[:]
  def quick(lo,hi):
   if lo>=hi:return
   pivot=a[lo];i,j=lo,hi
   while i<j:
    while i<j and a[j]>=pivot:j-=1
    a[i]=a[j]
    while i<j and a[i]<=pivot:i+=1
    a[j]=a[i]
   a[i]=pivot;row(q,[f'[{lo},{hi}]',pivot,i,seq(a)]);quick(lo,i-1);quick(i+1,hi)
  quick(0,len(a)-1)
  inputs=nums(re.search(r'文件记录依次为\((.*?)\)',q['content']).group(1));capacity=int(re.search(r'工作区最多容纳(\d+)条记录',q['content']).group(1))
  # Independent replacement selection: each stored item carries its eligible run number.
  work=[(0,x) for x in inputs[:capacity]];heapq.heapify(work);at=capacity;made=[]
  while work:
   run,x=heapq.heappop(work)
   while len(made)<=run:made.append([])
   made[run].append(x)
   if at<len(inputs):
    value=inputs[at];at+=1;heapq.heappush(work,(run+(value<x),value))
  assert sorted(itertools.chain.from_iterable(made))==sorted(inputs)
  assert all(r==sorted(r) for r in made)
  for index,run in enumerate(made,1):contains(q,f'R{index}=('+seq(run)+')')
  levels=[len(made)]
  while levels[-1]>1:levels.append((levels[-1]+1)//2)
  contains(q,'→'.join(map(str,levels)));contains(q,f'共{len(levels)-1}趟')
 finish(q)

def main():
 for n in (1,2,3):
  fills(n);trees(n);hashes(n);huffman(n);searchtrees(n);shortest(n);aoe(n);sorts(n)
 assert len(PASSED)==51
 print('独立数值复核通过：三套卷全部30道填空和21道综合应用题。')
 print('覆盖：压缩下标/数组/后缀栈/队列/next/广义表/树森林计数/B与B+树/图度数、DFS、连通界与拓扑/堆/栈排列/折半；遍历线索/散列ASL/Huffman/AVL与BST/Floyd与Dijkstra/AOE/内部逐趟排序与外排段数、块I/O、置换选择。')
 print('算法不导入命题或构建模块；每次读取当前JSON题面与答案。')

if __name__=='__main__':main()
