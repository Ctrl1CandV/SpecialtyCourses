#include <stdbool.h>
#include <stddef.h>
typedef struct Node {
    int data;
    bool mark;
    struct Node *left, *right;
} Node;

static void chooseLeaf(const Node *p, int depth, bool seenMark,
                       const Node **bestLeaf, int *bestLen) {
    if (p == NULL) return;
    ++depth;
    seenMark = seenMark || p->mark;
    if (p->left == NULL && p->right == NULL) {
        if (seenMark && depth > *bestLen) {
            *bestLen = depth;
            *bestLeaf = p;
        }
        return;
    }
    chooseLeaf(p->left, depth, seenMark, bestLeaf, bestLen);
    chooseLeaf(p->right, depth, seenMark, bestLeaf, bestLen);
}

static bool writeToLeaf(const Node *p, const Node *target,
                        const Node *out[], int *len) {
    if (p == NULL) return false;
    out[(*len)++] = p;
    if (p == target) return true;
    if (writeToLeaf(p->left, target, out, len) ||
        writeToLeaf(p->right, target, out, len)) return true;
    --*len;
    return false;
}

bool longestMarkedPath(const Node *root, const Node *out[], int *len) {
    const Node *leaf = NULL;
    int bestLen = 0;
    *len = 0;
    chooseLeaf(root, 0, false, &leaf, &bestLen);
    if (leaf == NULL) return false;
    return writeToLeaf(root, leaf, out, len);
}