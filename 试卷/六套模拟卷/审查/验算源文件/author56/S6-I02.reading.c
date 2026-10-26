#define main original_main
#include <stdio.h>
#include <stdlib.h>
typedef struct Node { int key; struct Node *next; } Node;
Node *fromArray(const int x[], int n) {
    Node dummy = {0, NULL}, *tail = &dummy;
    for (int i = 0; i < n; ++i) {
        Node *p = malloc(sizeof *p);
        if (p == NULL) exit(EXIT_FAILURE);
        p->key = x[i]; p->next = NULL;
        tail->next = p; tail = p;
    }
    return dummy.next;
}
Node *mergeReverse(Node *a, Node *b) {
    Node *out = NULL, *p;
    while (a != NULL || b != NULL) {
        if (b == NULL || (a != NULL && a->key <= b->key)) {
            p = a; a = a->next;
        } else {
            p = b; b = b->next;
        }
        p->next = out;
        out = p;
    }
    return out;
}
int main(void) {
    const int x[] = {1, 3, 3}, y[] = {2, 3, 4};
    Node *a = fromArray(x, 3), *b = fromArray(y, 3);
    Node *p = mergeReverse(a, b);
    while (p != NULL) {
        Node *next = p->next;
        printf("%d ", p->key);
        free(p); p = next;
    }
    putchar('\n');
    return 0;
}
#undef main

#include <assert.h>
int main(void) {
    assert(original_main() == 0);
    assert(mergeReverse(NULL, NULL) == NULL);
    Node a = {3, NULL}, b = {3, NULL};
    Node *out = mergeReverse(&a, &b);
    assert(out == &b && out->next == &a);
    return 0;
}
