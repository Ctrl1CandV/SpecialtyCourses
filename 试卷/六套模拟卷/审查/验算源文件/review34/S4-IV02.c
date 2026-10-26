#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <limits.h>
#include <stdbool.h>
#include <stddef.h>
typedef struct Node {
    int key;
    struct Node *left, *right;
} Node;

bool closestKey(const Node *root, int x, int *out) {
    if (root == NULL) return false;
    bool have = false;
    long long bestDiff = 0;
    int bestKey = 0;
    for (const Node *p = root; p != NULL; ) {
        long long d = (long long)p->key - x;
        if (d < 0) d = -d;
        if (!have || d < bestDiff ||
            (d == bestDiff && p->key < bestKey)) {
            have = true;
            bestDiff = d;
            bestKey = p->key;
        }
        if (p->key == x) break;
        p = x < p->key ? p->left : p->right;
    }
    *out = bestKey;
    return true;
}

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
