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