#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>
typedef struct TNode {
    int data;
    struct TNode *left, *right;
} TNode;

static void scanBest(const TNode *p, long long sum,
                     long long *best, int *haveBest) {
    sum += p->data;
    if (p->left == 0 && p->right == 0) {
        if (!*haveBest || sum > *best) *best = sum;
        *haveBest = 1;
        return;
    }
    if (p->left != 0) scanBest(p->left, sum, best, haveBest);
    if (p->right != 0) scanBest(p->right, sum, best, haveBest);
}

static int savePath(const TNode *p, long long sum, long long best,
                    int path[], int depth, int *pathLen) {
    if (p == 0) return 0;
    path[depth] = p->data;
    sum += p->data;
    if (p->left == 0 && p->right == 0) {
        if (sum == best) {
            *pathLen = depth + 1;
            return 1;
        }
        return 0;
    }
    if (savePath(p->left, sum, best, path, depth + 1, pathLen)) return 1;
    return savePath(p->right, sum, best, path, depth + 1, pathLen);
}

int maxRootLeafSum(const TNode *root, int *path, int *pathLen) {
    long long best = 0;
    int haveBest = 0;
    *pathLen = 0;
    scanBest(root, 0, &best, &haveBest);  /* 题设 root 非空 */
    savePath(root, 0, best, path, 0, pathLen);
    return (int)best;                    /* 题设保证路径和在int范围内 */
}

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
