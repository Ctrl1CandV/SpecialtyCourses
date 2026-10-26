import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
GCC = r'D:/Program Files/mingw64/bin/gcc.exe'
answers = {}
for paper in (3, 4):
    rows = json.loads((ROOT / f'资料整理/六套模拟卷成稿/答案源稿/第{paper}套.json').read_text(encoding='utf-8'))['questions']
    answers.update({q['id']: q['content'] for q in rows})

H = {}

H['S3-IV01'] = r'''
static unsigned seed=11;
static unsigned rnd(void){seed=seed*1664525u+1013904223u;return seed;}
static Node *make(Node *nodes,int n,int *v){for(int i=0;i<n;i++){nodes[i].key=v[i];nodes[i].next=(i+1<n?&nodes[i+1]:NULL);}return n?&nodes[0]:NULL;}
int main(void){
 for(int tc=0;tc<1000;tc++){
  Node a[30],b[30],c[30];int av[30],bv[30],cv[30],expected[90],na=rnd()%30,nb=rnd()%30,nc=rnd()%30,total=na+nb+nc;
  for(int j=0;j<3;j++){int *v=j==0?av:j==1?bv:cv;int n=j==0?na:j==1?nb:nc;int x=-20;for(int i=0;i<n;i++){x+=rnd()%4;v[i]=x;}}
  int p=0;for(int i=0;i<na;i++)expected[p++]=av[i];for(int i=0;i<nb;i++)expected[p++]=bv[i];for(int i=0;i<nc;i++)expected[p++]=cv[i];
  for(int i=0;i<total;i++)for(int j=i+1;j<total;j++)if(expected[j]<expected[i]){int t=expected[i];expected[i]=expected[j];expected[j]=t;}
  Node *out=mergeThree(make(a,na,av),make(b,nb,bv),make(c,nc,cv));int n=0,seen[90]={0};
  for(Node *q=out;q;q=q->next){assert(n<total);assert(q->key==expected[n++]);int found=0;for(int i=0;i<na;i++)if(q==&a[i]){assert(!seen[i]);seen[i]=1;found=1;}for(int i=0;i<nb;i++)if(q==&b[i]){assert(!seen[30+i]);seen[30+i]=1;found=1;}for(int i=0;i<nc;i++)if(q==&c[i]){assert(!seen[60+i]);seen[60+i]=1;found=1;}assert(found);}
  assert(n==total);
 }
 puts("S3-IV01 1000 random three-list merges OK");return 0;
}
'''

H['S3-IV02'] = r'''
static unsigned seed=19;
static unsigned rnd(void){seed=seed*1664525u+1013904223u;return seed;}
static Node nodes[50];
static void oracle(const Node *p,int depth,int mark,int *best){if(!p)return;mark|=p->mark;depth++;if(!p->left&&!p->right){if(mark&&depth>*best)*best=depth;return;}oracle(p->left,depth,mark,best);oracle(p->right,depth,mark,best);}
static int valid(const Node *p,const Node *out[],int idx,int n,int mark){if(!p||p!=out[idx])return 0;mark|=p->mark;if(idx==n-1)return !p->left&&!p->right&&mark;return valid(p->left,out,idx+1,n,mark)||valid(p->right,out,idx+1,n,mark);}
int main(void){
 {const Node *out[50];int len=999;assert(!longestMarkedPath(NULL,out,&len)&&len==0);}
 for(int tc=0;tc<1000;tc++){
  int n=1+rnd()%45;for(int i=0;i<n;i++){nodes[i].data=i;nodes[i].mark=rnd()%3==0;nodes[i].left=nodes[i].right=NULL;}
  for(int i=1;i<n;i++){int p=rnd()%i;while(nodes[p].left&&nodes[p].right)p=(p+1)%i;if(!nodes[p].left)nodes[p].left=&nodes[i];else nodes[p].right=&nodes[i];}
  int best=0;oracle(&nodes[0],0,0,&best);const Node *out[50];int len=-1;int got=longestMarkedPath(&nodes[0],out,&len);assert(got==(best>0));if(!got)assert(len==0);else assert(len==best&&valid(&nodes[0],out,0,len,0));
 }
 puts("S3-IV02 1000 random marked trees OK");return 0;
}
'''

H['S3-IV03'] = r'''
static unsigned seed=29;
static unsigned rnd(void){seed=seed*1664525u+1013904223u;return seed;}
static int oracle(const int g[12][12],int V,int u,int t,int left,int mask){if(left==0)return u==t;if(u==t)return 0;int ans=0;for(int v=0;v<V;v++)if(g[u][v]&&!(mask&(1<<v)))ans+=oracle(g,V,v,t,left-1,mask|(1<<v));return ans;}
int main(void){
 for(int tc=0;tc<1000;tc++){
  int g[12][12]={{0}},V=1+rnd()%8;for(int u=0;u<V;u++)for(int v=u+1;v<V;v++){g[u][v]=g[v][u]=rnd()%3==0;}
  for(int s=0;s<V;s++)for(int t=0;t<V;t++)for(int k=0;k<V;k++){int got=countPaths(g,V,s,t,k),want=oracle(g,V,s,t,k,1<<s);assert(got==want);}
 }
 puts("S3-IV03 1000 random graphs, all s/t/k OK");return 0;
}
'''

H['S4-IV01'] = r'''
static unsigned seed=41;
static unsigned rnd(void){seed=seed*1664525u+1013904223u;return seed;}
int main(void){
 for(int tc=0;tc<1000;tc++){
  int n=rnd()%70,a=(int)(rnd()%21)-10,b=a+rnd()%20,v[70],expected[70],remaining=0;
  Node *tail=NULL,*first=NULL;for(int i=0;i<n;i++){v[i]=(int)(rnd()%31)-15;Node *p=malloc(sizeof(Node));p->key=v[i];if(tail)tail->next=p;else first=p;tail=p;}if(tail)tail->next=first;
  for(int i=0;i<n;i++){
   if(v[i]<a||v[i]>b)expected[remaining++]=v[i];
  }
  int removed=deleteRange(&tail,n,a,b);assert(removed==n-remaining);
  if(remaining==0)assert(tail==NULL);else{assert(tail&&tail->next);Node *first=tail->next,*p=first;for(int i=0;i<remaining;i++){assert(p&&p->key==expected[i]);p=p->next;}assert(p==first);p=first;for(int i=0;i<remaining;i++){Node *next=p->next;free(p);p=next;}}
 }
 puts("S4-IV01 1000 random circular-list deletions OK");return 0;
}
'''

H['S4-IV02'] = r'''
static unsigned seed=53;
static unsigned rnd(void){seed=seed*1664525u+1013904223u;return seed;}
static void insert(Node **r,Node *p){while(*r){r=p->key<(*r)->key?&(*r)->left:&(*r)->right;}*r=p;}
int main(void){
 for(int tc=0;tc<1000;tc++){
  Node nodes[80],*root=NULL;int n=rnd()%80,used[201]={0};for(int i=0;i<n;i++){int k=rnd()%201;while(used[k])k=(k+1)%201;used[k]=1;nodes[i].key=k-100;nodes[i].left=nodes[i].right=NULL;insert(&root,&nodes[i]);}
  int x=(int)(rnd()%261)-130,out=777,got=closestKey(root,x,&out);assert(got==(n>0));if(n==0){assert(out==777);continue;}
  int best=0;long long dist=0;for(int i=0;i<n;i++){long long d=(long long)nodes[i].key-x;if(d<0)d=-d;if(i==0||d<dist||(d==dist&&nodes[i].key<best)){best=nodes[i].key;dist=d;}}assert(out==best);
 }
 puts("S4-IV02 1000 random BST nearest-key queries OK");return 0;
}
'''

H['S4-IV03'] = r'''
static unsigned seed=67;
static unsigned rnd(void){seed=seed*1664525u+1013904223u;return seed;}
static int parent[100];
static int find(int x){while(parent[x]!=x)x=parent[x]=parent[parent[x]];return x;}
static int kruskal(const int w[100][100],int V,int banA,int banB,Edge out[100],long long *total){for(int i=0;i<V;i++)parent[i]=i;int n=0;*total=0;while(n<V-1){int best=INT_MAX,a=-1,b=-1;for(int u=0;u<V;u++)for(int v=u+1;v<V;v++){if((u==banA&&v==banB)||w[u][v]>=best||find(u)==find(v))continue;best=w[u][v];a=u;b=v;}if(a<0)return 0;out[n++]=(Edge){a,b,best};*total+=best;parent[find(a)]=find(b);}return 1;}
int main(void){
 for(int tc=0;tc<1000;tc++){
  static int w[100][100];int V=2+rnd()%9;for(int i=0;i<V;i++)for(int j=0;j<V;j++)w[i][j]=(i==j?0:INT_MAX);
  for(int i=1;i<V;i++){int p=rnd()%i,v=rnd()%16;w[i][p]=w[p][i]=v;}
  for(int i=0;i<V;i++)for(int j=i+1;j<V;j++)if(w[i][j]==INT_MAX&&rnd()%3==0){int v=rnd()%16;w[i][j]=w[j][i]=v;}
  Edge old[100],oracleTree[100],rep={-1,-1,-1};long long oldWeight,newWeight=1234567,oracleWeight;assert(kruskal(w,V,-1,-1,old,&oldWeight));int failed=rnd()%(V-1),a=old[failed].u,b=old[failed].v;
  int expected=kruskal(w,V,a,b,oracleTree,&oracleWeight);int got=repairMST(w,V,old,failed,&rep,&newWeight);assert(got==expected);
  if(!got){assert(rep.u==-1&&rep.v==-1&&rep.weight==-1&&newWeight==1234567);}else{
   assert(rep.u>=0&&rep.v>=0&&rep.u<V&&rep.v<V&&rep.u!=rep.v&&w[rep.u][rep.v]==rep.weight);assert(!((rep.u==a&&rep.v==b)||(rep.u==b&&rep.v==a)));assert(newWeight==oracleWeight);
   for(int i=0;i<V;i++){parent[i]=i;}
   for(int i=0;i<V-1;i++){
    if(i!=failed){assert(find(old[i].u)!=find(old[i].v));parent[find(old[i].u)]=find(old[i].v);}
   }
   assert(find(rep.u)!=find(rep.v));parent[find(rep.u)]=find(rep.v);
   for(int i=1;i<V;i++){assert(find(i)==find(0));}
  }
 }
 puts("S4-IV03 1000 random MST edge failures OK");return 0;
}
'''

for qid, harness in H.items():
    m = re.search(r'```c\n(.*?)\n```', answers[qid], re.S)
    assert m, qid
    cpath = HERE / f'{qid}.c'
    exe = HERE / f'{qid}.exe'
    cpath.write_text('#include <stdio.h>\n#include <stdlib.h>\n#include <assert.h>\n#include <limits.h>\n' + m.group(1) + '\n' + harness, encoding='utf-8')
    comp = subprocess.run([GCC, '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror', str(cpath), '-o', str(exe)], capture_output=True, text=True)
    if comp.returncode:
        print(qid, 'COMPILE ERROR', comp.stderr)
        raise SystemExit(1)
    run = subprocess.run([str(exe)], capture_output=True, text=True)
    if run.returncode:
        print(qid, 'RUN ERROR', run.stdout, run.stderr)
        raise SystemExit(1)
    print(run.stdout.strip())
