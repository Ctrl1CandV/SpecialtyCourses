static void fillPost(const int pre[], const int in[],
                     int preLeft, int inLeft, int len,
                     int post[], int *out) {
    if (len == 0) return;
    int root = pre[preLeft];
    int split = inLeft;
    while (in[split] != root) ++split;  /* 题设保证遍历合法且标识互异 */
    int leftSize = split - inLeft;
    fillPost(pre, in, preLeft + 1, inLeft, leftSize, post, out);
    fillPost(pre, in, preLeft + 1 + leftSize, split + 1,
             len - leftSize - 1, post, out);
    post[(*out)++] = root;
}

void toPost(const int pre[], const int in[], int n, int post[]) {
    int out = 0;
    fillPost(pre, in, 0, 0, n, post, &out);
}

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
}