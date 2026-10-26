#include <stdio.h>
unsigned long long grow(unsigned long long n, int *count) {
    unsigned long long x = 2;
    *count = 0;
    while (x < n / 2) {
        x = x * x;
        ++(*count);
    }
    return x;
}
int main(void) {
    unsigned long long n = 65536ULL;
    int count = 0;
    unsigned long long x = grow(n, &count);
    printf("n=%llu x=%llu count=%d\n", n, x, count);
    return 0;
}
