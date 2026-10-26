#include <stdio.h>
long countOps(const int readings[], int n, long *outSum) {
    long visits = 0;
    *outSum = 0;
    for (int span = 1; span < n; span *= 2) {
        for (int j = 0; j < span; ++j) {
            *outSum += readings[j];
            ++visits;
        }
    }
    return visits;
}
int main(void) {
    int readings[16] = {3, 1, 4, 1, 5, 9, 2, 6,
                        5, 3, 5, 8, 9, 7, 9, 3};
    long total = 0;
    long visits = countOps(readings, 16, &total);
    printf("visits=%ld, total=%ld\n", visits, total);
    return 0;
}