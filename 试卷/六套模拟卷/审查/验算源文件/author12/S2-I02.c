#include <stdio.h>
typedef struct DNode {
    int data;
    struct DNode *prior, *next;
} DNode;
void swapWithPrior(DNode *p) {
    DNode *q = p->prior, *x = q->prior, *y = p->next;
    x->next = p;
    p->prior = x;
    p->next = q;
    q->prior = p;
    q->next = y;
    y->prior = q;
}
void printForward(const DNode *head, const DNode *tail) {
    const DNode *p = head->next;
    while (p != tail) {
        printf("%d ", p->data);
        p = p->next;
    }
    putchar('\n');
}
int main(void) {
    DNode head = {-1, NULL, NULL}, tail = {-1, NULL, NULL};
    DNode a = {10, NULL, NULL}, b = {20, NULL, NULL};
    head.next = &a; a.prior = &head;
    a.next = &b; b.prior = &a;
    b.next = &tail; tail.prior = &b;
    printForward(&head, &tail);
    swapWithPrior(&b);
    printForward(&head, &tail);
    printf("tail-prior=%d\n", tail.prior->data);
    return 0;
}