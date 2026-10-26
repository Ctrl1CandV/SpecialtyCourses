#include <stdio.h>
#include <stdlib.h>
typedef struct Node { int data; struct Node *next; } Node;
void removeEven(Node *head) {
    Node *pre = head, *p = head->next;
    while (p != NULL) {
        if (p->data % 2 == 0) {
            pre->next = p->next;
            free(p);
            p = pre->next;
        } else {
            pre = p;
            p = p->next;
        }
    }
}
int main(void) {
    Node head = {0, NULL};
    const int input[] = {3, 8, 5, 6, 7};
    Node *tail = &head;
    for (int i = 0; i < 5; ++i) {
        Node *node = malloc(sizeof *node);
        if (node == NULL) exit(EXIT_FAILURE);
        node->data = input[i]; node->next = NULL;
        tail->next = node; tail = node;
    }
    removeEven(&head);
    Node *p = head.next;
    while (p != NULL) {
        Node *next = p->next;
        printf("%d ", p->data);
        free(p);
        p = next;
    }
    putchar('\n');
    return 0;
}
