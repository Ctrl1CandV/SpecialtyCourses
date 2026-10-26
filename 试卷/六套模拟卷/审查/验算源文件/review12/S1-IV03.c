#include <assert.h>
#include <stddef.h>
#include <stdlib.h>
#include <stdio.h>
typedef struct Arc {
    int to;
    struct Arc *next;
} Arc;
typedef struct {
    int V, E;
    Arc **head;
} Graph;

static int dfsAvoid(const Graph *G, int u, int t, int w,
                    unsigned char seen[100], int path[],
                    int depth, int *pathLen) {
    seen[u] = 1;
    path[depth] = u;
    if (u == t) {
        *pathLen = depth + 1;
        return 1;
    }
    for (const Arc *e = G->head[u]; e != 0; e = e->next) {
        int v = e->to;
        if (v != w && !seen[v] &&
            dfsAvoid(G, v, t, w, seen, path, depth + 1, pathLen))
            return 1;
    }
    return 0;
}

int pathAvoidingVertex(const Graph *G, int s, int t, int w,
                       int *path, int *pathLen) {
    unsigned char seen[100] = {0};
    *pathLen = 0;
    return dfsAvoid(G, s, t, w, seen, path, 0, pathLen);
}

static int oracleReach(int n, int adj[12][12], int s, int t, int w) {
    int seen[12] = {0}, q[12], front = 0, rear = 0;
    seen[s] = 1; q[rear++] = s;
    while (front < rear) {
        int u = q[front++]; if (u == t) return 1;
        for (int v = 0; v < n; ++v)
            if (v != w && adj[u][v] && !seen[v]) { seen[v] = 1; q[rear++] = v; }
    }
    return 0;
}
int main(void) {
    for (int trial = 0; trial < 400; ++trial) {
        int n = 3 + rand() % 9, adj[12][12] = {0};
        Arc arc[150]; Arc *head[12] = {0}; int ec = 0, undirected = 0;
        for (int u = 0; u < n; ++u) for (int v = u + 1; v < n; ++v)
            if (rand() % 3 == 0) {
                adj[u][v] = adj[v][u] = 1; ++undirected;
                arc[ec] = (Arc){v, head[u]}; head[u] = &arc[ec++];
                arc[ec] = (Arc){u, head[v]}; head[v] = &arc[ec++];
            }
        Graph g = {n, undirected, head};
        int s = rand() % n, t, w, path[12], len = -1;
        do { t = rand() % n; } while (t == s);
        do { w = rand() % n; } while (w == s || w == t);
        int got = pathAvoidingVertex(&g, s, t, w, path, &len);
        assert(got == oracleReach(n, adj, s, t, w));
        if (!got) assert(len == 0);
        else {
            int seen[12] = {0}; assert(len >= 2 && len <= n);
            assert(path[0] == s && path[len-1] == t);
            for (int i = 0; i < len; ++i) {
                assert(path[i] != w && !seen[path[i]]); seen[path[i]] = 1;
                if (i) assert(adj[path[i-1]][path[i]]);
            }
        }
    }
    puts("S1-IV03 400 cases OK");
}
