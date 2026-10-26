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

#include <assert.h>
#include <stdio.h>
struct Queue { int a[32], front, rear; };
int empty(const Queue *q) { return q->front == q->rear; }
void enqueue(Queue *q, int x) { q->a[q->rear++] = x; }
int dequeue(Queue *q) { return q->a[q->front++]; }
static int out[32], count;
void output(int x) { out[count++] = x; }
int main(void) {
    Queue q = {0};
    assert(sampleDag(&q) == 1);
    assert(count == 4 && out[0] == 0 && out[1] == 1
           && out[2] == 2 && out[3] == 3);
    Queue cyclic = {0};
    count = 0;
    assert(sampleCycle(&cyclic) == 0 && count == 0);
    return 0;
}
