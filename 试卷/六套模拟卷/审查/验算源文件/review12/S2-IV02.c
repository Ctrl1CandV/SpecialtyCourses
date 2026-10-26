#include <assert.h>
#include <stddef.h>
#include <stdlib.h>
#include <stdio.h>
#include <stddef.h>
typedef struct TNode {
    int data;
    int count;
    struct TNode *left, *right;
} TNode;

static int leafCount(TNode *p) {
    if (p == NULL) return 0;
    if (p->left == NULL && p->right == NULL) {
        p->count = 1;
        return 1;
    }
    int a = leafCount(p->left);
    int b = leafCount(p->right);
    p->count = a + b;
    return p->count;
}

void fillLeafCounts(TNode *root) {
    (void)leafCount(root);
}

static int oracleLeaves(TNode *p) {
    if (!p) return 0;
    if (!p->left && !p->right) return 1;
    return oracleLeaves(p->left) + oracleLeaves(p->right);
}
int main(void) {
    fillLeafCounts(0);
    for (int trial = 0; trial < 400; ++trial) {
        TNode node[30] = {0}; int n = 1 + rand() % 30;
        for (int i = 1; i < n; ++i) {
            int parent;
            do { parent = rand() % i; }
            while (node[parent].left && node[parent].right);
            if (!node[parent].left && !node[parent].right && rand() % 2)
                node[parent].right = &node[i];
            else if (!node[parent].left) node[parent].left = &node[i];
            else node[parent].right = &node[i];
        }
        fillLeafCounts(node);
        for (int i = 0; i < n; ++i) assert(node[i].count == oracleLeaves(&node[i]));
    }
    puts("S2-IV02 400 cases OK");
}
