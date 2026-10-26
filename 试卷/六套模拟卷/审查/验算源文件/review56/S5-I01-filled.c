#include <stdio.h>
unsigned long long work(unsigned n) {
    if (n == 1) return 0;
    unsigned long long s = 0;
    for (unsigned i = 0; i < n; ++i) {
        ++s;
    }
    unsigned half = n / 2;
    unsigned long long left = work(half);
    unsigned long long right = work(half);
    return left + right + s;
}
int main(void) {
    const unsigned input[] = {2, 4, 8};
    for (unsigned i = 0; i < 3; ++i) {
        unsigned long long value = work(input[i]);
        printf("%u -> %llu\n", input[i], value);
    }
    return 0;
}
