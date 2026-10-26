#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <limits.h>
#include <stdlib.h>
typedef struct Node { int key; struct Node *next; } Node;

int deleteRange(Node **tailRef, int n, int a, int b) {
    if (n == 0) return 0;
    Node *cur = (*tailRef)->next;
    (*tailRef)->next = NULL;  /* 暂时展开环 */
    Node *first = NULL, *last = NULL;
    int deleted = 0;
    for (int i = 0; i < n; ++i) {
        Node *next = cur->next;
        if (a <= cur->key && cur->key <= b) {
            free(cur);
            ++deleted;
        } else {
            if (first == NULL) first = cur;
            else last->next = cur;
            last = cur;
        }
        cur = next;
    }
    if (last == NULL) {
        *tailRef = NULL;
    } else {
        last->next = first;
        *tailRef = last;
    }
    return deleted;
}

static unsigned seed=41;
static unsigned rnd(void){seed=seed*1664525u+1013904223u;return seed;}
int main(void){
 for(int tc=0;tc<1000;tc++){
  int n=rnd()%70,a=(int)(rnd()%21)-10,b=a+rnd()%20,v[70],expected[70],remaining=0;
  Node *tail=NULL,*first=NULL;for(int i=0;i<n;i++){v[i]=(int)(rnd()%31)-15;Node *p=malloc(sizeof(Node));p->key=v[i];if(tail)tail->next=p;else first=p;tail=p;}if(tail)tail->next=first;
  for(int i=0;i<n;i++){
   if(v[i]<a||v[i]>b)expected[remaining++]=v[i];
  }
  int removed=deleteRange(&tail,n,a,b);assert(removed==n-remaining);
  if(remaining==0)assert(tail==NULL);else{assert(tail&&tail->next);Node *first=tail->next,*p=first;for(int i=0;i<remaining;i++){assert(p&&p->key==expected[i]);p=p->next;}assert(p==first);p=first;for(int i=0;i<remaining;i++){Node *next=p->next;free(p);p=next;}}
 }
 puts("S4-IV01 1000 random circular-list deletions OK");return 0;
}
