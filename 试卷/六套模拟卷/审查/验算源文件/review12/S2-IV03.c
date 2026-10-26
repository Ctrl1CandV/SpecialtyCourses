#include <assert.h>
#include <stddef.h>
#include <stdlib.h>
#include <stdio.h>
#include <stddef.h>
typedef struct Arc {
    int to;
    struct Arc *next;
} Arc;
typedef struct {
    int V, E;
    Arc **head;
} Graph;

int pathAtMostK(const Graph *G, int s, int t, int k,
                int *path, int *pathLen) {
    *pathLen = 0;
    if (k < 0) return 0;
    if (s == t) {
        path[0] = s;
        *pathLen = 1;
        return 1;
    }

    int dist[100], parent[100], queue[100], rev[100];
    for (int i = 0; i < G->V; ++i) {
        dist[i] = -1;
        parent[i] = -1;
    }
    int front = 0, rear = 0;
    dist[s] = 0;
    queue[rear++] = s;
    while (front < rear && dist[t] == -1) {
        int u = queue[front++];
        for (const Arc *a = G->head[u]; a != NULL; a = a->next) {
            int v = a->to;
            if (dist[v] != -1) continue;
            dist[v] = dist[u] + 1;
            parent[v] = u;
            queue[rear++] = v;
        }
    }
    if (dist[t] == -1 || dist[t] > k) return 0;

    int len = 0;
    for (int v = t; v != -1; v = parent[v]) rev[len++] = v;
    for (int i = 0; i < len; ++i) path[i] = rev[len - 1 - i];
    *pathLen = len;
    return 1;
}

static int oracleDist(int n, int adj[12][12], int s, int t) {
    int dist[12], q[12], front = 0, rear = 0;
    for (int i = 0; i < n; ++i) dist[i] = -1;
    dist[s] = 0; q[rear++] = s;
    while (front < rear) {
        int u = q[front++]; if (u == t) return dist[u];
        for (int v = 0; v < n; ++v) if (adj[u][v] && dist[v] < 0) {
            dist[v] = dist[u] + 1; q[rear++] = v;
        }
    }
    return -1;
}
int main(void) {
    for (int trial = 0; trial < 500; ++trial) {
        int n = 1 + rand() % 10, adj[12][12] = {0};
        Arc arc[150]; Arc *head[12] = {0}; int ec = 0, undirected = 0;
        for (int u = 0; u < n; ++u) for (int v = u + 1; v < n; ++v)
            if (rand() % 3 == 0) {
                adj[u][v] = adj[v][u] = 1; ++undirected;
                arc[ec] = (Arc){v, head[u]}; head[u] = &arc[ec++];
                arc[ec] = (Arc){u, head[v]}; head[v] = &arc[ec++];
            }
        Graph g = {n, undirected, head};
        int s = rand() % n, t = rand() % n, k = rand() % 15 - 2;
        int path[12], len = -1, d = oracleDist(n, adj, s, t);
        int expect = k >= 0 && d >= 0 && d <= k;
        int got = pathAtMostK(&g, s, t, k, path, &len);
        assert(got == expect);
        if (!got) assert(len == 0);
        else {
            int seen[12] = {0}; assert(len >= 1 && len <= n && len - 1 <= k);
            assert(path[0] == s && path[len-1] == t);
            for (int i = 0; i < len; ++i) {
                assert(!seen[path[i]]); seen[path[i]] = 1;
                if (i) assert(adj[path[i-1]][path[i]]);
            }
        }
    }
    puts("S2-IV03 500 cases OK");
}
