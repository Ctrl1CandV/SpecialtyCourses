#include <stdbool.h>

static int countDfs(const int g[12][12], int V, int u, int t,
                    int usedEdges, int k, bool onPath[12]) {
    if (usedEdges == k) return u == t ? 1 : 0;
    if (u == t) return 0;
    int ans = 0;
    for (int v = 0; v < V; ++v) {
        if (g[u][v] && !onPath[v]) {
            onPath[v] = true;
            ans += countDfs(g, V, v, t, usedEdges + 1, k, onPath);
            onPath[v] = false;
        }
    }
    return ans;
}

int countPaths(const int g[12][12], int V, int s, int t, int k) {
    bool onPath[12] = {false};
    onPath[s] = true;
    return countDfs(g, V, s, t, 0, k, onPath);
}