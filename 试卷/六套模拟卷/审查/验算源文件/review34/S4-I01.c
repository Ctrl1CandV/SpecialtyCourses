#include <stdio.h>
int minPrefix(const int a[], int n) {
    if (n == 1) {
        return a[0];
    }
    int t = minPrefix(a, n - 1);
    return t < a[n - 1] ? t : a[n - 1];
}

int main(void) {
    const int a[] = {23, 33, 16, 79, 34, 29};
    int n = sizeof(a) / sizeof(a[0]);
    int answer = minPrefix(a, n);
    printf("minimum=%d\n", answer);
    return 0;
}