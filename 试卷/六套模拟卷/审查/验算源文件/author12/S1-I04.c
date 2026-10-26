#include <stdio.h>
typedef struct TNode {
    int data;
    struct TNode *left, *right;
} TNode;
int leafCount(const TNode *t) {
    if (t == NULL) return 0;
    if (t->left == NULL && t->right == NULL)
        return 1;
    return leafCount(t->left) + leafCount(t->right);
}
void report(const char *name, const TNode *root) {
    printf("%s: %d\n", name, leafCount(root));
}
int main(void) {
    TNode d = {4, NULL, NULL};
    TNode e = {5, NULL, NULL};
    TNode b = {2, &d, &e};
    TNode c = {3, NULL, NULL};
    TNode a = {1, &b, &c};
    report("tree", &a);
    report("single", &c);
    report("empty", NULL);
    return 0;
}