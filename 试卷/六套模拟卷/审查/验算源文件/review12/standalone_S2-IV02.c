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