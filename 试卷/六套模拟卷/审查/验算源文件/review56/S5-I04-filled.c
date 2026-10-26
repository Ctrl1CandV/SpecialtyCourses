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
