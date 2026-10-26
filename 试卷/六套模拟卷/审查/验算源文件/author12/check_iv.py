import re
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[2]
GCC = r'D:/Program Files/mingw64/bin/gcc.exe'
ANSWERS = {}
for paper in (1, 2):
    rows = json.loads((ROOT / f'资料整理/六套模拟卷成稿/答案源稿/第{paper}套.json').read_text(encoding='utf-8'))['questions']
    ANSWERS.update({q['id']: q['content'] for q in rows})

HARNESS = {}

HARNESS['S1-IV01'] = r'''
static unsigned z=27;
static unsigned rnd(void){z=z*1664525u+1013904223u;return z;}
static Node *make(const int a[],int n){Node *h=calloc(1,sizeof(Node)),*p=h;for(int i=0;i<n;i++){p->next=malloc(sizeof(Node));p=p->next;p->data=a[i];p->next=NULL;}return h;}
static void destroy(Node *p){while(p){Node *q=p->next;free(p);p=q;}}
int main(void){
 for(int tc=0;tc<1000;tc++){
  int a[40],b[40],m=0,n=0;
  for(int v=-20;v<20;v++){if(rnd()%3==0)a[m++]=v;if(rnd()%4==0)b[n++]=v;}
  Node *A=make(a,m),*B=make(b,n);listDifference(A,B);
  Node *p=A->next;int j=0;
  for(int i=0;i<m;i++){while(j<n&&b[j]<a[i])j++;if(j<n&&b[j]==a[i])continue;assert(p&&p->data==a[i]);p=p->next;}
  assert(p==NULL);Node *q=B->next;for(int i=0;i<n;i++){assert(q&&q->data==b[i]);q=q->next;}assert(q==NULL);
  destroy(A);destroy(B);
 }
 puts("S1-IV01 OK 1000 random cases");return 0;
}
'''

HARNESS['S1-IV02'] = r'''
static unsigned z=91;
static unsigned rnd(void){z=z*1664525u+1013904223u;return z;}
static TNode t[50];static long long oracle;static int oracleValid;
static void walk(TNode *p,long long s){s+=p->data;if(!p->left&&!p->right){if(!oracleValid||s>oracle)oracle=s;oracleValid=1;return;}if(p->left)walk(p->left,s);if(p->right)walk(p->right,s);}
static int valid(TNode *p,const int *path,int i,int len){if(!p||p->data!=path[i])return 0;if(i+1==len)return !p->left&&!p->right;return valid(p->left,path,i+1,len)||valid(p->right,path,i+1,len);}
int main(void){
 for(int tc=0;tc<1000;tc++){
  int n=1+rnd()%45;for(int i=0;i<n;i++){t[i].data=(int)(rnd()%201)-100;t[i].left=t[i].right=NULL;}
  for(int i=1;i<n;i++){int k=rnd()%i;while(t[k].left&&t[k].right)k=(k+1)%i;if(!t[k].left)t[k].left=&t[i];else t[k].right=&t[i];}
  oracleValid=0;walk(&t[0],0);int path[50],len=-1,got=maxRootLeafSum(&t[0],path,&len);assert(oracleValid&&got==oracle&&len>=1&&len<=n);
  long long sum=0;for(int i=0;i<len;i++)sum+=path[i];assert(sum==got&&valid(&t[0],path,0,len));
 }
 puts("S1-IV02 OK 1000 random trees");return 0;
}
'''

GRAPH_UTIL = r'''
static unsigned z=43;
static unsigned rnd(void){z=z*1664525u+1013904223u;return z;}
static void edge(Graph *g,int u,int v){Arc *a=malloc(sizeof(Arc)),*b=malloc(sizeof(Arc));a->to=v;a->next=g->head[u];g->head[u]=a;b->to=u;b->next=g->head[v];g->head[v]=b;g->E++;}
static void clear(Graph *g){for(int i=0;i<g->V;i++){Arc *p=g->head[i];while(p){Arc *q=p->next;free(p);p=q;}}free(g->head);}
static int adjacent(const Graph *g,int u,int v){for(Arc *p=g->head[u];p;p=p->next)if(p->to==v)return 1;return 0;}
'''

HARNESS['S1-IV03'] = GRAPH_UTIL + r'''
static int ref(const Graph *g,int s,int t,int w){int q[100],seen[100]={0},h=0,r=0;seen[w]=seen[s]=1;q[r++]=s;while(h<r){int u=q[h++];if(u==t)return 1;for(Arc *a=g->head[u];a;a=a->next)if(!seen[a->to]){seen[a->to]=1;q[r++]=a->to;}}return 0;}
int main(void){
 for(int tc=0;tc<1000;tc++){
  Graph g;g.V=3+rnd()%27;g.E=0;g.head=calloc(g.V,sizeof(Arc*));for(int u=0;u<g.V;u++)for(int v=u+1;v<g.V;v++)if(rnd()%6==0)edge(&g,u,v);
  int s=rnd()%g.V,t=rnd()%g.V,w=rnd()%g.V;while(t==s)t=(t+1)%g.V;while(w==s||w==t)w=(w+1)%g.V;
  int path[100],len=-1,got=pathAvoidingVertex(&g,s,t,w,path,&len),want=ref(&g,s,t,w);assert(got==want);if(!got)assert(len==0);else{int seen[100]={0};assert(len>=2&&len<=g.V&&path[0]==s&&path[len-1]==t);for(int i=0;i<len;i++){assert(path[i]!=w&&!seen[path[i]]);seen[path[i]]=1;if(i)assert(adjacent(&g,path[i-1],path[i]));}}
  clear(&g);
 }
 puts("S1-IV03 OK 1000 random graphs");return 0;
}
'''

HARNESS['S2-IV01'] = r'''
static unsigned z=77;
static unsigned rnd(void){z=z*1664525u+1013904223u;return z;}
int main(void){
 for(int tc=0;tc<1000;tc++){
  Node head={0,NULL},*tail=&head;int a[100],n=rnd()%100;
  for(int i=0;i<n;i++){a[i]=(int)(rnd()%21)-10;tail->next=malloc(sizeof(Node));tail=tail->next;tail->data=a[i];tail->next=NULL;}
  stableNegFirst(&head);Node *p=head.next;for(int phase=0;phase<2;phase++)for(int i=0;i<n;i++)if((a[i]<0)==(phase==0)){assert(p&&p->data==a[i]);p=p->next;}assert(p==NULL);
  p=head.next;while(p){Node *q=p->next;free(p);p=q;}
 }
 puts("S2-IV01 OK 1000 random lists");return 0;
}
'''

HARNESS['S2-IV02'] = r'''
static unsigned z=121;
static unsigned rnd(void){z=z*1664525u+1013904223u;return z;}
static TNode t[50];
static int ref(TNode *p){if(!p)return 0;if(!p->left&&!p->right)return 1;return ref(p->left)+ref(p->right);}
int main(void){
 fillLeafCounts(NULL);
 for(int tc=0;tc<1000;tc++){
  int n=1+rnd()%45;for(int i=0;i<n;i++){t[i].left=t[i].right=NULL;t[i].count=-1;}
  for(int i=1;i<n;i++){int k=rnd()%i;while(t[k].left&&t[k].right)k=(k+1)%i;if(!t[k].left)t[k].left=&t[i];else t[k].right=&t[i];}
  fillLeafCounts(&t[0]);for(int i=0;i<n;i++)assert(t[i].count==ref(&t[i]));
 }
 puts("S2-IV02 OK 1000 random trees");return 0;
}
'''

HARNESS['S2-IV03'] = GRAPH_UTIL + r'''
static int ref(const Graph *g,int s,int t){int q[100],d[100],h=0,r=0;for(int i=0;i<g->V;i++)d[i]=-1;d[s]=0;q[r++]=s;while(h<r){int u=q[h++];for(Arc *a=g->head[u];a;a=a->next)if(d[a->to]==-1){d[a->to]=d[u]+1;q[r++]=a->to;}}return d[t];}
int main(void){
 for(int tc=0;tc<1000;tc++){
  Graph g;g.V=1+rnd()%29;g.E=0;g.head=calloc(g.V,sizeof(Arc*));for(int u=0;u<g.V;u++)for(int v=u+1;v<g.V;v++)if(rnd()%5==0)edge(&g,u,v);
  int s=rnd()%g.V,t=rnd()%g.V,k=(int)(rnd()%(g.V+3))-1,path[100],len=-1;
  int got=pathAtMostK(&g,s,t,k,path,&len),d=ref(&g,s,t),want=k>=0&&d>=0&&d<=k;assert(got==want);
  if(!got)assert(len==0);else{int seen[100]={0};assert(path[0]==s&&path[len-1]==t&&len-1==d&&len-1<=k);for(int i=0;i<len;i++){assert(!seen[path[i]]);seen[path[i]]=1;if(i)assert(adjacent(&g,path[i-1],path[i]));}}
  clear(&g);
 }
 puts("S2-IV03 OK 1000 random graphs");return 0;
}
'''

for qid in HARNESS:
    content = ANSWERS[qid]
    m = re.search(r'```c\n(.*?)\n```', content, re.S)
    assert m, qid
    source = '#include <stdio.h>\n#include <stdlib.h>\n#include <assert.h>\n#include <string.h>\n' + m.group(1) + '\n' + HARNESS[qid]
    src = HERE / f'{qid}.c'
    exe = HERE / f'{qid}.exe'
    src.write_text(source, encoding='utf-8')
    compile = subprocess.run([GCC, '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', str(src), '-o', str(exe)], text=True, capture_output=True)
    if compile.returncode:
        print(qid, 'COMPILE FAIL', compile.stderr)
        raise SystemExit(1)
    run = subprocess.run([str(exe)], text=True, capture_output=True)
    if run.returncode:
        print(qid, 'RUN FAIL', run.stdout, run.stderr)
        raise SystemExit(1)
    print(run.stdout.strip())
