#include <stdbool.h>
#include <limits.h>
typedef struct { int u, v, weight; } Edge;

bool repairMST(const int w[100][100], int V,
               const Edge mst[], int failedIndex,
               Edge *replacement, long long *newWeight) {
    bool inFirst[100] = {false};
    int stack[100], top = 0;
    int start = mst[failedIndex].u;
    inFirst[start] = true;
    stack[top++] = start;

    while (top > 0) {
        int u = stack[--top];
        for (int i = 0; i < V - 1; ++i) {
            if (i == failedIndex) continue;
            int v = -1;
            if (mst[i].u == u) v = mst[i].v;
            else if (mst[i].v == u) v = mst[i].u;
            if (v >= 0 && !inFirst[v]) {
                inFirst[v] = true;
                stack[top++] = v;
            }
        }
    }

    int best = INT_MAX;
    Edge chosen = {0, 0, 0};
    int a = mst[failedIndex].u, b = mst[failedIndex].v;
    for (int u = 0; u < V; ++u) {
        for (int v = u + 1; v < V; ++v) {
            if (inFirst[u] == inFirst[v]) continue;
            if ((u == a && v == b) || (u == b && v == a)) continue;
            if (w[u][v] != INT_MAX && w[u][v] < best) {
                best = w[u][v];
                chosen = (Edge){u, v, w[u][v]};
            }
        }
    }
    if (best == INT_MAX) return false;

    long long total = 0;
    for (int i = 0; i < V - 1; ++i) total += mst[i].weight;
    *replacement = chosen;
    *newWeight = total - mst[failedIndex].weight + best;
    return true;
}