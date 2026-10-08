// Lab 6.4 - write4 (tuong duong ROP Emporium). no-PIE, NX bat, khong canary.
// Co print_file(char*) in noi dung file, nhung KHONG chua san chuoi "flag.txt".
// Phai tu ghi "flag.txt" vao .bss roi goi print_file voi rdi tro vao do.
// Nhet san usefulGadgets: pop r14 ; pop r15 ; ret  va  mov [r14], r15 ; ret.
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void print_file(char *name) {
    FILE *f = fopen(name, "r");
    if (!f) { puts("cannot open"); return; }
    int c;
    while ((c = fgetc(f)) != EOF) putchar(c);
    fclose(f);
}

__asm__(
    ".text\n"
    ".globl pwn_pop_rdi\n"
    "pwn_pop_rdi:\n"
    "    pop %rdi\n"
    "    ret\n"
    ".globl pwn_pop_r14_r15\n"
    "pwn_pop_r14_r15:\n"
    "    pop %r14\n"
    "    pop %r15\n"
    "    ret\n"
    ".globl pwn_mov_r14_r15\n"
    "pwn_mov_r14_r15:\n"
    "    mov %r15, (%r14)\n"        // mov qword ptr [r14], r15
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
