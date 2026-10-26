#include <stdio.h>
#define CAP 8
typedef struct {
    int a[CAP];
    int top0, top1;
} Shared;
void init(Shared *s) {
    s->top0 = -1;
    s->top1 = CAP;
}
int full(const Shared *s) {
    return s->top0 + 1 == s->top1;
}
int push0(Shared *s, int x) {
    if (full(s)) return 0;
    s->a[++s->top0] = x;
    return 1;
}
int push1(Shared *s, int x) {
    if (full(s)) return 0;
    s->a[--s->top1] = x;
    return 1;
}
int pop1(Shared *s, int *out) {
    if (s->top1 == CAP) return 0;
    *out = s->a[s->top1++];
    return 1;
}
int main(void) {
    Shared s;
    int value;
    init(&s);
    push0(&s, 11);
    push1(&s, 72);
    push0(&s, 13);
    if (pop1(&s, &value)) printf("%d\n", value);
    return 0;
}
