#include <stddef.h>
typedef struct Node { struct Node *left, *right; } Node;

static int heightAndUpdate(const Node *p, int *best) {
    if (p == NULL) return -1;
    int left = heightAndUpdate(p->left, best);
    int right = heightAndUpdate(p->right, best);
    int through = left + right + 2;
    if (through > *best) *best = through;
    return (left > right ? left : right) + 1;
}

int treeDiameter(const Node *root) {
    int best = 0;
    heightAndUpdate(root, &best);
    return best;
}

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
static int bruteDiameter(int n, int adj[12][12]) {
    int best = 0;
    for (int start = 0; start < n; ++start) {
        int q[12], dist[12], front = 0, rear = 0;
        for (int i = 0; i < n; ++i) dist[i] = -1;
        dist[start] = 0; q[rear++] = start;
        while (front < rear) {
            int u = q[front++];
            for (int v = 0; v < n; ++v) if (adj[u][v] && dist[v] < 0) {
                dist[v] = dist[u] + 1; q[rear++] = v;
                if (dist[v] > best) best = dist[v];
            }
        }
    }
    return best;
}
int main(void) {
    assert(treeDiameter(NULL) == 0);
    srand(13);
    for (int rep = 0; rep < 400; ++rep) {
        int n = 1 + rand() % 12;
        Node nodes[12] = {0};
        int adj[12][12] = {{0}};
        for (int i = 1; i < n; ++i) {
            int parent;
            do { parent = rand() % i; }
            while (nodes[parent].left && nodes[parent].right);
            if (!nodes[parent].left && (!nodes[parent].right || rand() % 2))
                nodes[parent].left = &nodes[i];
            else
                nodes[parent].right = &nodes[i];
            adj[parent][i] = adj[i][parent] = 1;
        }
        assert(treeDiameter(&nodes[0]) == bruteDiameter(n, adj));
    }
    puts("S5-IV03 random-tree/all-pairs-distance checks pass");
    return 0;
}
