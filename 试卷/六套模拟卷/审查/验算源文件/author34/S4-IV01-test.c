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

#include <assert.h>
#include <stdio.h>
int main(void) {
  unsigned seed = 12345;
  for (int trial=0; trial<2000; ++trial) {
    seed=seed*1664525u+1013904223u; int n=(int)(seed%21);
    int values[21], kept[21], kc=0;
    Node *tail=NULL;
    for (int i=0;i<n;++i) {
      seed=seed*1664525u+1013904223u;
      values[i]=(int)(seed%11)-5;
      Node *p=malloc(sizeof *p); assert(p); p->key=values[i];
      if (!tail) { p->next=p; tail=p; }
      else { p->next=tail->next; tail->next=p; tail=p; }
    }
    seed=seed*1664525u+1013904223u; int a=(int)(seed%11)-5;
    seed=seed*1664525u+1013904223u; int b=(int)(seed%11)-5;
    if (a>b) {int z=a;a=b;b=z;}
    for(int i=0;i<n;++i) if(values[i]<a || values[i]>b) kept[kc++]=values[i];
    int removed=deleteRange(&tail,n,a,b);
    assert(removed==n-kc);
    if(kc==0) assert(tail==NULL);
    else {
      assert(tail!=NULL); Node *p=tail->next;
      for(int i=0;i<kc;++i) { assert(p->key==kept[i]); p=p->next; }
      assert(p==tail->next);
      p=tail->next;
      for(int i=0;i<kc;++i) {Node *next=p->next;free(p);p=next;}
    }
  }
  puts("2000 random circular lists passed"); return 0;
}
