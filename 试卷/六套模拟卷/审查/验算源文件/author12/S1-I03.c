#include <stdio.h>
typedef struct Node {
    int data;
    struct Node *next;
} Node;
typedef struct { Node *rear; } Queue;
void enQueue(Queue *q, Node *x) {
    if (q->rear == NULL) {
        x->next = x;
        q->rear = x;
    } else {
        x->next = q->rear->next;
        q->rear->next = x;
        q->rear = x;
    }
}
Node *deQueue(Queue *q) {
    if (q->rear == NULL) return NULL;
    Node *x = q->rear->next;
    if (x == q->rear) q->rear = NULL;
    else q->rear->next = x->next;
    x->next = NULL;
    return x;
}
int main(void) {
    Queue q = {NULL};
    Node a = {4, NULL}, b = {9, NULL};
    enQueue(&q, &a);
    enQueue(&q, &b);
    Node *first = deQueue(&q);
    printf("first=%d, rear=%d\n", first->data, q.rear->data);
    Node *second = deQueue(&q);
    Node *third = deQueue(&q);
    printf("second=%d, empty=%d, third-null=%d\n",
           second->data, q.rear == NULL, third == NULL);
    return 0;
}