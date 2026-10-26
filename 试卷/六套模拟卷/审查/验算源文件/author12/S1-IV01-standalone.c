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