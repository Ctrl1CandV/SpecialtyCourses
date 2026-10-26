#include <stdlib.h>
#include <stdio.h>
typedef struct Node {
    int key;
    struct Node *next;
} Node;
void intersect(Node *A, const Node *B) {
    Node *pa = A->next;
    Node *tail = A;
    const Node *pb = B->next;
    A->next = NULL;
    while (pa != NULL && pb != NULL) {
        if (pa->key == pb->key) {
            Node *next = pa->next;
            tail->next = pa;
            tail = pa;
            pa = next;
            pb = pb->next;
        } else if (pa->key < pb->key) {
            Node *next = pa->next;
            free(pa);
            pa = next;
        } else {
            pb = pb->next;
        }
    }
    while (pa != NULL) {
        Node *next = pa->next;
        free(pa);
        pa = next;
    }
    tail->next = NULL;
}
void showIntersection(Node *A, const Node *B) {
    intersect(A, B);
    for (Node *p = A->next; p != NULL; p = p->next)
        printf("%d ", p->key);
    putchar('\n');
}