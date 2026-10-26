#define main original_main
#include <stdio.h>
enum { CAP = 11, EMPTY = -1 };
int insertLinear(int table[], int m, int key) {
    int pos = key % m;
    for (int step = 0; step < m; ++step) {
        if (table[pos] == EMPTY) {
            table[pos] = key;
            return 1;
        }
        pos = (pos + 1) % m;
    }
    return 0;
}
int main(void) {
    int table[CAP];
    const int keys[] = {7, 18, 29, 3};
    for (int i = 0; i < CAP; ++i)
        table[i] = EMPTY;
    for (int i = 0; i < 4; ++i)
        insertLinear(table, CAP, keys[i]);
    for (int i = 0; i < CAP; ++i)
        printf("%d ", table[i]);
    putchar('\n');
    return 0;
}
#undef main

#include <assert.h>
int main(void) {
    assert(original_main() == 0);
    int a[3] = {0, 1, 2};
    assert(insertLinear(a, 3, 3) == 0);
    int b[3] = {-1, -1, -1};
    assert(insertLinear(b, 3, 4) == 1);
    assert(insertLinear(b, 3, 7) == 1);
    assert(insertLinear(b, 3, 10) == 1);
    assert(b[0] == 10 && b[1] == 4 && b[2] == 7);
    return 0;
}
