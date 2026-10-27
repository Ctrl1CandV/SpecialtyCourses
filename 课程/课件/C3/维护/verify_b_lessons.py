"""Extract current B-series appendix code, compile, and test against independent results."""
from pathlib import Path
import os,re,subprocess,shutil
ROOT=Path(__file__).resolve().parents[4]
BASE=ROOT/'课程/课件/C3'
TMP=ROOT/'_tmp/c3_revision/b_verify'
CPP=r'''
#include <algorithm>
#include <cassert>
#include <cstddef>
#include <cstdio>
#include <cstdlib>
#include <deque>
#include <functional>
#include <numeric>
#include <random>
#include <set>
#include <string>
#include <vector>
using namespace std;
mt19937 rng(8022027);
template<class T> T* node(){auto p=(T*)calloc(1,sizeof(T)); assert(p); return p;}
template<class T> T* chain(const vector<int>& a){T *h=nullptr,*r=nullptr;for(int x:a){T*p=node<T>();p->data=x;if(r)r->next=p;else h=p;r=p;}return h;}
template<class T> vector<int> vals(T*p){vector<int>a;set<T*>seen;for(;p;p=p->next){assert(seen.insert(p).second);a.push_back(p->data);}return a;}
template<class T> void destroy(T*p){while(p){T*q=p->next;free(p);p=q;}}
'''
TEST=r'''
void test1(){
 for(int z=0;z<500;++z){vector<int>a,b;for(unsigned i=0,n=rng()%25;i<n;++i)a.push_back(rng()%15-7);for(unsigned i=0,n=rng()%25;i<n;++i)b.push_back(rng()%15-7);sort(a.begin(),a.end());sort(b.begin(),b.end());
 auto x=chain<L1::Node>(a),y=chain<L1::Node>(b);set<L1::Node*> before;for(auto p=x;p;p=p->next)before.insert(p);for(auto p=y;p;p=p->next)before.insert(p);
 auto r=L1::mergeAndReverse(x,y);vector<int>expect=a;expect.insert(expect.end(),b.begin(),b.end());sort(expect.rbegin(),expect.rend());assert(vals(r)==expect);set<L1::Node*>after;for(auto p=r;p;p=p->next)after.insert(p);assert(before==after);destroy(r);
 shuffle(expect.begin(),expect.end(),rng);auto h=node<L1::SortNode>();h->next=chain<L1::SortNode>(expect);vector<L1::SortNode*>ids;for(auto p=h->next;p;p=p->next)ids.push_back(p);L1::SelectionSort(h);sort(expect.begin(),expect.end());assert(vals(h->next)==expect);int i=0;for(auto p=h->next;p;p=p->next)assert(p==ids[i++]);destroy(h);
 }
}
void test2(){L2::LinkQueue q{nullptr};deque<int>d;
 for(int i=0;i<5000;++i){if(rng()%2){auto p=node<L2::LinkNode>();p->data=i;L2::EnQueue(&q,p);d.push_back(i);}else{auto p=L2::DeQueue(&q);if(d.empty())assert(p==nullptr);else{assert(p&&p->data==d.front());d.pop_front();free(p);}}assert((q.rear==nullptr)==d.empty());if(q.rear)assert(q.rear->next->data==d.front());}
 while(auto p=L2::DeQueue(&q))free(p);
 for(int cap=1;cap<=10;++cap){L2::TwStack s;L2::InitStack(s,cap);vector<int>a[2];for(int z=0;z<1000;++z){int side=rng()%2;if(rng()%2){bool room=a[0].size()+a[1].size()<(size_t)cap;bool ok=L2::Push(s,side,z);assert(ok==room);if(ok)a[side].push_back(z);}else{int out=-987;bool ok=L2::Pop(s,side,out);assert(ok==!a[side].empty());if(ok){assert(out==a[side].back());a[side].pop_back();}else assert(out==-987);}assert(s.top[0]+1==(int)a[0].size());assert(cap-s.top[1]==(int)a[1].size());}}
}
bool bracketOracle(const string&s){vector<char>v;for(char c:s){auto l=string("([{").find(c),r=string(")]}").find(c);if(l!=string::npos)v.push_back(c);else if(r!=string::npos){if(v.empty()||v.back()!=string("([{")[r])return false;v.pop_back();}}return v.empty();}
void test3(){for(int z=0;z<500;++z){vector<int>a,b;for(int x=-10;x<=10;++x){if(rng()%2)a.push_back(x);if(rng()%2)b.push_back(x);}auto A=node<L3::DiffNode>(),B=node<L3::DiffNode>();A->next=chain<L3::DiffNode>(a);B->next=chain<L3::DiffNode>(b);vector<L3::DiffNode*>bp;for(auto p=B;p;p=p->next)bp.push_back(p);L3::listDifference(A,B);vector<int>e;set_difference(a.begin(),a.end(),b.begin(),b.end(),back_inserter(e));assert(vals(A->next)==e);assert(vals(B->next)==b);int j=0;for(auto p=B;p;p=p->next)assert(p==bp[j++]);destroy(A);destroy(B);}
 vector<string>cases={"","([a]+{b})","([)]","())(","((","abc",string(500,'(')+string(500,')')};for(int z=0;z<1000;++z){string s;for(unsigned i=0,n=rng()%50;i<n;++i)s+="()[]{}ab"[rng()%8];cases.push_back(s);}for(auto&s:cases){auto h=node<L3::CharNode>(),p=h;vector<L3::CharNode*>mem{h};for(char c:s){auto q=node<L3::CharNode>();q->ch=c;p->next=q;p=q;mem.push_back(p);}p->next=h;assert(L3::bracketsMatch(h)==bracketOracle(s));for(auto x:mem)free(x);}}
void test4(){for(int n=0;n<=60;++n)for(int z=0;z<10;++z){vector<L4::TreeNode*>a;for(int i=0;i<n;++i){auto p=node<L4::TreeNode>();p->data=i-20;a.push_back(p);}for(int i=1;i<n;++i){while(true){auto p=a[rng()%i];auto &slot=(rng()%2)?p->left:p->right;if(!slot){slot=a[i];break;}}}
 vector<int>pre,in,post,best,cur;function<void(L4::TreeNode*)>walk=[&](auto p){if(!p)return;pre.push_back(p->data);cur.push_back(p->data);if(!p->left&&!p->right&&cur.size()>best.size())best=cur;walk(p->left);in.push_back(p->data);walk(p->right);post.push_back(p->data);cur.pop_back();};auto root=n?a[0]:nullptr;walk(root);vector<int>path(n+1,999),out(n+1,999);int len=L4::longestPath(root,path.data());assert(len==(int)best.size());assert(equal(best.begin(),best.end(),path.begin()));L4::toPost(pre.data(),in.data(),n,out.data());assert(equal(post.begin(),post.end(),out.begin()));assert(out[n]==999);for(auto p:a)free(p);
}}
template<class G,class A> G graphOf(const vector<vector<int>>&e,vector<A*>&mem){int n=e.size();G g{n,(A**)calloc(n,sizeof(A*))};for(int i=0;i<n;++i)for(int j=n-1;j>=0;--j)if(e[i][j]){A*p=node<A>();p->to=j;p->next=g.head[i];g.head[i]=p;mem.push_back(p);}return g;}
bool pathOK(const vector<vector<int>>&e,const int p[],int len,int s,int t){if(len<1||p[0]!=s||p[len-1]!=t)return false;set<int>x;for(int i=0;i<len;++i){if(!x.insert(p[i]).second)return false;if(i&&!e[p[i-1]][p[i]])return false;}return true;}
bool permOracle(const vector<vector<int>>&e,int s,int t,int k,int w){int n=e.size();vector<int>q;for(int x=0;x<n;++x)if(x!=s)q.push_back(x);do{vector<int>p{s};p.insert(p.end(),q.begin(),q.end());for(int len=1;len<=n;++len){if(k>=0&&len!=k+1)continue;if(pathOK(e,p.data(),len,s,t)&&(w<0||find(p.begin(),p.begin()+len,w)!=p.begin()+len))return true;}}while(next_permutation(q.begin(),q.end()));return false;}
void test5(){for(int n=3;n<=7;++n)for(int z=0;z<35;++z){vector<vector<int>>e(n,vector<int>(n));for(int i=0;i<n;++i)for(int j=i+1;j<n;++j)e[i][j]=e[j][i]=(rng()%3==0);vector<L5::Arc*>mem;auto g=graphOf<L5::Graph,L5::Arc>(e,mem);vector<int>p(n+1,-1);int s=rng()%n,t=rng()%n;for(int k=0;k<n;++k){bool ok=L5::exactPath(&g,s,t,k,p.data());assert(ok==permOracle(e,s,t,k,-1));if(ok)assert(pathOK(e,p.data(),k+1,s,t));}assert(!L5::exactPath(&g,s,t,-1,p.data()));assert(!L5::exactPath(&g,s,t,n,p.data()));
 s=0;t=n-1;int w=1,len=-1;bool ok=L5::pathThrough(&g,s,t,w,p.data(),len);assert(ok==permOracle(e,s,t,-1,w));if(ok){assert(pathOK(e,p.data(),len,s,t));assert(find(p.begin(),p.begin()+len,w)!=p.begin()+len);}else assert(len==0);for(auto a:mem)free(a);free(g.head);}}
bool kahnCycle(const vector<vector<int>>&e){int n=e.size();vector<int>d(n);for(auto&r:e)for(int v=0;v<n;++v)d[v]+=r[v];deque<int>q;for(int i=0;i<n;++i)if(!d[i])q.push_back(i);int c=0;while(!q.empty()){int u=q.front();q.pop_front();++c;for(int v=0;v<n;++v)if(e[u][v]&&--d[v]==0)q.push_back(v);}return c!=n;}
bool topoOracle(const vector<vector<int>>&e,const vector<int>&o){int n=e.size();vector<int>d(n),seen(n);for(auto&r:e)for(int v=0;v<n;++v)d[v]+=r[v];for(int u:o){if(u<0||u>=n||seen[u]||d[u])return false;seen[u]=1;for(int v=0;v<n;++v)if(e[u][v])--d[v];}return true;}
void test6(){for(int n=1;n<=10;++n)for(int z=0;z<100;++z){vector<int>sigma(n);iota(sigma.begin(),sigma.end(),0);shuffle(sigma.begin(),sigma.end(),rng);vector<vector<int>>e(n,vector<int>(n));for(int i=0;i<n;++i)for(int j=i+1;j<n;++j)if(rng()%3==0)e[sigma[i]][sigma[j]]=1;vector<L6::Arc*>mem;auto g=graphOf<L6::Graph,L6::Arc>(e,mem);assert(L6::isTopo(&g,sigma.data()));auto o=sigma;shuffle(o.begin(),o.end(),rng);assert(L6::isTopo(&g,o.data())==topoOracle(e,o));o[0]=n;assert(!L6::isTopo(&g,o.data()));if(n>1){o=sigma;o[0]=o[1];assert(!L6::isTopo(&g,o.data()));}
 for(int u=0;u<n;++u){for(int v=0;v<n;++v){if(!e[u][v]){auto f=e;f[u][v]=1;auto want=kahnCycle(f)?L6::CYCLE:(topoOracle(f,sigma)?L6::ORDER_OK:L6::REORDER);assert(L6::classifyArc(&g,sigma.data(),u,v)==want);}}}
 for(auto a:mem){free(a);}free(g.head);}}
int main(){test1();test2();test3();test4();test5();test6();puts("B01-B06: all 12 algorithms and state traces passed");}
'''

def main():
 TMP.mkdir(parents=True,exist_ok=True)
 chunks=[CPP]
 for i in range(1,7):
  path=BASE/f'C3-B-{i:02d}'/f'C3-B-{i:02d}-讲稿.md'
  raw=path.read_text(encoding='utf-8').split('## 附录二 完整代码',1)[1].split('## 附录三',1)[0]
  codes=re.findall(r'```cpp\n(.*?)\n```',raw,re.S)
  assert len(codes)>=2,(path,len(codes))
  code='\n'.join(codes)
  code=re.sub(r'^#include.*\n','',code,flags=re.M)
  chunks.append(f'namespace L{i} {{\n{code}\n}}\n')
 chunks.append(TEST)
 cpp=TMP/'b_lessons.cpp';exe=TMP/'b_lessons.exe'
 cpp.write_text('\n'.join(chunks),encoding='utf-8')
 compiler=os.environ.get('C3_GXX') or os.environ.get('CXX') or shutil.which('g++') or 'D:/Program Files/mingw64/bin/g++.exe'
 subprocess.run([compiler,'-std=c++17','-Wall','-Wextra','-O2',str(cpp),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)

if __name__=='__main__':main()
