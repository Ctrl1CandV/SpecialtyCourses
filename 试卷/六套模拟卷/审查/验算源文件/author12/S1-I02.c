#include <stdio.h>
typedef struct Node {
    int data;
    struct Node *next;
} Node;
void insertBefore(Node *head, Node *p, Node *s) {
    Node *prev = head;
    while (prev->next != p)
        prev = prev->next;
    s->next = p;
    prev->next = s;
}
void printList(const Node *head) {
    const Node *p = head->next;
    while (p != NULL) {
        printf("%d", p->data);
        if (p->next != NULL) printf("->");
        p = p->next;
    }
    putchar('\n');
}
int main(void) {
    Node head = {0, NULL}, a = {4, NULL}, b = {9, NULL};
    Node s = {7, NULL}, t = {8, NULL};
    head.next = &a;
    a.next = &b;
    printList(&head);
    insertBefore(&head, &a, &s);
    insertBefore(&head, &b, &t);
    printList(&head);
    return 0;
}