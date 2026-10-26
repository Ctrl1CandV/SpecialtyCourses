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