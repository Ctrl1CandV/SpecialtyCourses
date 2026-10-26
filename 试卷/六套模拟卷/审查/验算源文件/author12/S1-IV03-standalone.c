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