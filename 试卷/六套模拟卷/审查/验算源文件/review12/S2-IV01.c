#include <assert.h>
#include <stddef.h>
#include <stdlib.h>
#include <stdio.h>
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

int main(void) {
    for (int trial = 0; trial < 400; ++trial) {
        Node h = {0, 0}, a[40]; int neg[40], nonneg[40], nn = 0, np = 0;
        int n = rand() % 41;
        for (int i = 0; i < n; ++i) {
            a[i].data = rand() % 21 - 10;
            a[i].next = i + 1 < n ? &a[i+1] : 0;
            if (a[i].data < 0) neg[nn++] = a[i].data;
            else nonneg[np++] = a[i].data;
        }
        h.next = n ? a : 0;
        stableNegFirst(&h);
        Node *p = h.next;
        for (int i = 0; i < nn; ++i) { assert(p && p->data == neg[i]); p = p->next; }
        for (int i = 0; i < np; ++i) { assert(p && p->data == nonneg[i]); p = p->next; }
        assert(!p);
    }
    puts("S2-IV01 400 cases OK");
}
