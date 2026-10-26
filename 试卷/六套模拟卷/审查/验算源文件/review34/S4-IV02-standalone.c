#include <stdbool.h>
#include <stddef.h>
typedef struct Node {
    int key;
    struct Node *left, *right;
} Node;

bool closestKey(const Node *root, int x, int *out) {
    if (root == NULL) return false;
    bool have = false;
    long long bestDiff = 0;
    int bestKey = 0;
    for (const Node *p = root; p != NULL; ) {
        long long d = (long long)p->key - x;
        if (d < 0) d = -d;
        if (!have || d < bestDiff ||
            (d == bestDiff && p->key < bestKey)) {
            have = true;
            bestDiff = d;
            bestKey = p->key;
        }
        if (p->key == x) break;
        p = x < p->key ? p->left : p->right;
    }
    *out = bestKey;
    return true;
}