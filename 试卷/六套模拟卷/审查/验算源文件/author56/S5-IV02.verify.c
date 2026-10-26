#include <stdbool.h>
#include <stddef.h>
#include <stdlib.h>
typedef struct Arc { int to; struct Arc *next; } Arc;
typedef struct Graph { int V; Arc **head; } Graph;

bool canBePrefix(const Graph *G, const int P[], int k) {
    if (k == 0) return true;
    int *indeg = calloc((size_t)G->V, sizeof *indeg);
    if (indeg == NULL) abort();
    for (int u = 0; u < G->V; ++u)
        for (const Arc *e = G->head[u]; e != NULL; e = e->next)
            ++indeg[e->to];
    for (int i = 0; i < k; ++i) {
        int u = P[i];
        if (indeg[u] != 0) {
            free(indeg);
            return false;
        }
        for (const Arc *e = G->head[u]; e != NULL; e = e->next)
            --indeg[e->to];
    }
    free(indeg);
    return true;
}

#include <assert.h>
#include <stdio.h>
static int brute(const Graph *G, const int P[], int k, int used[],
                 int indeg[], int at) {
    if (at == G->V) return 1;
    for (int u = 0; u < G->V; ++u) {
        if (used[u] || indeg[u] != 0 || (at < k && P[at] != u)) continue;
        used[u] = 1;
        for (const Arc *e = G->head[u]; e; e = e->next) --indeg[e->to];
        if (brute(G, P, k, used, indeg, at + 1)) {
            for (const Arc *e = G->head[u]; e; e = e->next) ++indeg[e->to];
            used[u] = 0;
            return 1;
        }
        for (const Arc *e = G->head[u]; e; e = e->next) ++indeg[e->to];
        used[u] = 0;
    }
    return 0;
}
int main(void) {
    Graph zero = {0, NULL};
    assert(canBePrefix(&zero, NULL, 0));
    srand(12);
    for (int rep = 0; rep < 250; ++rep) {
        int V = 1 + rand() % 6;
        Arc arcs[36]; Arc *head[6] = {0};
        int E = 0;
        for (int u = 0; u < V; ++u)
            for (int v = u + 1; v < V; ++v)
                if (rand() % 3 == 0) {
                    arcs[E] = (Arc){v, head[u]};
                    head[u] = &arcs[E++];
                }
        Graph G = {V, head};
        int P[6]; for (int i = 0; i < V; ++i) P[i] = i;
        for (int i = V - 1; i > 0; --i) {
            int j = rand() % (i + 1), t = P[i]; P[i] = P[j]; P[j] = t;
        }
        for (int k = 0; k <= V; ++k) {
            int used[6] = {0}, indeg[6] = {0};
            for (int u = 0; u < V; ++u)
                for (Arc *e = head[u]; e; e = e->next) ++indeg[e->to];
            int want = brute(&G, P, k, used, indeg, 0);
            assert((int)canBePrefix(&G, P, k) == want);
        }
    }
    puts("S5-IV02 random DAG/topological-prefix checks pass");
    return 0;
}
