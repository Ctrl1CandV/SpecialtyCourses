#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>
#include <stddef.h>
typedef struct Node {
    int data;
    struct Node *next;
} Node;

void stableNegFirst(Node *L) {
    Node neg = {0, NULL}, nonneg = {0, NULL};
    Node *tn = &neg, *tp = &nonneg;
    Node *p = L->next;
    while (p != NULL) {
        Node *next = p->next;
        p->next = NULL;
        if (p->data < 0) {
            tn->next = p;
            tn = p;
        } else {
            tp->next = p;
            tp = p;
        }
        p = next;
    }
    tn->next = nonneg.next;
    L->next = neg.next;
}

static unsigned z=77;
static unsigned rnd(void){z=z*1664525u+1013904223u;return z;}
int main(void){
 for(int tc=0;tc<1000;tc++){
  Node head={0,NULL},*tail=&head;int a[100],n=rnd()%100;
  for(int i=0;i<n;i++){a[i]=(int)(rnd()%21)-10;tail->next=malloc(sizeof(Node));tail=tail->next;tail->data=a[i];tail->next=NULL;}
  stableNegFirst(&head);Node *p=head.next;for(int phase=0;phase<2;phase++)for(int i=0;i<n;i++)if((a[i]<0)==(phase==0)){assert(p&&p->data==a[i]);p=p->next;}assert(p==NULL);
  p=head.next;while(p){Node *q=p->next;free(p);p=q;}
 }
 puts("S2-IV01 OK 1000 random lists");return 0;
}
