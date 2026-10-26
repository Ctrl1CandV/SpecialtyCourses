#include <stdio.h>
typedef struct TNode {
    struct TNode *left, *right;
} TNode;
int heightIfBalanced(const TNode *t) {
    if (t == NULL) return 0;
    int a = heightIfBalanced(t->left);
    if (a < 0) return -1;
    int b = heightIfBalanced(t->right);
    if (b < 0) return -1;
    if (a - b > 1 || b - a > 1) return -1;
    return 1 + (a > b ? a : b);
}
int balanced(const TNode *t) {
    return heightIfBalanced(t) >= 0;
}
int main(void) {
    TNode x = {NULL, NULL}, y = {NULL, NULL};
    TNode root = {&x, &y};
    TNode p = {NULL, NULL}, q = {&p, NULL};
    TNode chain = {&q, NULL};
    printf("%d %d %d\n", balanced(&root),
           balanced(&chain), balanced(NULL));
    return 0;
}