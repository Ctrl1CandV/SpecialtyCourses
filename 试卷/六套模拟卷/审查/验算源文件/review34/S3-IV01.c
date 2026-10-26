#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <limits.h>
#include <stddef.h>
typedef struct Node { int key; struct Node *next; } Node;

Node *mergeThree(Node *a, Node *b, Node *c) {
    Node *head = NULL;
    Node **tailNext = &head;
    while (a != NULL || b != NULL || c != NULL) {
        Node **pick = NULL;
        if (a != NULL) pick = &a;
        if (b != NULL && (pick == NULL || b->key < (*pick)->key))
            pick = &b;
        if (c != NULL && (pick == NULL || c->key < (*pick)->key))
            pick = &c;
        Node *p = *pick;
        *pick = p->next;
        *tailNext = p;
        tailNext = &p->next;
    }
    *tailNext = NULL;
    return head;
}

static unsigned seed=11;
static unsigned rnd(void){seed=seed*1664525u+1013904223u;return seed;}
static Node *make(Node *nodes,int n,int *v){for(int i=0;i<n;i++){nodes[i].key=v[i];nodes[i].next=(i+1<n?&nodes[i+1]:NULL);}return n?&nodes[0]:NULL;}
int main(void){
 for(int tc=0;tc<1000;tc++){
  Node a[30],b[30],c[30];int av[30],bv[30],cv[30],expected[90],na=rnd()%30,nb=rnd()%30,nc=rnd()%30,total=na+nb+nc;
  for(int j=0;j<3;j++){int *v=j==0?av:j==1?bv:cv;int n=j==0?na:j==1?nb:nc;int x=-20;for(int i=0;i<n;i++){x+=rnd()%4;v[i]=x;}}
  int p=0;for(int i=0;i<na;i++)expected[p++]=av[i];for(int i=0;i<nb;i++)expected[p++]=bv[i];for(int i=0;i<nc;i++)expected[p++]=cv[i];
  for(int i=0;i<total;i++)for(int j=i+1;j<total;j++)if(expected[j]<expected[i]){int t=expected[i];expected[i]=expected[j];expected[j]=t;}
  Node *out=mergeThree(make(a,na,av),make(b,nb,bv),make(c,nc,cv));int n=0,seen[90]={0};
  for(Node *q=out;q;q=q->next){assert(n<total);assert(q->key==expected[n++]);int found=0;for(int i=0;i<na;i++)if(q==&a[i]){assert(!seen[i]);seen[i]=1;found=1;}for(int i=0;i<nb;i++)if(q==&b[i]){assert(!seen[30+i]);seen[30+i]=1;found=1;}for(int i=0;i<nc;i++)if(q==&c[i]){assert(!seen[60+i]);seen[60+i]=1;found=1;}assert(found);}
  assert(n==total);
 }
 puts("S3-IV01 1000 random three-list merges OK");return 0;
}
