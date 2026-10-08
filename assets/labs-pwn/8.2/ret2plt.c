// Lab 8.2 phan A: ret2plt.
// Binary da NHAP san system() (co system@plt) va co chuoi "/bin/sh" trong
// .rodata. Khi khong leak duoc libc, ta goi lai system qua PLT stub: dia chi
// system@plt co dinh trong binary No-PIE, PLT tu lo viec resolve luc chay.
//
// Ubuntu 24.04, glibc 2.39, gcc 13.3. No-PIE, khong canary, Partial RELRO.
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

// gcc 13 No-PIE khong con 'pop rdi ; ret' san -> tu nhet mot gadget.
__asm__(
    ".text\n"
    ".globl pwn_pop_rdi\n"
    "pwn_pop_rdi:\n"
    "    pop %rdi\n"
    "    ret\n"
);

void vuln(void) {
    char buf[64];
    read(0, buf, 256);          // overflow saved RIP
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    puts("== ret2plt demo ==");
    // Khong bao gio chay, chi de linker nhap system@plt va giu chuoi /bin/sh.
    if (getpid() == 0) system("/bin/sh");
    vuln();
    return 0;
}
