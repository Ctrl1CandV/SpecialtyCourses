from pathlib import Path
import os, re, json, shutil, subprocess
root=Path(__file__).resolve().parents[3]
questions={}
for f in sorted((root/'试卷/2027押题卷/源稿').glob('第*.json')):
    for q in json.loads(f.read_text(encoding='utf-8'))['questions']:
        questions[q['id']]=q
def blocks(s): return re.findall(r'```cpp\n(.*?)\n```',s,re.S)
fills={
'P1-I01':['a[write-2]','++write','write'],
'P1-I02':['next','pre=p','next'],
'P2-I01':['p->next','q'],
'P2-I02':['a[i]<=b[j]','++i'],
'P2-I05':['top>=0 && out[top]==current','top+1'],
'P3-I01':['k%n','k-1'],
'P3-I02':['p->next','ta=p'],
'P3-I05':['dist[v]==-1','dist[u]+1'],
'P2-I04':['p->left!=NULL && p->right!=NULL']}
parts=[r'''#include <cstdio>
#include <cstdlib>
#include <cstddef>
#include <cassert>
#include <vector>
#include <deque>
#include <algorithm>
#include <random>
#include <set>
#include <map>
#include <functional>
#include <climits>
#include <iostream>
std::vector<int> printed;
void record(const char*,int x){ printed.push_back(x); }
void record(const char*){ printed.push_back(-1); }
''']
for id,q in questions.items():
    if q['section'] not in ['I','IV']: continue
    if id in ['P1-I03','P2-I03','P3-I03']: continue
    ns=id.replace('-','_')
    if q['section']=='IV': c='\n'.join(blocks(q['content'])+blocks(q['answer']))
    else: c='\n'.join(blocks(q['content']))
    if id in fills:
        fs=fills[id]
        if id=='P2-I02' and 'if (k == 0 || ①)' in c: fs=['out[k-1]!=x','++i','++j']
        for symbol,fill in zip('①②③',fs): c=c.replace(symbol,fill)
    if id in ['P1-I04','P2-I04']: c='struct Node {int data; Node *left,*right;};\n'+c
    if id=='P3-I04': c='int emits=0; void emit(int){++emits;}\n'+c
    c=c.replace('printf(', 'record(')
    parts.append('namespace '+ns+' {\n'+c+'\n}')

parts.append(r'''
int main(){
std::mt19937 rng(2710802); long long checks=0;
for(int run=0;run<2000;++run){
 int n=run%60; std::vector<int>a(n); for(int &x:a)x=int(rng()%15)-7; std::sort(a.begin(),a.end());
 auto b=a; std::vector<int>exp; std::map<int,int> freq;
 for(int x:a) if(++freq[x]<=2)exp.push_back(x);
 int len=P1_I01::compact(b.data(),n); assert(len==int(exp.size()) && std::equal(exp.begin(),exp.end(),b.begin())); ++checks;
 std::vector<P1_I02::Node> list(n+1); P1_I02::Node headB={0,NULL};
 for(int i=0;i<=n;++i) list[i]={i?int(rng()%19)-9:0,i<n?&list[i+1]:NULL};
 std::vector<P1_I02::Node*> ea,eb;
 for(int i=1;i<=n;++i)(list[i].data>=-3&&list[i].data<=5?eb:ea).push_back(&list[i]);
 P1_I02::extract(&list[0],&headB,-3,5);
 auto p=list[0].next; for(auto v:ea){assert(p==v);p=p->next;}assert(p==NULL);
 p=headB.next;for(auto v:eb){assert(p==v);p=p->next;}assert(p==NULL);++checks;
 P2_I01::Node head={0,NULL},*tail=&head;std::vector<int> unique;
 for(int x:a){tail->next=(P2_I01::Node*)malloc(sizeof(P2_I01::Node));tail=tail->next;tail->data=x;tail->next=NULL;}
 for(auto [x,f]:freq)if(f==1)unique.push_back(x);
 P2_I01::removeRepeated(&head);auto pp=head.next;
 for(int x:unique){assert(pp&&pp->data==x);auto next=pp->next;free(pp);pp=next;}assert(pp==NULL);++checks;
 int m=(run*3)%50;std::vector<int>c(m);for(int &x:c)x=int(rng()%17)-8;std::sort(c.begin(),c.end());
 b.resize(n+m);std::set<int> all(a.begin(),a.end());all.insert(c.begin(),c.end());exp.assign(all.begin(),all.end());
 len=P2_I02::mergeDistinct(a.data(),n,c.data(),m,b.data());assert(len==int(exp.size())&&std::equal(exp.begin(),exp.end(),b.begin()));++checks;
 b=a;int k=run%80;exp=a;if(n)std::rotate(exp.begin(),exp.end()-k%n,exp.end());
 P3_I01::rotateRight(b.data(),n,k);assert(b==exp);++checks;
 std::vector<P3_I02::Node> ln(n+1);P3_I02::Node bh={0,NULL};
 for(int i=0;i<=n;++i)ln[i]={i,i<n?&ln[i+1]:NULL};
 P3_I02::split(&ln[0],&bh);auto r=ln[0].next;
 for(int i=1;i<=n;i+=2){assert(r==&ln[i]);r=r->next;}assert(!r);r=bh.next;
 for(int i=2;i<=n;i+=2){assert(r==&ln[i]);r=r->next;}assert(!r);++checks;
 // Repeated leftmost adjacent deletion is an independent reference for the stack reading.
 std::vector<int> records(n);for(int &x:records)x=int(rng()%7)-3;
 exp=records;bool changed=true;
 while(changed){changed=false;for(int i=0;i+1<int(exp.size());++i)if(exp[i]==exp[i+1]){exp.erase(exp.begin()+i,exp.begin()+i+2);changed=true;break;}}
 b.resize(n);len=P2_I05::cancelPairs(records.data(),n,b.data());
 assert(len==int(exp.size())&&std::equal(exp.begin(),exp.end(),b.begin()));++checks;
}
// All-pairs distances independently check limited BFS counting and duplicate-discovery handling.
for(int run=0;run<600;++run){
 int n=1+run%30,limit=run%35,s=run%n;int g[100][100]={0},dist[100][100];
 for(int i=0;i<n;++i)for(int j=i+1;j<n;++j)g[i][j]=g[j][i]=(rng()%5==0);
 for(int i=0;i<n;++i)for(int j=0;j<n;++j)dist[i][j]=(i==j?0:g[i][j]?1:1000);
 for(int k=0;k<n;++k)for(int i=0;i<n;++i)for(int j=0;j<n;++j)dist[i][j]=std::min(dist[i][j],dist[i][k]+dist[k][j]);
 int expected=0;for(int v=0;v<n;++v)expected+=(dist[s][v]<=limit);
 assert(P3_I05::nearby(g,n,s,limit)==expected);++checks;
}
// Independent simulations of output/count questions.
{
 std::vector<int> st,out;int push=0,pop=0,top=0;
 for(int x:{4,1,3,2,6,5}){while(!st.empty()){++top;if(st.back()>=x)break;out.push_back(st.back());st.pop_back();++pop;}st.push_back(x);++push;}
 while(!st.empty()){out.push_back(st.back());st.pop_back();++pop;}
 assert((out==std::vector<int>{1,2,3,4,5,6})&&push==6&&pop==6&&top==8);++checks;
 std::deque<int> q={2,5,1,4,3};out.clear();int step=1,dq=0,eq=0;
 while(!q.empty()){out.push_back(q.front());q.pop_front();++dq;for(int j=0;j<step&&!q.empty();++j){int x=q.front();q.pop_front();++dq;q.push_back(x);++eq;}++step;}
 assert((out==std::vector<int>{2,1,5,3,4})&&dq==15&&eq==10);++checks;
 std::vector<int>heap(1);int compares=0;
 for(int x:{8,3,6,1,5,2}){heap.push_back(x);int i=int(heap.size())-1;while(i>1){++compares;if(heap[i/2]<=x)break;heap[i]=heap[i/2];i/=2;}heap[i]=x;}
 assert((heap==std::vector<int>{0,1,3,2,8,5,6})&&compares==7);
 out.clear();for(int z=0;z<2;++z){out.push_back(heap[1]);int x=heap.back();heap.pop_back();int i=1;while(i*2<int(heap.size())){int j=i*2;if(j+1<int(heap.size())&&heap[j+1]<heap[j])++j;if(x<=heap[j])break;heap[i]=heap[j];i=j;}heap[i]=x;}
 assert((out==std::vector<int>{1,2})&&(heap==std::vector<int>{0,3,5,6,8}));++checks;
}
{
 P1_I04::Node z[6]={{6,&z[1],&z[2]},{3,&z[3],NULL},{8,&z[4],&z[5]},{2,NULL,NULL},{7,NULL,NULL},{9,NULL,NULL}};
 assert(P1_I04::f(z,1)==54 && P1_I04::f(NULL,1)==0);++checks;
 P2_I04::Node z2[7]={{0,&z2[1],&z2[2]},{0,NULL,&z2[3]},{0,&z2[4],&z2[5]},{0,&z2[6],NULL},{0,NULL,NULL},{0,NULL,NULL},{0,NULL,NULL}};
 assert(P2_I04::count(z2)==2&&P2_I04::count(NULL)==0);++checks;
 int a[1024]={0};for(int k=0;k<=10;++k){P3_I04::emits=0;P3_I04::work(a,1<<k);assert(P3_I04::emits==k*(1<<k)/2);++checks;}
}
// Group reversal: identities, tail segment, and absence of lost/cyclic nodes.
for(int n=0;n<70;++n)for(int k=1;k<80;++k){
 std::vector<P1_IV01::Node>z(n+1);std::vector<P1_IV01::Node*>exp;
 for(int i=0;i<=n;++i)z[i]={i,i<n?&z[i+1]:NULL};for(int i=1;i<=n;++i)exp.push_back(&z[i]);
 for(int i=0;i+k<=n;i+=k)std::reverse(exp.begin()+i,exp.begin()+i+k);
 P1_IV01::reverseGroups(&z[0],k);auto p=z[0].next;for(auto x:exp){assert(p==x);p=p->next;}assert(!p);++checks;
}
// Pruning: independently retain exactly nodes having a marked descendant.
for(int run=0;run<1000;++run){
 int n=run%80;std::vector<P1_IV02::TNode*>z(n);std::vector<int>par(n,-1),left(n,-1),right(n,-1);std::vector<bool>keep(n);
 for(int i=0;i<n;++i){z[i]=(P1_IV02::TNode*)malloc(sizeof(P1_IV02::TNode));*z[i]={i,int(rng()%5==0),NULL,NULL};if(i){int p=(i-1)/2;par[i]=p;if(i%2){z[p]->left=z[i];left[p]=i;}else{z[p]->right=z[i];right[p]=i;}}}
 for(int i=0;i<n;++i)if(z[i]->mark)for(int p=i;p>=0;p=par[p])keep[p]=true;
 auto rt=P1_IV02::prune(n?z[0]:NULL);assert(rt==((n&&keep[0])?z[0]:NULL));
 for(int i=0;i<n;++i)if(keep[i]){assert(z[i]->left==((left[i]>=0&&keep[left[i]])?z[left[i]]:NULL));assert(z[i]->right==((right[i]>=0&&keep[right[i]])?z[right[i]]:NULL));free(z[i]);}++checks;
}
for(int run=0;run<600;++run){
 int n=1+run%25;int a[100][100]={0};bool reach[100][100]={false};
 for(int i=0;i<n;++i)for(int j=0;j<n;++j){a[i][j]=(i!=j&&rng()%6==0);reach[i][j]=a[i][j]||i==j;}
 for(int k=0;k<n;++k)for(int i=0;i<n;++i)for(int j=0;j<n;++j)reach[i][j]=reach[i][j]||(reach[i][k]&&reach[k][j]);
 for(int t=0;t<n;++t){std::vector<int>exp;for(int i=0;i<n;++i)if(reach[i][t])exp.push_back(i);printed.clear();int got=P1_IV03::reachTarget(a,n,t);assert(got==int(exp.size())&&printed==exp);++checks;}
}
for(int a=0;a<15;++a)for(int b=0;b<15;++b)for(int common=0;common<8;++common){
 std::vector<P2_IV01::Node>x(a),y(b),z(common);auto shared=common?&z[0]:NULL;
 for(int i=0;i<a;++i)x[i]={1,i+1<a?&x[i+1]:shared};for(int i=0;i<b;++i)y[i]={1,i+1<b?&y[i+1]:shared};for(int i=0;i<common;++i)z[i]={1,i+1<common?&z[i+1]:NULL};
 assert(P2_IV01::firstCommon(a?&x[0]:shared,b?&y[0]:shared)==shared);++checks;
}
for(int n=2;n<=60;++n){
 std::vector<P2_IV02::TNode> z(n);for(int i=0;i<n;++i)z[i]={i,2*i+1<n?&z[2*i+1]:NULL,2*i+2<n?&z[2*i+2]:NULL};
 for(int p=0;p<n;++p)for(int q=0;q<n;++q)if(p!=q){int a=p,b=q;while(a!=b){if(a>b)a=(a-1)/2;else b=(b-1)/2;}assert(P2_IV02::lca(&z[0],&z[p],&z[q])==&z[a]);++checks;}
}
for(int run=0;run<400;++run){
 int n=1+run%9;std::vector<int>perm(n);for(int i=0;i<n;++i)perm[i]=i;std::shuffle(perm.begin(),perm.end(),rng);
 P2_IV03::Graph g={};g.n=n;std::vector<P2_IV03::Arc*>edges;bool adj[100][100]={false};
 for(int i=0;i<n;++i)for(int j=i+1;j<n;++j)if(rng()%3==0){int u=perm[i],v=perm[j];auto e=new P2_IV03::Arc{v,g.head[u]};g.head[u]=e;edges.push_back(e);adj[u][v]=true;}
 for(int s=0;s<n;++s)for(int t=0;t<n;++t){
  int best=-1;std::function<void(int,int)> enumerate=[&](int u,int d){if(u==t)best=std::max(best,d);for(int v=0;v<n;++v)if(adj[u][v])enumerate(v,d+1);};enumerate(s,0);
  printed.clear();int got=P2_IV03::longestPath(g,s,t);assert(got==best);
  if(best<0)assert((printed==std::vector<int>{-1}));else{assert(int(printed.size())==best+1&&printed.front()==s&&printed.back()==t);for(int i=1;i<int(printed.size());++i)assert(adj[printed[i-1]][printed[i]]);}
  ++checks;
 }for(auto e:edges)delete e;
}
for(int n=0;n<=100;++n)for(int entry=-1;entry<n;++entry){
 std::vector<P3_IV01::Node>z(n);for(int i=0;i<n;++i)z[i]={i,i+1<n?&z[i+1]:(entry<0?NULL:&z[entry])};
 auto got=P3_IV01::breakCycle(n?&z[0]:NULL);assert(got==(entry<0?NULL:&z[entry]));for(int i=0;i<n;++i)assert(z[i].next==(i+1<n?&z[i+1]:NULL));++checks;
}
for(int run=0;run<1000;++run){
 int n=run%60;std::vector<P3_IV02::TNode>z(n);P3_IV02::TNode*rt=NULL;std::vector<int>keys(n);
 for(int i=0;i<n;++i)keys[i]=i*3-100;std::shuffle(keys.begin(),keys.end(),rng);
 for(int i=0;i<n;++i){z[i]={keys[i],NULL,NULL};auto p=&rt;while(*p)p=keys[i]<(*p)->data?&(*p)->left:&(*p)->right;*p=&z[i];}
 int lo=int(rng()%200)-130,hi=lo+int(rng()%100);std::vector<int>exp;for(int x:keys)if(lo<=x&&x<=hi)exp.push_back(x);std::sort(exp.begin(),exp.end());
 printed.clear();assert(P3_IV02::printRange(rt,lo,hi)==int(exp.size())&&printed==exp);++checks;
}
for(int run=0;run<400;++run){
 int n=1+run%20;P3_IV03::Graph g={};g.n=n;bool adj[100][100]={false};std::vector<P3_IV03::Arc*>edges;
 for(int i=0;i<n;++i)for(int j=i+1;j<n;++j)if(rng()%5==0){adj[i][j]=adj[j][i]=true;auto e=new P3_IV03::Arc{j,g.head[i]};g.head[i]=e;edges.push_back(e);e=new P3_IV03::Arc{i,g.head[j]};g.head[j]=e;edges.push_back(e);}
 for(int w=0;w<n;++w){int exp[100],got[100];std::fill(exp,exp+n,-1);int count=0;
  for(int s=0;s<n;++s)if(s!=w&&exp[s]<0){std::vector<int>todo{s};exp[s]=count;for(int ix=0;ix<int(todo.size());++ix)for(int v=0;v<n;++v)if(v!=w&&adj[todo[ix]][v]&&exp[v]<0){exp[v]=count;todo.push_back(v);}++count;}
  assert(P3_IV03::componentsWithout(g,w,got)==count&&std::equal(exp,exp+n,got));++checks;
 }for(auto e:edges)delete e;
}
std::cout<<"Independent paper I/IV checks passed: "<<checks<<" cases\n";
}
''')
cpp=root/'_tmp/revision_2027/paper_code_review.cpp'
cpp.parent.mkdir(parents=True,exist_ok=True)
cpp.write_text('\n'.join(parts),encoding='utf-8')
exe=cpp.with_suffix('.exe')
compiler=os.environ.get('CXX') or shutil.which('g++') or 'D:/Program Files/mingw64/bin/g++.exe'
subprocess.run([compiler,'-std=c++17','-O2',str(cpp),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
