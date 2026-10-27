from pathlib import Path
import os, re, shutil, subprocess
root=Path(__file__).resolve().parents[4]
base=root/'课程/课件/C3'
parts=[]
for id in ['C3-A-01','C3-A-02']:
    md=(base/id/f'{id}-讲稿.md').read_text(encoding='utf-8')
    parts.extend(re.findall(r'```cpp\n(.*?)\n```',md,re.S))
source='\n'.join(parts)+r'''
#include <cassert>
#include <vector>
#include <set>
#include <algorithm>
#include <random>
#include <climits>
#include <iostream>
int main(){
  assert(FindEntry(NULL)==NULL);
  assert(FractionPoint(NULL,2)==NULL);
  assert(ThirdFloor(NULL)==NULL);
  long long tests=0;
  for(int n=0;n<=150;++n){
    std::vector<LNode> nodes(n+1);
    LinkList L=&nodes[0];
    for(int i=0;i<=n;++i){ nodes[i].data=1; nodes[i].next=(i<n?&nodes[i+1]:NULL); }
    assert(FindEntry(L)==NULL); ++tests;
    for(int k=-1;k<=n+3;++k){
      LNode *expected=(n==0 || k<1)?NULL:&nodes[(n+k-1)/k];
      assert(FractionPoint(L,k)==expected); ++tests;
    }
    assert(ThirdFloor(L)==(n<3?NULL:&nodes[n/3])); ++tests;
    for(int entry=1;entry<=n;++entry){
      nodes[n].next=&nodes[entry];
      assert(FindEntry(L)==&nodes[entry]); ++tests;
    }
  }
  std::mt19937 rng(8022027);
  for(int run=0;run<10000;++run){
    int n=run%81;
    std::vector<int> a(n);
    for(int &x:a) x=(int)(rng()%121)-30;
    if(n>2 && run%9==0){ a[0]=INT_MIN; a[1]=INT_MAX; }
    std::set<int> s(a.begin(),a.end());
    int missing=1; while(s.count(missing)) ++missing;
    assert(MissingPositive(a.data(),n)==missing); ++tests;
    int lo=(int)(rng()%50)-20, hi=lo+(int)(rng()%30);
    auto b=a; std::vector<int> expected;
    for(int x:a) if(x<lo || x>hi) expected.push_back(x);
    int count=RemoveRange(b.data(),n,lo,hi);
    assert(count==(int)expected.size());
    assert(std::equal(expected.begin(),expected.end(),b.begin())); ++tests;
    std::sort(a.begin(),a.end()); b=a;
    auto un=a; un.erase(std::unique(un.begin(),un.end()),un.end());
    count=UniqueSorted(b.data(),n);
    assert(count==(int)un.size() && std::equal(un.begin(),un.end(),b.begin())); ++tests;
    long long targets[]={(long long)(int(rng()%160)-40),2LL*INT_MIN,2LL*INT_MAX,-1,0,1};
    for(long long target:targets){
      bool found=false;
      for(int i=0;i<n;++i) for(int j=i+1;j<n;++j)
        if((long long)a[i]+a[j]==target) found=true;
      int i=-1,j=-1; bool got=TwoSumSorted(a.data(),n,target,i,j);
      assert(got==found);
      if(got) assert(0<=i && i<j && j<n && (long long)a[i]+a[j]==target);
      ++tests;
    }
    int M=run%53;
    for(int &x:a) x=(int)(rng()%(M+1));
    b=a;
    expected.clear(); s.clear();
    for(int x:a) if(s.insert(x).second) expected.push_back(x);
    count=UniqueBounded(b.data(),n,M);
    assert(count==(int)expected.size() && std::equal(expected.begin(),expected.end(),b.begin())); ++tests;
  }
  std::cout << "A lesson checks passed: " << tests << " cases\n";
}
'''
cpp=root/'_tmp/c3_revision/a_verify.cpp'
cpp.parent.mkdir(parents=True,exist_ok=True)
cpp.write_text(source,encoding='utf-8')
exe=cpp.with_suffix('.exe')
compiler=os.environ.get('C3_GXX') or os.environ.get('CXX') or shutil.which('g++') or 'D:/Program Files/mingw64/bin/g++.exe'
subprocess.run([compiler,'-std=c++17','-Wall','-Wextra','-Werror','-pedantic',str(cpp),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)

