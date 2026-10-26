#include <stddef.h>
#include <stdio.h>
typedef struct Node {
    int key;
    struct Node *left, *right;
} Node;
int leafCount(const Node *t) {
    if (t == NULL) return 0;
    if (t->left == NULL && t->right == NULL) return 1;
    return leafCount(t->left) + leafCount(t->right);
}
int main(void) {
    Node nodes[7];
    for (int i = 0; i < 7; ++i) {
        nodes[i].key = i + 1;
        nodes[i].left = NULL;
        nodes[i].right = NULL;
    }
    nodes[0].left = &nodes[1];
    nodes[0].right = &nodes[2];
    nodes[1].left = &nodes[3];
    nodes[1].right = &nodes[4];
    nodes[2].right = &nodes[5];
    nodes[5].left = &nodes[6];
    printf("leaves=%d\n", leafCount(&nodes[0]));
    return 0;
}
