#include <stdio.h>
typedef struct {
    int a[4];
    int front, rear, count;
} Queue;
void init(Queue *q) {
    q->front = 0;
    q->rear = 0;
    q->count = 0;
}
int enq(Queue *q, int x) {
    if (q->count == 4) return 0;
    q->a[q->rear] = x;
    q->rear = (q->rear + 1) % 4;
    ++q->count;
    return 1;
}
int deq(Queue *q, int *out) {
    if (q->count == 0) return 0;
    *out = q->a[q->front];
    q->front = (q->front + 1) % 4;
    --q->count;
    return 1;
}
int main(void) {
    Queue q;
    int x;
    init(&q);
    enq(&q, 10);
    enq(&q, 20);
    deq(&q, &x);
    printf("first=%d\n", x);
    enq(&q, 30);
    return 0;
}