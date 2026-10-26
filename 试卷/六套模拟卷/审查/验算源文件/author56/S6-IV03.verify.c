#include <stddef.h>
#include <stdlib.h>
typedef struct Arc { int to; struct Arc *next; } Arc;
typedef struct Graph { int V; Arc **head; } Graph;
typedef enum { ORDER_OK, REORDER, CYCLE } State;

State classifyArc(const Graph *G, const int sigma[], int u, int v) {
    if (u == v) return CYCLE;
    int V = G->V;
    int *pos = malloc((size_t)V * sizeof *pos);
    if (pos == NULL) abort();
    for (int i = 0; i < V; ++i) pos[sigma[i]] = i;
    if (pos[u] < pos[v]) {
        free(pos);
        return ORDER_OK;
    }
    free(pos);

    unsigned char *seen = calloc((size_t)V, sizeof *seen);
    int *stack = malloc((size_t)V * sizeof *stack);
    if (seen == NULL || stack == NULL) {
        free(seen);
        free(stack);
        abort();
    }
    int top = 0;
    stack[top++] = v;
    seen[v] = 1;
    while (top != 0) {
        int x = stack[--top];
        if (x == u) {
            free(seen);
            free(stack);
            return CYCLE;
        }
        for (const Arc *e = G->head[x]; e != NULL; e = e->next) {
            int y = e->to;
            if (!seen[y]) {
                seen[y] = 1;
                stack[top++] = y;
            }
        }
    }
    free(seen);
    free(stack);
    return REORDER;
}

#include <assert.h>
#include <stdio.h>
static int expected(int n, int matrix[7][7], int sigma[], int u, int v) {
    int indeg[7] = {0}, used[7] = {0}, count = 0;
    for (int a = 0; a < n; ++a)
        for (int b = 0; b < n; ++b)
            if (matrix[a][b] || (a == u && b == v)) ++indeg[b];
    for (;;) {
        int picked = -1;
        for (int x = 0; x < n; ++x)
            if (!used[x] && indeg[x] == 0) { picked = x; break; }
        if (picked < 0) break;
        used[picked] = 1; ++count;
        for (int b = 0; b < n; ++b)
            if (matrix[picked][b] || (picked == u && b == v)) --indeg[b];
    }
    if (count != n) return CYCLE;
    int pu = -1, pv = -1;
    for (int i = 0; i < n; ++i) {
        if (sigma[i] == u) pu = i;
        if (sigma[i] == v) pv = i;
    }
    return pu < pv ? ORDER_OK : REORDER;
}
int main(void) {
    srand(16);
    int observed[3] = {0};
    for (int rep = 0; rep < 250; ++rep) {
        int n = 2 + rand() % 6;
        int sigma[7], pos[7], matrix[7][7] = {{0}};
        Arc arcs[49], *head[7] = {0};
        int E = 0;
        for (int i = 0; i < n; ++i) sigma[i] = i;
        for (int i = n - 1; i > 0; --i) {
            int j = rand() % (i + 1), t = sigma[i];
            sigma[i] = sigma[j]; sigma[j] = t;
        }
        for (int i = 0; i < n; ++i) pos[sigma[i]] = i;
        for (int u = 0; u < n; ++u)
            for (int v = 0; v < n; ++v)
                if (pos[u] < pos[v] && rand() % 3 == 0) {
                    matrix[u][v] = 1;
                    arcs[E] = (Arc){v, head[u]}; head[u] = &arcs[E++];
                }
        Graph G = {n, head};
        for (int u = 0; u < n; ++u)
            for (int v = 0; v < n; ++v)
                if (!matrix[u][v]) {
                    State got = classifyArc(&G, sigma, u, v);
                    int want = expected(n, matrix, sigma, u, v);
                    assert((int)got == want);
                    ++observed[got];
                }
        for (int u = 0; u < n; ++u) {
            int seen[7] = {0};
            for (Arc *e = head[u]; e; e = e->next) seen[e->to] = 1;
            for (int v = 0; v < n; ++v) assert(seen[v] == matrix[u][v]);
        }
    }
    assert(observed[ORDER_OK] && observed[REORDER] && observed[CYCLE]);
    puts("S6-IV03 random-DAG/rebuild-and-check-state checks pass");
    return 0;
}
