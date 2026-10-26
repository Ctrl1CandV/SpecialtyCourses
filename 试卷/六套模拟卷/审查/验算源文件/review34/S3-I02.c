#include <stddef.h>
#include <stdio.h>
typedef struct Node {
    int key;
    char tag;
    struct Node *next;
} Node;

void selectionSort(Node *head) {
    for (Node *p = head->next; p != NULL; p = p->next) {
        Node *best = p;
        for (Node *q = p->next; q != NULL; q = q->next) {
            if (q->key < best->key) best = q;
        }
        if (best != p) {
            int key = p->key;
            char tag = p->tag;
            p->key = best->key;
            p->tag = best->tag;
            best->key = key;
            best->tag = tag;
        }
    }
}
int main(void) {
    Node nodes[4] = {
        {4, 'a', NULL}, {2, '-', NULL},
        {4, 'b', NULL}, {1, '-', NULL}
    };
    for (int i = 0; i < 3; ++i) nodes[i].next = &nodes[i + 1];
    Node head = {0, '-', &nodes[0]};
    selectionSort(&head);
    for (Node *p = head.next; p != NULL; p = p->next)
        printf("(%d,%c) ", p->key, p->tag);
    putchar('\n');
    return 0;
}