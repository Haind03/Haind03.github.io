// Lab 6.4 - ret2win (tuong duong ROP Emporium). no-PIE, NX bat, khong canary.
// Co san ham ret2win() goi system("/bin/cat flag.txt"). Chi can tran roi dat
// saved RIP = &ret2win (them 1 'ret' can alignment cho system).
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void ret2win() {
    puts("ret2win() called:");
    system("/bin/cat flag.txt");
}

void pwnme() {
    char buf[32];
    printf("> ");
    read(0, buf, 200);          // overflow
}

int main() {
    setvbuf(stdout, 0, 2, 0);
    pwnme();
    return 0;
}
