#include <stddef.h>
#include <stdlib.h>
typedef struct Node { int key; struct Node *next; } Node;

Node *symmetricDiff(Node *A, Node *B) {
    Node dummy = {0, NULL};
    Node *tail = &dummy;
    while (A != NULL && B != NULL) {
        if (A->key < B->key) {
            Node *p = A;
            A = A->next;
            p->next = NULL;
            tail->next = p;
            tail = p;
        } else if (B->key < A->key) {
            Node *p = B;
            B = B->next;
            p->next = NULL;
            tail->next = p;
            tail = p;
        } else {
            Node *oldA = A, *oldB = B;
            A = A->next;
            B = B->next;
            free(oldA);
            free(oldB);
        }
    }
    tail->next = (A != NULL ? A : B);
    return dummy.next;
}

#include <assert.h>
#include <stdio.h>
int main(void) {
    assert(symmetricDiff(NULL, NULL) == NULL);
    srand(14);
    for (int rep = 0; rep < 400; ++rep) {
        Node *A = NULL, *B = NULL, **ta = &A, **tb = &B;
        Node *expected[30] = {0};
        int common[30] = {0}, membershipA[30] = {0}, membershipB[30] = {0};
        for (int key = 0; key < 30; ++key) {
            membershipA[key] = rand() % 2;
            membershipB[key] = rand() % 2;
            if (membershipA[key]) {
                Node *p = malloc(sizeof *p); assert(p);
                p->key = key; p->next = NULL; *ta = p; ta = &p->next;
                expected[key] = p;
            }
            if (membershipB[key]) {
                Node *p = malloc(sizeof *p); assert(p);
                p->key = key; p->next = NULL; *tb = p; tb = &p->next;
                if (!membershipA[key]) expected[key] = p;
            }
            common[key] = membershipA[key] && membershipB[key];
        }
        Node *out = symmetricDiff(A, B);
        int prev = -1, count = 0, want = 0;
        for (int k = 0; k < 30; ++k) if ((membershipA[k] != 0) != (membershipB[k] != 0)) ++want;
        while (out) {
            assert(out->key > prev && out == expected[out->key] && !common[out->key]);
            prev = out->key; ++count;
            Node *next = out->next; free(out); out = next;
        }
        assert(count == want);
    }
    puts("S6-IV01 random-set/surviving-node-identity checks pass");
    return 0;
}
