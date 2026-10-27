"""Compile the nine algorithm answers extracted from current JSON and test their contracts.

Run from repository root. Generated C++ files/binaries stay in ignored _tmp.
"""
from pathlib import Path
import json,os,re,shutil,subprocess,hashlib

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'试卷/2027押题卷/源稿'
TMP=ROOT/'_tmp/revision_2027/algorithm_checks'
TMP.mkdir(parents=True,exist_ok=True)
GXX=Path(os.environ.get('CXX') or shutil.which('g++') or 'D:/Program Files/mingw64/bin/g++.exe')
HEADER=r'''
#include <algorithm>
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <functional>
#include <random>
#include <set>
#include <sstream>
#include <string>
#include <vector>
using namespace std;
string captured;
int capture(const char *fmt, ...) {
    char b[128]; va_list args; va_start(args, fmt);
    int n=vsnprintf(b,sizeof(b),fmt,args); va_end(args);
    captured+=b; return n;
}
vector<int> output() { vector<int> r; istringstream s(captured); int x; while(s>>x) r.push_back(x); return r; }
#define printf capture
'''
TESTS={
'P2-I02':r'''
int main(){mt19937 rng(27212);for(int n=0;n<=30;++n)for(int m=0;m<=30;++m)for(int rep=0;rep<8;++rep){
 vector<int>a(n),b(m);for(int&x:a)x=int(rng()%17)-8;for(int&x:b)x=int(rng()%17)-8;sort(a.begin(),a.end());sort(b.begin(),b.end());
 vector<int>want=a;want.insert(want.end(),b.begin(),b.end());sort(want.begin(),want.end());want.erase(unique(want.begin(),want.end()),want.end());vector<int>out(n+m);
 int k=mergeDistinct(a.data(),n,b.data(),m,out.data());out.resize(k);assert(out==want);
}}
''',
'P1-IV01':r'''
int main(){
 for(int n=0;n<=60;++n) for(int k=1;k<=15;++k){
  Node head{0,nullptr};Node *tail=&head;vector<Node*> ptrs;
  for(int i=0;i<n;++i){Node *p=(Node*)malloc(sizeof(Node));*p={i,nullptr};tail->next=p;tail=p;ptrs.push_back(p);}
  vector<Node*> want=ptrs;for(int s=0;s+k<=n;s+=k) reverse(want.begin()+s,want.begin()+s+k);
  reverseGroups(&head,k);Node *p=head.next;
  for(int i=0;i<n;++i){assert(p==want[i]);assert(p->data==int(find(ptrs.begin(),ptrs.end(),p)-ptrs.begin()));p=p->next;}
  assert(p==nullptr);for(Node *x:ptrs)free(x);
 }
}
''',
'P1-IV02':r'''
int main(){mt19937 rng(27101);
 for(int n=0;n<=60;++n)for(int rep=0;rep<30;++rep){
  vector<TNode*> ns;vector<pair<int,int>> slots;
  vector<int> l(n,-1),r(n,-1);vector<bool> keep(n,false);
  for(int i=0;i<n;++i){auto *p=(TNode*)malloc(sizeof(TNode));*p={i,int(rng()%4==0),nullptr,nullptr};ns.push_back(p);
   if(i){int at=rng()%slots.size();auto [par,side]=slots[at];slots.erase(slots.begin()+at);if(side==0){ns[par]->left=p;l[par]=i;}else{ns[par]->right=p;r[par]=i;}}
   slots.push_back({i,0});slots.push_back({i,1});
  }
  function<bool(int)> check=[&](int i){if(i<0)return false;bool a=check(l[i]),b=check(r[i]);keep[i]=a||b||ns[i]->mark;return bool(keep[i]);};
  if(n)check(0);TNode *root=prune(n?ns[0]:nullptr);assert(root==(n&&keep[0]?ns[0]:nullptr));
  for(int i=0;i<n;++i)if(keep[i]){assert(ns[i]->left==(l[i]>=0&&keep[l[i]]?ns[l[i]]:nullptr));assert(ns[i]->right==(r[i]>=0&&keep[r[i]]?ns[r[i]]:nullptr));free(ns[i]);}
 }
}
''',
'P1-IV03':r'''
int main(){mt19937 rng(27103);
 for(int n=1;n<=22;++n)for(int rep=0;rep<50;++rep){int A[100][100]={0};
  for(int i=0;i<n;++i)for(int j=0;j<n;++j)if(i!=j)A[i][j]=rng()%5==0;
  int t=rng()%n;vector<int>want;
  for(int s=0;s<n;++s){bool seen[100]={false};vector<int>st{s};seen[s]=true;while(!st.empty()){int u=st.back();st.pop_back();for(int v=0;v<n;++v)if(A[u][v]&&!seen[v]){seen[v]=true;st.push_back(v);}}if(seen[t])want.push_back(s);}
  captured.clear();int count=reachTarget(A,n,t);assert(count==int(want.size()));assert(output()==want);
 }
}
''',
'P2-IV01':r'''
int main(){for(int a=0;a<=10;++a)for(int b=0;b<=10;++b)for(int c=0;c<=8;++c){
 vector<Node*>all;auto chain=[&](int n,Node *suffix){Node *h=suffix;for(int i=0;i<n;++i){Node *p=(Node*)malloc(sizeof(Node));*p={0,h};all.push_back(p);h=p;}return h;};
 Node *common=chain(c,nullptr),*A=chain(a,common),*B=chain(b,common);vector<Node*>next;
 for(auto*p:all)next.push_back(p->next);assert(firstCommon(A,B)==common);
 for(size_t i=0;i<all.size();++i){assert(all[i]->next==next[i]);free(all[i]);}
}}
''',
'P2-IV02':r'''
int main(){mt19937 rng(27202);for(int n=2;n<=60;++n)for(int rep=0;rep<30;++rep){
 vector<TNode*>ns;vector<pair<int,int>> slots;vector<int>parent(n,-1);
 for(int i=0;i<n;++i){auto*p=(TNode*)malloc(sizeof(TNode));*p={i,nullptr,nullptr};ns.push_back(p);if(i){int at=rng()%slots.size();auto[par,side]=slots[at];slots.erase(slots.begin()+at);parent[i]=par;if(side==0)ns[par]->left=p;else ns[par]->right=p;}slots.push_back({i,0});slots.push_back({i,1});}
 for(int q=0;q<20;++q){int a=rng()%n,b=rng()%n;if(a==b)b=(b+1)%n;set<int>anc;for(int x=a;x!=-1;x=parent[x])anc.insert(x);int x=b;while(!anc.count(x))x=parent[x];assert(lca(ns[0],ns[a],ns[b])==ns[x]);}
 for(auto*p:ns)free(p);
}}
''',
'P2-IV03':r'''
int main(){mt19937 rng(27203);for(int n=1;n<=22;++n)for(int rep=0;rep<60;++rep){
 Graph g{};g.n=n;bool adj[MAXV][MAXV]={false};vector<Arc*> arcs;
 for(int u=0;u<n;++u)for(int v=u+1;v<n;++v)if(rng()%4==0){adj[u][v]=true;auto*e=new Arc{v,g.head[u]};g.head[u]=e;arcs.push_back(e);}
 int s=rng()%n,t=rng()%n;vector<int>memo(n,-2);function<int(int)>best=[&](int u){if(u==t)return 0;if(memo[u]!=-2)return memo[u];int val=-1;for(int v=u+1;v<n;++v)if(adj[u][v]){int b=best(v);if(b>=0)val=max(val,b+1);}return memo[u]=val;};int want=best(s);
 captured.clear();int got=longestPath(g,s,t);assert(got==want);auto path=output();
 if(want<0)assert(path==vector<int>{-1});else{assert(path.size()==size_t(want+1));assert(path.front()==s&&path.back()==t);for(size_t i=1;i<path.size();++i)assert(adj[path[i-1]][path[i]]);}
 for(auto*e:arcs)delete e;
}}
''',
'P3-IV01':r'''
int main(){for(int n=0;n<=70;++n)for(int entry=-1;entry<n;++entry){
 vector<Node*>ns;for(int i=0;i<n;++i){auto*p=(Node*)malloc(sizeof(Node));*p={i,nullptr};ns.push_back(p);if(i)ns[i-1]->next=p;}
 if(entry>=0)ns.back()->next=ns[entry];Node*head=n?ns[0]:nullptr;assert(breakCycle(head)==(entry>=0?ns[entry]:nullptr));
 Node*p=head;for(int i=0;i<n;++i){assert(p==ns[i]);p=p->next;}assert(p==nullptr);for(auto*x:ns)free(x);
}}
''',
'P3-IV02':r'''
int main(){mt19937 rng(27302);for(int n=0;n<=100;++n)for(int rep=0;rep<12;++rep){
 vector<int>vals;for(int i=0;i<n;++i)vals.push_back(2*i-100);shuffle(vals.begin(),vals.end(),rng);TNode*root=nullptr;vector<TNode*>ns;
 for(int x:vals){TNode**p=&root;while(*p)p=x<(*p)->data?&(*p)->left:&(*p)->right;*p=(TNode*)malloc(sizeof(TNode));**p={x,nullptr,nullptr};ns.push_back(*p);}
 for(int test=0;test<20;++test){int lo=int(rng()%250)-125,hi=int(rng()%250)-125;if(lo>hi)swap(lo,hi);vector<int>want;for(int x:vals)if(lo<=x&&x<=hi)want.push_back(x);sort(want.begin(),want.end());captured.clear();int got=printRange(root,lo,hi);assert(got==int(want.size()));assert(output()==want);}
 for(auto*p:ns)free(p);
}}
''',
'P3-IV03':r'''
int main(){mt19937 rng(27303);for(int n=1;n<=30;++n)for(int rep=0;rep<50;++rep){
 Graph g{};g.n=n;bool adj[MAXV][MAXV]={false};vector<Arc*>arcs;
 for(int u=0;u<n;++u)for(int v=u+1;v<n;++v)if(rng()%6==0){adj[u][v]=adj[v][u]=true;auto*a=new Arc{v,g.head[u]};g.head[u]=a;arcs.push_back(a);auto*b=new Arc{u,g.head[v]};g.head[v]=b;arcs.push_back(b);}
 int w=rng()%n,label[MAXV];vector<int>want(n,-1);int count=0;
 for(int s=0;s<n;++s)if(s!=w&&want[s]<0){vector<int>st{s};want[s]=count;while(!st.empty()){int u=st.back();st.pop_back();for(int v=0;v<n;++v)if(v!=w&&adj[u][v]&&want[v]<0){want[v]=count;st.push_back(v);}}++count;}
 assert(componentsWithout(g,w,label)==count);for(int i=0;i<n;++i)assert(label[i]==want[i]);for(auto*e:arcs)delete e;
}}
'''
}

def main():
    count=0
    for p in (1,2,3):
        path=SRC/f'第{p}套.json'; raw=path.read_bytes(); obj=json.loads(raw)
        for q in obj['questions']:
            if q['section']!='IV' and q['id']!='P2-I02':continue
            blocks=re.findall(r'```(?:cpp|c)\s*\n(.*?)\n```',q['content']+'\n'+q['answer'],re.S)
            assert blocks,q['id']
            if q['id']=='P2-I02':
                blocks=[b.replace('①','a[i] <= b[j]').replace('②','++i') for b in blocks]
            text=HEADER+'\n'+'\n'.join(blocks)+'\n'+TESTS[q['id']]
            src=TMP/(q['id']+'.cpp');exe=TMP/(q['id']+'.exe');src.write_text(text,encoding='utf-8')
            subprocess.run([str(GXX),'-std=c++17','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-pedantic',str(src),'-o',str(exe)],check=True,capture_output=True,text=True)
            subprocess.run([str(exe)],check=True,timeout=30,capture_output=True,text=True)
            if q['id']=='P2-I02':
                src.write_text(text.replace('a[i] <= b[j]','a[i] < b[j]'),encoding='utf-8')
                subprocess.run([str(GXX),'-std=c++17','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-pedantic',str(src),'-o',str(exe)],check=True,capture_output=True,text=True)
                subprocess.run([str(exe)],check=True,timeout=30,capture_output=True,text=True)
            count+=1;print(q['id'],'PASS')
        print(path.name,'sha256',hashlib.sha256(raw).hexdigest())
    print('All',count,'code answers (9 algorithms + ordered merge reading) passed randomized and boundary tests.')
if __name__=='__main__':main()
