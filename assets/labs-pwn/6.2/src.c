// Lab 6.2: leak libc qua GOT. NX bat, no-PIE, khong canary, Partial RELRO.
// Co puts de leak, co overflow qua read. Chay voi ASLR BAT.
//
// gcc 13 no-PIE KHONG con 'pop rdi ; ret' san. Giai doan 1 (leak) can gadget
// trong chinh binary (chua biet base libc nen chua lay gadget libc duoc).
// Vi vay ta chu dong nhet mot gadget kieu ROP Emporium vao source.
#include <stdio.h>
#include <unistd.h>

// Gadget tu nhet: pop rdi ; ret (bytes 5f c3). ROPgadget/pwntools se tim thay.
__asm__(
    ".text\n"
    ".globl pwn_pop_rdi\n"
    "pwn_pop_rdi:\n"
    "    pop %rdi\n"
    "    ret\n"
);

void vuln() {
    char buf[64];
    read(0, buf, 256);
}

int main() {
    setvbuf(stdout, 0, 2, 0);
    puts("start");
    vuln();
    return 0;
}
