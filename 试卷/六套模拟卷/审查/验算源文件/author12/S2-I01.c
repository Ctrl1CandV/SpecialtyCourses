#include <stdio.h>
static unsigned long long moveCount = 0;
void move(char from, char to) {
    ++moveCount;
    printf("%c->%c\n", from, to);
}
void hanoi(int n, char from, char aux, char to) {
    if (n == 1) {
        move(from, to);
        return;
    }
    hanoi(n - 1, from, to, aux);
    move(from, to);
    hanoi(n - 1, aux, from, to);
}
int main(void) {
    hanoi(3, 'A', 'B', 'C');
    printf("moves=%llu\n", moveCount);
    return 0;
}