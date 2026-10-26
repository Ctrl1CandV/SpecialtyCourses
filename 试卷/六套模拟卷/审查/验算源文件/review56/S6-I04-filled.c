#include <stddef.h>
typedef struct Queue Queue;
typedef struct Arc { int to; struct Arc *next; } Arc;
int empty(const Queue *q);
void enqueue(Queue *q, int x);
int dequeue(Queue *q);
void output(int x);
int kahn(int V, Arc *head[], int indeg[], Queue *q) {
    int count = 0;
    for (int u = 0; u < V; ++u)
        if (indeg[u] == 0) enqueue(q, u);
    while (!empty(q)) {
        int u = dequeue(q);
        output(u);
        ++count;
        for (Arc *e = head[u]; e != NULL; e = e->next)
            if (--indeg[e->to] == 0) enqueue(q, e->to);
    }
    return count == V;
}
int sampleDag(Queue *q) {
    Arc e23 = {3, NULL}, e12 = {2, NULL}, e02 = {2, NULL};
    Arc *head[4] = {&e02, &e12, &e23, NULL};
    int indeg[4] = {0, 0, 2, 1};
    return kahn(4, head, indeg, q);
}
int sampleCycle(Queue *q) {
    Arc e01 = {1, NULL}, e10 = {0, NULL};
    Arc *head[2] = {&e01, &e10};
    int indeg[2] = {1, 1};
    return kahn(2, head, indeg, q);
}
