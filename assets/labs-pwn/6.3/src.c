// Lab 6.3: ret2syscall. Build STATIC (giau gadget), NX bat, no-PIE, khong canary.
// Tu khai bao chuoi "/bin/sh" de elf.search chac chan tim thay.
//
// Thuc te glibc 2.39 + gcc 13: binary static CO 'pop rax ; ret' va 'syscall',
// nhung KHONG co 'pop rdi ; ret' / 'pop rsi ; ret' / 'pop rdx ; ret' sach
// (chung bi chon trong cac day lenh rac). Vi vay ta nhet san mot bo gadget
// sach kieu ROP Emporium de chain ret2syscall lam tay chay dung nhu ly thuyet.
#include <stdio.h>
#include <unistd.h>

char shell[] = "/bin/sh";       // nhung chuoi vao .data cua binary

// usefulGadgets: pop rax/rdi/rsi/rdx ; ret va syscall ; ret
__asm__(
    ".text\n"
    ".globl pwn_pop_rax\n"
    "pwn_pop_rax:  pop %rax\n ret\n"
    ".globl pwn_pop_rdi\n"
    "pwn_pop_rdi:  pop %rdi\n ret\n"
    ".globl pwn_pop_rsi\n"
    "pwn_pop_rsi:  pop %rsi\n ret\n"
    ".globl pwn_pop_rdx\n"
    "pwn_pop_rdx:  pop %rdx\n ret\n"
    ".globl pwn_syscall\n"
    "pwn_syscall:  syscall\n ret\n"
);

void vuln() {
    char buf[64];
    read(0, buf, 512);
}

int main() {
    setvbuf(stdout, 0, 2, 0);
    puts(shell);
    vuln();
    return 0;
}
