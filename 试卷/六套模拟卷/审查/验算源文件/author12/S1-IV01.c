#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>
#include <stdlib.h>
typedef struct Node {
    int data;
    struct Node *next;
} Node;

void listDifference(Node *A, const Node *B) {
    Node *prev = A, *pa = A->next;
    const Node *pb = B->next;
    while (pa != NULL && pb != NULL) {
        if (pa->data < pb->data) {
            prev = pa;
            pa = pa->next;
        } else if (pa->data > pb->data) {
            pb = pb->next;
        } else {
            Node *old = pa;
            pa = pa->next;
            prev->next = pa;
            free(old);
            pb = pb->next;
        }
    }
}

static unsigned z=27;
static unsigned rnd(void){z=z*1664525u+1013904223u;return z;}
static Node *make(const int a[],int n){Node *h=calloc(1,sizeof(Node)),*p=h;for(int i=0;i<n;i++){p->next=malloc(sizeof(Node));p=p->next;p->data=a[i];p->next=NULL;}return h;}
static void destroy(Node *p){while(p){Node *q=p->next;free(p);p=q;}}
int main(void){
 for(int tc=0;tc<1000;tc++){
  int a[40],b[40],m=0,n=0;
  for(int v=-20;v<20;v++){if(rnd()%3==0)a[m++]=v;if(rnd()%4==0)b[n++]=v;}
  Node *A=make(a,m),*B=make(b,n);listDifference(A,B);
  Node *p=A->next;int j=0;
  for(int i=0;i<m;i++){while(j<n&&b[j]<a[i])j++;if(j<n&&b[j]==a[i])continue;assert(p&&p->data==a[i]);p=p->next;}
  assert(p==NULL);Node *q=B->next;for(int i=0;i<n;i++){assert(q&&q->data==b[i]);q=q->next;}assert(q==NULL);
  destroy(A);destroy(B);
 }
 puts("S1-IV01 OK 1000 random cases");return 0;
}
