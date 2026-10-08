// Lab 6.4 - split (tuong duong ROP Emporium). no-PIE, NX bat, khong canary.
// Co system (qua usefulFunction goi system("/bin/ls")) va chuoi usefulString
// = "/bin/cat flag.txt". Viec cua ta: goi system(usefulString).
// gcc 13 no-PIE khong co 'pop rdi ; ret' -> tu nhet gadget.
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

char usefulString[] = "/bin/cat flag.txt";   // chuoi muc tieu, nam trong binary

void usefulFunction() {
    system("/bin/ls");                       // keo system vao PLT
}

__asm__(
    ".text\n"
    ".globl pwn_pop_rdi\n"
    "pwn_pop_rdi:\n"
    "    pop %rdi\n"
    "    ret\n"
);

void pwnme() {
    char buf[32];
    printf("> ");
    read(0, buf, 200);
}

int main() {
    setvbuf(stdout, 0, 2, 0);
    pwnme();
    return 0;
}
