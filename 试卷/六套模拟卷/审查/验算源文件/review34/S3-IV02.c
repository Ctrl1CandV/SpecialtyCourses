#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <limits.h>
#include <stdbool.h>
#include <stddef.h>
typedef struct Node {
    int data;
    bool mark;
    struct Node *left, *right;
} Node;

static void chooseLeaf(const Node *p, int depth, bool seenMark,
                       const Node **bestLeaf, int *bestLen) {
    if (p == NULL) return;
    ++depth;
    seenMark = seenMark || p->mark;
    if (p->left == NULL && p->right == NULL) {
        if (seenMark && depth > *bestLen) {
            *bestLen = depth;
            *bestLeaf = p;
        }
        return;
    }
    chooseLeaf(p->left, depth, seenMark, bestLeaf, bestLen);
    chooseLeaf(p->right, depth, seenMark, bestLeaf, bestLen);
}

static bool writeToLeaf(const Node *p, const Node *target,
                        const Node *out[], int *len) {
    if (p == NULL) return false;
    out[(*len)++] = p;
    if (p == target) return true;
    if (writeToLeaf(p->left, target, out, len) ||
        writeToLeaf(p->right, target, out, len)) return true;
    --*len;
    return false;
}

bool longestMarkedPath(const Node *root, const Node *out[], int *len) {
    const Node *leaf = NULL;
    int bestLen = 0;
    *len = 0;
    chooseLeaf(root, 0, false, &leaf, &bestLen);
    if (leaf == NULL) return false;
    return writeToLeaf(root, leaf, out, len);
}

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
