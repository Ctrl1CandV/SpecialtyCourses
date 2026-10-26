#include <stddef.h>
typedef struct Node { int key; struct Node *next; } Node;

Node *mergeThree(Node *a, Node *b, Node *c) {
    Node *head = NULL;
    Node **tailNext = &head;
    while (a != NULL || b != NULL || c != NULL) {
        Node **pick = NULL;
        if (a != NULL) pick = &a;
        if (b != NULL && (pick == NULL || b->key < (*pick)->key))
            pick = &b;
        if (c != NULL && (pick == NULL || c->key < (*pick)->key))
            pick = &c;
        Node *p = *pick;
        *pick = p->next;
        *tailNext = p;
        tailNext = &p->next;
    }
    *tailNext = NULL;
    return head;
}
