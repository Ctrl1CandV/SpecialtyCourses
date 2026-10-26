#include <stddef.h>
#include <stdlib.h>
typedef struct Node { int key; struct Node *next; } Node;

Node *symmetricDiff(Node *A, Node *B) {
    Node dummy = {0, NULL};
    Node *tail = &dummy;
    while (A != NULL && B != NULL) {
        if (A->key < B->key) {
            Node *p = A;
            A = A->next;
            p->next = NULL;
            tail->next = p;
            tail = p;
        } else if (B->key < A->key) {
            Node *p = B;
            B = B->next;
            p->next = NULL;
            tail->next = p;
            tail = p;
        } else {
            Node *oldA = A, *oldB = B;
            A = A->next;
            B = B->next;
            free(oldA);
            free(oldB);
        }
    }
    tail->next = (A != NULL ? A : B);
    return dummy.next;
}

#include <assert.h>
#include <stdio.h>
static unsigned r=6729u;
static unsigned rng(void){r=r*1664525u+1013904223u;return r;}
static Node *make(const int x[],int n){Node *head=NULL,*tail=NULL;for(int i=0;i<n;i++){Node *p=malloc(sizeof *p);assert(p);p->key=x[i];p->next=NULL;if(!head)head=p;else tail->next=p;tail=p;}return head;}
int main(void){
  for(int trial=0;trial<4000;trial++){
    int a[25],b[25],na=(int)(rng()%25),nb=(int)(rng()%25),xa=0,xb=0;
    for(int i=0;i<na;i++){xa+=(int)(rng()%3)+1;a[i]=xa;}
    for(int i=0;i<nb;i++){xb+=(int)(rng()%3)+1;b[i]=xb;}
    Node *out=symmetricDiff(make(a,na),make(b,nb));
    int i=0,j=0;Node *p=out;
    while(i<na||j<nb){
      if(i<na && j<nb && a[i]==b[j]){i++;j++;continue;}
      int v;if(j==nb || (i<na&&a[i]<b[j]))v=a[i++];else v=b[j++];
      assert(p&&p->key==v);p=p->next;
    }
    assert(!p);p=out;while(p){Node *next=p->next;free(p);p=next;}
  }
  puts("S6-IV01 PASS 4000 random sorted-list symmetric differences");return 0;
}