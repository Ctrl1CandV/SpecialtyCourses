#include <stddef.h>
#include <stdlib.h>
typedef struct Node { int key; struct Node *next; } Node;

void keepLastOfEachKey(Node *L) {
    Node *pre = L, *p = L->next;
    while (p != NULL) {
        while (p->next != NULL && p->key == p->next->key) {
            Node *old = p;
            p = p->next;
            pre->next = p;
            free(old);
        }
        pre = p;
        p = p->next;
    }
}

#include <assert.h>
#include <stdio.h>
static unsigned r=1729u;
static unsigned rng(void){r=r*1664525u+1013904223u;return r;}
int main(void){
  for(int trial=0;trial<4000;trial++){
    Node *head=malloc(sizeof *head); assert(head); head->next=NULL;
    Node *tail=head; int vals[50],len=rng()%50;
    for(int i=0;i<len;i++){vals[i]= i? vals[i-1]+(int)(rng()%2): (int)(rng()%5);Node *p=malloc(sizeof *p);assert(p);p->key=vals[i];p->next=NULL;tail->next=p;tail=p;}
    keepLastOfEachKey(head);
    Node *p=head->next;
    for(int i=0;i<len;i++) if(i==len-1||vals[i]!=vals[i+1]){assert(p&&p->key==vals[i]);p=p->next;}
    assert(!p);p=head->next;
    while(p){Node *next=p->next;free(p);p=next;}
    free(head);
  }
  puts("S5-IV01 PASS 4000 sorted random lists");return 0;
}