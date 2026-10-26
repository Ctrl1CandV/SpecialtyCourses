#include <stdio.h>
enum { V = 4 };
int g[V][V] = {
    {0, 1, 1, 0}, {1, 0, 1, 0},
    {1, 1, 0, 0}, {0, 0, 0, 0}
};
int seen[V] = {0};
void dfs(int u) {
    seen[u] = 1;
    for (int v = 0; v < V; ++v) {
        if (g[u][v] && !seen[v]) {
            printf("%d->%d ", u, v);
            dfs(v);
        }
    }
}
int visitForest(void) {
    int components = 0;
    for (int u = 0; u < V; ++u) {
        if (!seen[u]) {
            ++components;
            printf("C%d: ", components);
            dfs(u);
            putchar('\n');
        }
    }
    return components;
}
int main(void) {
    int total = visitForest();
    printf("components=%d\n", total);
    return 0;
}
