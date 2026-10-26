#include <assert.h>
#include <stddef.h>
#include <stdlib.h>
#include <stdio.h>
typedef struct TNode {
    int data;
    struct TNode *left, *right;
} TNode;

static void scanBest(const TNode *p, long long sum,
                     long long *best, int *haveBest) {
    sum += p->data;
    if (p->left == 0 && p->right == 0) {
        if (!*haveBest || sum > *best) *best = sum;
        *haveBest = 1;
        return;
    }
    if (p->left != 0) scanBest(p->left, sum, best, haveBest);
    if (p->right != 0) scanBest(p->right, sum, best, haveBest);
}

static int savePath(const TNode *p, long long sum, long long best,
                    int path[], int depth, int *pathLen) {
    if (p == 0) return 0;
    path[depth] = p->data;
    sum += p->data;
    if (p->left == 0 && p->right == 0) {
        if (sum == best) {
            *pathLen = depth + 1;
            return 1;
        }
        return 0;
    }
    if (savePath(p->left, sum, best, path, depth + 1, pathLen)) return 1;
    return savePath(p->right, sum, best, path, depth + 1, pathLen);
}

int maxRootLeafSum(const TNode *root, int *path, int *pathLen) {
    long long best = 0;
    int haveBest = 0;
    *pathLen = 0;
    scanBest(root, 0, &best, &haveBest);  /* 题设 root 非空 */
    savePath(root, 0, best, path, 0, pathLen);
    return (int)best;                    /* 题设保证路径和在int范围内 */
}

static int oracleBest(const TNode *p) {
    if (!p->left && !p->right) return p->data;
    if (!p->left) return p->data + oracleBest(p->right);
    if (!p->right) return p->data + oracleBest(p->left);
    int a = oracleBest(p->left), b = oracleBest(p->right);
    return p->data + (a > b ? a : b);
}
static int validPath(const TNode *p, const int path[], int len) {
    if (!p || len <= 0 || p->data != path[0]) return 0;
    if (len == 1) return !p->left && !p->right;
    return validPath(p->left, path + 1, len - 1) ||
           validPath(p->right, path + 1, len - 1);
}
int main(void) {
    for (int trial = 0; trial < 400; ++trial) {
        TNode node[30] = {0}; int n = 1 + rand() % 30;
        for (int i = 0; i < n; ++i) node[i].data = rand() % 31 - 15;
        for (int i = 1; i < n; ++i) {
            int parent;
            do { parent = rand() % i; }
            while (node[parent].left && node[parent].right);
            if (!node[parent].left && !node[parent].right && rand() % 2)
                node[parent].right = &node[i];
            else if (!node[parent].left) node[parent].left = &node[i];
            else node[parent].right = &node[i];
        }
        int path[30], len = -1, got = maxRootLeafSum(node, path, &len);
        assert(got == oracleBest(node));
        assert(len >= 1 && len <= n && validPath(node, path, len));
        int sum = 0; for (int i = 0; i < len; ++i) sum += path[i];
        assert(sum == got);
    }
    puts("S1-IV02 400 cases OK");
}
