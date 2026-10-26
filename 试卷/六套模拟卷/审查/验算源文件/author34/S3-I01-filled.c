#include <stdio.h>

unsigned long long countOps(int n) {
    unsigned long long count = 0;
    for (long long i = 1; i <= n; i *= 2) {
        for (int j = n; j >= 1; --j) {
            ++count;
        }
    }
    return count;
}

int main(void) {
    int sample = 8;
    unsigned long long result = countOps(sample);
    printf("n=%d, count=%llu\n", sample, result);
    return 0;
}
