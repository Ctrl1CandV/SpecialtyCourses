#include <assert.h>
#include <stddef.h>
#include <stdlib.h>
#include <stdio.h>
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

int main(void) {
    for (int trial = 0; trial < 300; ++trial) {
        Node ah = {0, 0}, bh = {0, 0}, *at = &ah, *bt = &bh;
        int expected[50], en = 0, na = rand() % 25, nb = rand() % 25;
        int av[25], bv[25];
        for (int i = 0; i < na; ++i) av[i] = i * 3 - 20;
        for (int i = 0; i < nb; ++i) bv[i] = i * 2 - 20;
        for (int i = 0; i < na; ++i) {
            Node *x = malloc(sizeof(*x)); x->data = av[i]; x->next = 0;
            at->next = x; at = x;
            int has = 0;
            for (int j = 0; j < nb; ++j) if (av[i] == bv[j]) has = 1;
            if (!has) expected[en++] = av[i];
        }
        for (int i = 0; i < nb; ++i) {
            Node *x = malloc(sizeof(*x)); x->data = bv[i]; x->next = 0;
            bt->next = x; bt = x;
        }
        listDifference(&ah, &bh);
        Node *p = ah.next;
        for (int i = 0; i < en; ++i) { assert(p && p->data == expected[i]); p = p->next; }
        assert(!p);
        p = bh.next;
        for (int i = 0; i < nb; ++i) { assert(p && p->data == bv[i]); p = p->next; }
        assert(!p);
        while (ah.next) { p = ah.next; ah.next = p->next; free(p); }
        while (bh.next) { p = bh.next; bh.next = p->next; free(p); }
    }
    puts("S1-IV01 300 cases OK");
}
