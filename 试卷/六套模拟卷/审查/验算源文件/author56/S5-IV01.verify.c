#include <stddef.h>
#include <stdlib.h>
typedef struct Node { int key; struct Node *next; } Node;

void keepLastOfEachKey(Node *L) {
    Node *pre = L, *p = L->next;
    while (p != NULL) {
        while (p->next != NULL && p->key == p->next->key) {
            Node *old = p;
            p = p->next;
            pre->next = p;
            free(old);
        }
        pre = p;
        p = p->next;
    }
}

#include <assert.h>
#include <stdio.h>
int main(void) {
    Node empty = {0, NULL};
    keepLastOfEachKey(&empty);
    assert(empty.next == NULL);
    srand(11);
    for (int rep = 0; rep < 400; ++rep) {
        Node head = {0, NULL}, *tail = &head;
        Node *last[32] = {0};
        int key = 0, count = 1 + rand() % 24;
        for (int i = 0; i < count; ++i) {
            if (i != 0 && rand() % 3 == 0) ++key;
            Node *p = malloc(sizeof *p);
            assert(p != NULL);
            p->key = key; p->next = NULL;
            tail->next = p; tail = p;
            last[key] = p;
        }
        keepLastOfEachKey(&head);
        int prev = -1, actual = 0, expected = 0;
        for (int k = 0; k < 32; ++k) if (last[k]) ++expected;
        Node *p = head.next;
        while (p != NULL) {
            assert(p->key > prev && p == last[p->key]);
            prev = p->key; ++actual;
            Node *next = p->next; free(p); p = next;
        }
        assert(actual == expected);
    }
    puts("S5-IV01 random and boundary checks pass");
    return 0;
}
