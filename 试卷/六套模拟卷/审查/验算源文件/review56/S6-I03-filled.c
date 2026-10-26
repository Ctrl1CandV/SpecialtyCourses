#include <stddef.h>
typedef struct Node { struct Node *left, *right; } Node;
typedef struct Queue Queue;
int empty(const Queue *q);
int size(const Queue *q);
Node *dequeue(Queue *q);
void enqueue(Queue *q, Node *p);
int weightedLeaves(Node *root, Queue *q) {
    if (root == NULL) return 0;
    enqueue(q, root);
    int total = 0, level = 1;
    while (!empty(q)) {
        int count = size(q);
        int leaves = 0;
        for (int j = 0; j < count; ++j) {
            Node *p = dequeue(q);
            if (p->left == NULL && p->right == NULL) ++leaves;
            if (p->left != NULL) enqueue(q, p->left);
            if (p->right != NULL) enqueue(q, p->right);
        }
        total += leaves * level;
        ++level;
    }
    return total;
}
int sample(Queue *q) {
    Node a = {NULL, NULL}, b = {NULL, NULL};
    Node c = {NULL, NULL};
    Node left = {&a, &b}, root = {&left, &c};
    return weightedLeaves(&root, q);
}
