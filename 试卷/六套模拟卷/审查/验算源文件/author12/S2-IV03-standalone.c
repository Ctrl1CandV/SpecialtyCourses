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