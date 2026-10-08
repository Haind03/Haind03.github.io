// Lab 10.3 - do an cuoi "PTIT Secret Diary".
// Capstone: ghep 3 ky thuat da hoc.
//   - format string (Phan 7.1) de LEAK canary va dia chi libc
//   - canary (Phan 5.2): phai ghi dung canary khi tran de khong bi abort
//   - ret2libc (Phan 6.1/6.2): goi system("/bin/sh")
// Mitigation: NX bat, stack canary BAT, no-PIE, Partial RELRO. ASLR BAT.
//
// gcc 13 no-PIE khong con 'pop rdi ; ret' san -> tu nhet mot gadget sach.
#include <stdio.h>
#include <string.h>
#include <unistd.h>

__asm__(
    ".text\n"
    ".globl c_pop_rdi\n"
    "c_pop_rdi:\n"
    "    pop %rdi\n"
    "    ret\n"
);

void setup(void) {
    setvbuf(stdout, 0, 2, 0);
    setvbuf(stdin, 0, 2, 0);
}

void vuln(void) {
    char buf[128];

    // BUG 1: format string. In lai ten nguoi dung bang printf(buf).
    printf("Ban ten gi?\n> ");
    int n = read(0, buf, 120);
    if (n < 0) n = 0;
    buf[n] = '\0';               // chan de printf(buf) dung dung cho
    printf("Chao ");
    printf(buf);                 // <-- loi format string, dung de LEAK
    puts("");

    // BUG 2: overflow. buf[128] nhung doc toi 400 byte -> tran qua canary + saved RIP.
    printf("Viet dong nhat ky di:\n> ");
    read(0, buf, 400);
}

int main(void) {
    setup();
    puts("====================================");
    puts("      PTIT Secret Diary  v2.0");
    puts("====================================");
    vuln();
    puts("Da luu nhat ky. Tam biet.");
    return 0;
}
