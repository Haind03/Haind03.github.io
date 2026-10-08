// Lab 6.4 - callme (tuong duong ROP Emporium). no-PIE, NX bat, khong canary.
// Phai goi callme_one, callme_two, callme_three DUNG THU TU, moi ham voi ba
// tham so dung: 0xdeadbeefdeadbeef, 0xcafebabecafebabe, 0xd00df00dd00df00d.
// Nhet san gadget gop 'pop rdi ; pop rsi ; pop rdx ; ret' (usefulGadgets).
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define A 0xdeadbeefdeadbeefULL
#define B 0xcafebabecafebabeULL
#define C 0xd00df00dd00df00dULL

static int step = 0;

void callme_one(unsigned long a, unsigned long b, unsigned long c) {
    if (a == A && b == B && c == C) { step = 1; puts("callme_one OK"); }
    else { puts("callme_one WRONG"); exit(1); }
}
void callme_two(unsigned long a, unsigned long b, unsigned long c) {
    if (step == 1 && a == A && b == B && c == C) { step = 2; puts("callme_two OK"); }
    else { puts("callme_two WRONG"); exit(1); }
}
void callme_three(unsigned long a, unsigned long b, unsigned long c) {
    if (step == 2 && a == A && b == B && c == C) {
        puts("callme_three OK, flag:");
        system("/bin/cat flag.txt");
    } else { puts("callme_three WRONG"); exit(1); }
}

__asm__(
    ".text\n"
    ".globl pwn_pop_rdi_rsi_rdx\n"
    "pwn_pop_rdi_rsi_rdx:\n"
    "    pop %rdi\n"
    "    pop %rsi\n"
    "    pop %rdx\n"
    "    ret\n"
);

void pwnme() {
    char buf[32];
    printf("> ");
    read(0, buf, 400);
}

int main() {
    setvbuf(stdout, 0, 2, 0);
    pwnme();
    return 0;
}
