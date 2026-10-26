#include <stdio.h>
#include <stdlib.h>
typedef struct Node { int data; struct Node *next; } Node;
typedef struct { Node *front, *rear; } Queue;

int init(Queue *q) {
    Node *h = malloc(sizeof *h);
    if (h == NULL) return 0;
    h->next = NULL;
    q->front = q->rear = h;
    return 1;
}
int enq(Queue *q, int x) {
    Node *p = malloc(sizeof *p);
    if (p == NULL) return 0;
    p->data = x; p->next = NULL;
    q->rear->next = p;
    q->rear = p;
    return 1;
}
int deq(Queue *q, int *out) {
    Node *p = q->front->next;
    if (p == NULL) return 0;
    *out = p->data;
    q->front->next = p->next;
    if (q->rear == p) q->rear = q->front;
    free(p);
    return 1;
}
int empty(const Queue *q) { return q->front == q->rear; }
int main(void) {
    Queue q; int x;
    if (!init(&q)) return 1;
    if (!enq(&q, 4) || !enq(&q, 7)) return 1;
    deq(&q, &x);
    if (!enq(&q, 9)) return 1;
    printf("%d %d\n", x, q.front->next->data);
    while (!empty(&q)) deq(&q, &x);
    free(q.front);
    return 0;
}
