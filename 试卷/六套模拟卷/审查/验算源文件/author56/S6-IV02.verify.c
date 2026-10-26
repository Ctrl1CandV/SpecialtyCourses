static void fillPost(const int pre[], const int in[],
                     int preLeft, int inLeft, int len,
                     int post[], int *out) {
    if (len == 0) return;
    int root = pre[preLeft];
    int split = inLeft;
    while (in[split] != root) ++split;  /* 题设保证遍历合法且标识互异 */
    int leftSize = split - inLeft;
    fillPost(pre, in, preLeft + 1, inLeft, leftSize, post, out);
    fillPost(pre, in, preLeft + 1 + leftSize, split + 1,
             len - leftSize - 1, post, out);
    post[(*out)++] = root;
}

void toPost(const int pre[], const int in[], int n, int post[]) {
    int out = 0;
    fillPost(pre, in, 0, 0, n, post, &out);
}

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
typedef struct TestNode { int key, left, right; } TestNode;
static TestNode nodes[16];
static int pre[16], in[16], want[16], post[16], pc, ic, wc;
static void emitPre(int x) {
    if (x < 0) return;
    pre[pc++] = nodes[x].key;
    emitPre(nodes[x].left); emitPre(nodes[x].right);
}
static void emitIn(int x) {
    if (x < 0) return;
    emitIn(nodes[x].left); in[ic++] = nodes[x].key; emitIn(nodes[x].right);
}
static void emitPost(int x) {
    if (x < 0) return;
    emitPost(nodes[x].left); emitPost(nodes[x].right);
    want[wc++] = nodes[x].key;
}
int main(void) {
    toPost(NULL, NULL, 0, NULL);
    srand(15);
    for (int rep = 0; rep < 400; ++rep) {
        int n = 1 + rand() % 15;
        for (int i = 0; i < n; ++i)
            nodes[i] = (TestNode){100 + 3*i, -1, -1};
        for (int i = 1; i < n; ++i) {
            int p; do { p = rand() % i; }
            while (nodes[p].left >= 0 && nodes[p].right >= 0);
            if (nodes[p].left < 0 && (nodes[p].right >= 0 || rand()%2))
                nodes[p].left = i;
            else
                nodes[p].right = i;
        }
        pc = ic = wc = 0;
        emitPre(0); emitIn(0); emitPost(0);
        assert(pc == n && ic == n && wc == n);
        toPost(pre, in, n, post);
        for (int i = 0; i < n; ++i) assert(post[i] == want[i]);
    }
    puts("S6-IV02 random-tree/pre-in-post checks pass");
    return 0;
}
