"""Independent C11 executable tests for all paper 5/6 algorithm answers."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
GCC = Path("D:/Program Files/mingw64/bin/gcc.exe")

HARNESS = {
"S5-IV01": r'''
#include <assert.h>
#include <stdio.h>
static unsigned r=1729u;
static unsigned rng(void){r=r*1664525u+1013904223u;return r;}
int main(void){
  for(int trial=0;trial<4000;trial++){
    Node *head=malloc(sizeof *head); assert(head); head->next=NULL;
    Node *tail=head; int vals[50],len=rng()%50;
    for(int i=0;i<len;i++){vals[i]= i? vals[i-1]+(int)(rng()%2): (int)(rng()%5);Node *p=malloc(sizeof *p);assert(p);p->key=vals[i];p->next=NULL;tail->next=p;tail=p;}
    keepLastOfEachKey(head);
    Node *p=head->next;
    for(int i=0;i<len;i++) if(i==len-1||vals[i]!=vals[i+1]){assert(p&&p->key==vals[i]);p=p->next;}
    assert(!p);p=head->next;
    while(p){Node *next=p->next;free(p);p=next;}
    free(head);
  }
  puts("S5-IV01 PASS 4000 sorted random lists");return 0;
}''',
"S5-IV02": r'''
#include <assert.h>
#include <stdio.h>
static unsigned r=2871u;
static unsigned rng(void){r=r*1664525u+1013904223u;return r;}
static int predcheck(int n, unsigned char arc[8][8], const int p[],int k){
  int used[8]={0};for(int i=0;i<k;i++){int u=p[i];for(int a=0;a<n;a++)if(arc[a][u]&&!used[a])return 0;used[u]=1;}return 1;
}
int main(void){
  for(int trial=0;trial<5000;trial++){
    int n=1+(int)(rng()%8),ord[8],p[8];unsigned char mat[8][8]={{0}};Arc *head[8]={0};Graph g={n,head};
    for(int i=0;i<n;i++)ord[i]=i;
    for(int i=n-1;i>0;i--){int j=(int)(rng()%(unsigned)(i+1));int t=ord[i];ord[i]=ord[j];ord[j]=t;}
    for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)if(rng()%3==0){int a=ord[i],b=ord[j];mat[a][b]=1;Arc *e=malloc(sizeof *e);assert(e);e->to=b;e->next=head[a];head[a]=e;}
    for(int i=0;i<n;i++)p[i]=i;
    for(int i=n-1;i>0;i--){int j=(int)(rng()%(unsigned)(i+1));int t=p[i];p[i]=p[j];p[j]=t;}
    int k=(int)(rng()%(unsigned)(n+1));
    assert(canBePrefix(&g,p,k)==predcheck(n,mat,p,k));
    for(int a=0;a<n;a++){Arc *e=head[a];while(e){Arc *next=e->next;free(e);e=next;}}
  }
  puts("S5-IV02 PASS 5000 random DAG/prefix cases");return 0;
}''',
"S5-IV03": r'''
#include <assert.h>
#include <stdio.h>
static unsigned r=4973u;
static unsigned rng(void){r=r*1664525u+1013904223u;return r;}
int main(void){
  for(int trial=0;trial<5000;trial++){
    int n=(int)(rng()%20);Node a[20];int adj[20][20]={{0}};
    for(int i=0;i<n;i++)a[i].left=a[i].right=NULL;
    for(int i=1;i<n;i++){
      int p;do{p=(int)(rng()%(unsigned)i);}while(a[p].left&&a[p].right);
      if(!a[p].left && (!a[p].right || rng()%2==0))a[p].left=&a[i];else a[p].right=&a[i];
      adj[i][p]=adj[p][i]=1;
    }
    int expect=0;
    for(int src=0;src<n;src++){
      int dist[20],queue[20],head=0,tail=0;for(int j=0;j<n;j++)dist[j]=-1;
      dist[src]=0;queue[tail++]=src;
      while(head<tail){int x=queue[head++];for(int y=0;y<n;y++)if(adj[x][y]&&dist[y]<0){dist[y]=dist[x]+1;queue[tail++]=y;}}
      for(int j=0;j<n;j++)if(dist[j]>expect)expect=dist[j];
    }
    assert(treeDiameter(n?&a[0]:NULL)==expect);
  }
  puts("S5-IV03 PASS 5000 random trees vs all-pairs BFS");return 0;
}''',
"S6-IV01": r'''
#include <assert.h>
#include <stdio.h>
static unsigned r=6729u;
static unsigned rng(void){r=r*1664525u+1013904223u;return r;}
static Node *make(const int x[],int n){Node *head=NULL,*tail=NULL;for(int i=0;i<n;i++){Node *p=malloc(sizeof *p);assert(p);p->key=x[i];p->next=NULL;if(!head)head=p;else tail->next=p;tail=p;}return head;}
int main(void){
  for(int trial=0;trial<4000;trial++){
    int a[25],b[25],na=(int)(rng()%25),nb=(int)(rng()%25),xa=0,xb=0;
    for(int i=0;i<na;i++){xa+=(int)(rng()%3)+1;a[i]=xa;}
    for(int i=0;i<nb;i++){xb+=(int)(rng()%3)+1;b[i]=xb;}
    Node *out=symmetricDiff(make(a,na),make(b,nb));
    int i=0,j=0;Node *p=out;
    while(i<na||j<nb){
      if(i<na && j<nb && a[i]==b[j]){i++;j++;continue;}
      int v;if(j==nb || (i<na&&a[i]<b[j]))v=a[i++];else v=b[j++];
      assert(p&&p->key==v);p=p->next;
    }
    assert(!p);p=out;while(p){Node *next=p->next;free(p);p=next;}
  }
  puts("S6-IV01 PASS 4000 random sorted-list symmetric differences");return 0;
}''',
"S6-IV02": r'''
#include <assert.h>
#include <stdio.h>
static unsigned r=7927u;
static unsigned rng(void){r=r*1664525u+1013904223u;return r;}
static int left[18],right[18],pre[18],in[18],expected[18],ip,ii,io;
static void walk(int x){if(x<0)return;pre[ip++]=x+101;walk(left[x]);in[ii++]=x+101;walk(right[x]);expected[io++]=x+101;}
int main(void){
  for(int trial=0;trial<5000;trial++){
    int n=(int)(rng()%18),out[18];
    for(int i=0;i<n;i++)left[i]=right[i]=-1;
    for(int i=1;i<n;i++){int p;do{p=(int)(rng()%(unsigned)i);}while(left[p]>=0&&right[p]>=0);
      if(left[p]<0 && (right[p]>=0 || rng()%2==0))left[p]=i;else right[p]=i;}
    ip=ii=io=0;walk(n?0:-1);
    for(int i=0;i<18;i++)out[i]=-99;
    toPost(pre,in,n,out);
    for(int i=0;i<n;i++)assert(out[i]==expected[i]);
    if(n==0)assert(out[0]==-99);
  }
  puts("S6-IV02 PASS 5000 random binary trees and empty input");return 0;
}''',
"S6-IV03": r'''
#include <assert.h>
#include <stdio.h>
static unsigned r=9829u;
static unsigned rng(void){r=r*1664525u+1013904223u;return r;}
static int path(int n,unsigned char a[9][9],int src,int dst){int seen[9]={0},q[9],l=0,h=0;q[h++]=src;seen[src]=1;while(l<h){int x=q[l++];if(x==dst)return 1;for(int y=0;y<n;y++)if(a[x][y]&&!seen[y]){seen[y]=1;q[h++]=y;}}return 0;}
int main(void){
  for(int trial=0;trial<5000;trial++){
    int n=1+(int)(rng()%9),ord[9],pos[9];unsigned char mat[9][9]={{0}};Arc *head[9]={0};Graph g={n,head};
    for(int i=0;i<n;i++)ord[i]=i;
    for(int i=n-1;i>0;i--){int j=(int)(rng()%(unsigned)(i+1));int t=ord[i];ord[i]=ord[j];ord[j]=t;}
    for(int i=0;i<n;i++)pos[ord[i]]=i;
    for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)if(rng()%4==0){int a=ord[i],b=ord[j];mat[a][b]=1;Arc *e=malloc(sizeof *e);assert(e);e->to=b;e->next=head[a];head[a]=e;}
    int u=(int)(rng()%(unsigned)n),v=(int)(rng()%(unsigned)n);
    if(u!=v && mat[u][v]){trial--;for(int a=0;a<n;a++){Arc *e=head[a];while(e){Arc *next=e->next;free(e);e=next;}}continue;}
    State want=(u==v || path(n,mat,v,u))?CYCLE:((pos[u]<pos[v])?ORDER_OK:REORDER);
    assert(classifyArc(&g,ord,u,v)==want);
    for(int a=0;a<n;a++){Arc *e=head[a];while(e){Arc *next=e->next;free(e);e=next;}}
  }
  puts("S6-IV03 PASS 5000 random DAG/new-arc cases");return 0;
}''',
}

for paper in (5,6):
    answer = json.loads((ROOT / f"资料整理/六套模拟卷成稿/答案源稿/第{paper}套.json").read_text(encoding="utf-8"))
    for q in answer["questions"]:
        qid = q["id"]
        if qid not in HARNESS:
            continue
        match = re.search(r"```c\n(.*?)\n```", q["content"], re.S)
        assert match, qid
        cfile = HERE / f"{qid}.c"
        cfile.write_text(match.group(1) + "\n" + HARNESS[qid], encoding="utf-8")
        exe = HERE / f"{qid}.exe"
        cmd = [str(GCC), "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror", str(cfile), "-o", str(exe)]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        p = subprocess.run([str(exe)], check=True, capture_output=True, text=True, timeout=30)
        print(p.stdout.strip())
