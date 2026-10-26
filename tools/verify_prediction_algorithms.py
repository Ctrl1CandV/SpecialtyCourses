from pathlib import Path
import re,subprocess,json
root=Path(__file__).resolve().parents[1]
out=root/'试卷/2026机构押题'
work=root/'_tmp'/'prediction_checks';work.mkdir(parents=True,exist_ok=True)
gcc=r'D:\Program Files\mingw64\bin\gcc.exe'
sources={}
for paper in '一二三':
    md=(out/'源稿/可编辑答案'/f'押题卷{paper}参考答案.md').read_text(encoding='utf-8')
    alg=md.split('## 四、算法设计与分析题',1)[1]
    for i,code in enumerate(re.findall(r'```c\n(.*?)```',alg,re.S),1):sources[(paper,i)]=code
assert len(sources)==9
h={}
h['一',1]=r'''
#include <assert.h>
int main(void) {
 static long long a[MAXV+1][MAXV+1];
 static int path[MAXV+1][MAXV+1];
 long long expected[4][4]={{0,1,9,3},{11,0,8,2},
                         {3,4,0,6},{9,10,6,0}};
 for(int i=1;i<=4;i++) for(int j=1;j<=4;j++)
  a[i][j]=(i==j?0:INF);
 int e[][3]={{1,2,1},{1,4,4},{2,3,9},{2,4,2},
             {3,1,3},{3,2,5},{3,4,8},{4,3,6}};
 for(int i=0;i<8;i++) a[e[i][0]][e[i][1]]=e[i][2];
 Floyd(4,a,path);
 for(int i=1;i<=4;i++)for(int j=1;j<=4;j++)
  assert(a[i][j]==expected[i-1][j-1]);
 PrintAllPaths(4,a,path);
 a[1][2]=INF;PrintAllPaths(2,a,path);
 return 0;
}
'''
h['一',2]=r'''
#include <assert.h>
#include <string.h>
static void check(const char *s,int want) {
 size_t n=strlen(s);Node *a=calloc(n+1,sizeof *a);
 assert(a);for(size_t i=0;i<=n;i++)a[i].link=&a[(i+1)%(n+1)];
 for(size_t i=0;i<n;i++)a[i+1].ch=s[i];
 assert(bracketsMatch(a)==want);free(a);
}
int main(void) {
 check("",1);check("a+([{}])",1);check("([)]",0);
 check(")",0);check("((",0);check("abc",1);return 0;
}
'''
h['一',3]=r'''
#include <assert.h>
int main(void) {
 BSTNode a={1,1,NULL,NULL},c={3,1,NULL,NULL};
 BSTNode b={2,3,&a,&c};
 assert(selectK(&b,1)==&a);assert(selectK(&b,2)==&b);
 assert(selectK(&b,3)==&c);assert(!selectK(&b,0));
 assert(!selectK(&b,4));assert(!selectK(NULL,1));return 0;
}
'''
h['二',1]=r'''
#include <assert.h>
int main(void) {
 int p[30],c[30];for(int i=0;i<29;i++)p[i]=i+1;p[29]=-1;
 assert(levelsAndHeight(p,30,c)==30);
 for(int i=0;i<30;i++)assert(c[i]==30-i);
 int q[]={4,4,0,1,-1};int expected[]={2,2,3,3,1};
 assert(levelsAndHeight(q,5,c)==3);
 for(int i=0;i<5;i++)assert(c[i]==expected[i]);
 assert(levelsAndHeight(q,0,c)==0);return 0;
}
'''
h['二',2]=r'''
#include <assert.h>
int main(void) {
 HNode a={10,NULL,NULL},b={20,NULL,NULL},c={30,NULL,NULL};
 HNode d={50,&b,&c},r={60,&a,&d};
 assert(WPL(&r)==110);assert(WPL(&a)==0);assert(WPL(NULL)==0);
 return 0;
}
'''
h['二',3]=r'''
#include <assert.h>
int main(void) {
 Node head={0,NULL};int values[]={2,1,2,4,-1};
 for(int i=0;i<5;i++)insertSorted(&head,values[i]);
 int expected[]={-1,1,2,2,4};Node *p=head.link;
 for(int i=0;i<5;i++){assert(p&&p->element==expected[i]);p=p->link;}
 assert(!p);p=head.link;while(p){Node *q=p->link;free(p);p=q;}
 return 0;
}
'''
h['三',1]=r'''
#include <assert.h>
int main(void) {
 Node a={1,NULL},b={2,NULL},x={0,NULL},y={0,&a};a.link=&b;
 concatenate(&x,&y);assert(x.link==&a&&!y.link&&b.link==NULL);
 concatenate(&x,&y);assert(a.link==&b);
 Node c={3,NULL};y.link=&c;concatenate(&x,&y);
 assert(b.link==&c&&!y.link&&!c.link);
 Node empty={0,NULL};concatenate(&empty,&y);assert(!empty.link);
 return 0;
}
'''
h['三',2]=r'''
#include <assert.h>
int main(void) {
 Node a[4]={{3,NULL},{-1,NULL},{3,NULL},{0,NULL}},head={0,a};
 for(int i=0;i<3;i++)a[i].link=&a[i+1];
 selectionSort(&head);int expected[]={-1,0,3,3};
 for(int i=0;i<4;i++){
  assert(a[i].data==expected[i]);
  assert(a[i].link==(i==3?NULL:&a[i+1]));
 }
 Node empty={0,NULL};selectionSort(&empty);return 0;
}
'''
h['三',3]=r'''
#include <assert.h>
#include <stdlib.h>
int main(void) {
 srand(802);
 for(int run=0;run<200;run++) {
  int n=run%60;TNode a[60];int order[60];TNode *root=NULL;
  for(int i=0;i<n;i++){a[i]=(TNode){i,NULL,NULL};order[i]=i;}
  for(int i=n-1;i>0;i--){int j=rand()%(i+1),t=order[i];
   order[i]=order[j];order[j]=t;}
  for(int i=0;i<n;i++){
   TNode **p=&root;
   while(*p)p=a[order[i]].data<(*p)->data?&(*p)->lchild:&(*p)->rchild;
   *p=&a[order[i]];
  }
  TNode *left[60],*right[60];
  for(int i=0;i<n;i++){left[i]=a[i].lchild;right[i]=a[i].rchild;}
  captured_count=0;printNonIncreasing(root);assert(captured_count==n);
  for(int i=0;i<n;i++)assert(captured[i]==n-i-1);
  for(int i=0;i<n;i++)assert(a[i].lchild==left[i]&&a[i].rchild==right[i]);
 }
 return 0;
}
'''
prefix=r'''
#include <stdio.h>
#include <stdarg.h>
static int captured[100],captured_count;
static int capture_print(const char *fmt,...) {
 (void)fmt;va_list ap;va_start(ap,fmt);
 captured[captured_count++]=va_arg(ap,int);va_end(ap);return 0;
}
#define printf capture_print
'''
results=[]
for j,((paper,i),code) in enumerate(sources.items(),1):
    unit=work/f'algorithm_{j}.c';exe=unit.with_suffix('.exe')
    unit.write_text((prefix if (paper,i)==('三',3) else '')+code+h[paper,i],encoding='utf-8')
    r=subprocess.run([gcc,'-std=c11','-Wall','-Wextra','-Werror','-pedantic',str(unit),'-o',str(exe)],capture_output=True,text=True)
    assert r.returncode==0,(paper,i,r.stderr)
    run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=10)
    assert run.returncode==0,(paper,i,run.stderr)
    if (paper,i)==('一',1):
        assert '<1,3>: length=9, path=1 -> 2 -> 4 -> 3' in run.stdout
        assert '<1,1>: length=0, path=1' in run.stdout
        assert '<1,2>: unreachable' in run.stdout
    results.append({'paper':paper,'algorithm':i,'compile':'pass','functional':'pass'})
(work/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'algorithms':len(results),'all_pass':True,'morris_random_cases':200},ensure_ascii=False))
