#include <stdio.h>
typedef struct {
    int data[6];
    int topL, topR;
} SharedStack;
void init(SharedStack *s) {
    s->topL = -1;
    s->topR = 6;
}
int full(const SharedStack *s) {
    return s->topL + 1 == s->topR;
}
int pushL(SharedStack *s, int x) {
    if (full(s)) return 0;
    s->data[++s->topL] = x;
    return 1;
}
int pushR(SharedStack *s, int x) {
    if (full(s)) return 0;
    s->data[--s->topR] = x;
    return 1;
}
int popR(SharedStack *s, int *out) {
    if (s->topR == 6) return 0;
    *out = s->data[s->topR++];
    return 1;
}
int main(void) {
    SharedStack s;
    int value = 0;
    init(&s);
    pushL(&s, 4);
    pushR(&s, 9);
    pushR(&s, 8);
    popR(&s, &value);
    printf("value=%d, topL=%d, topR=%d\n",
           value, s.topL, s.topR);
    return 0;
}