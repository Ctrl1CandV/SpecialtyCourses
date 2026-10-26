#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>
#include <stddef.h>
typedef struct TNode {
    int data;
    int count;
    struct TNode *left, *right;
} TNode;

static int leafCount(TNode *p) {
    if (p == NULL) return 0;
    if (p->left == NULL && p->right == NULL) {
        p->count = 1;
        return 1;
    }
    int a = leafCount(p->left);
    int b = leafCount(p->right);
    p->count = a + b;
    return p->count;
}

void fillLeafCounts(TNode *root) {
    (void)leafCount(root);
}

static unsigned z=121;
static unsigned rnd(void){z=z*1664525u+1013904223u;return z;}
static TNode t[50];
static int ref(TNode *p){if(!p)return 0;if(!p->left&&!p->right)return 1;return ref(p->left)+ref(p->right);}
int main(void){
 fillLeafCounts(NULL);
 for(int tc=0;tc<1000;tc++){
  int n=1+rnd()%45;for(int i=0;i<n;i++){t[i].left=t[i].right=NULL;t[i].count=-1;}
  for(int i=1;i<n;i++){int k=rnd()%i;while(t[k].left&&t[k].right)k=(k+1)%i;if(!t[k].left)t[k].left=&t[i];else t[k].right=&t[i];}
  fillLeafCounts(&t[0]);for(int i=0;i<n;i++)assert(t[i].count==ref(&t[i]));
 }
 puts("S2-IV02 OK 1000 random trees");return 0;
}
