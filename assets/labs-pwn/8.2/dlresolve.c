// Lab 8.2 phan B: ret2dlresolve.
// Binary KHONG nhap system, KHONG co chuoi /bin/sh, KHONG co ham in de leak.
// Chi co read (overflow) + puts + setvbuf. Vi la Partial RELRO (lazy binding),
// ta gia cac cau truc Elf64_Rela / Elf64_Sym / chuoi ten ham roi ep
// _dl_runtime_resolve phan giai "system" va goi system("/bin/sh").
//
// Ubuntu 24.04, glibc 2.39, gcc 13.3. No-PIE, khong canary, Partial RELRO.
#include <stdio.h>
#include <unistd.h>

// Gadget tu nhet cho pwntools dung xep chain goi read(0, data_addr, len):
//   pop rdi ; ret   (5f c3)
//   pop rsi ; ret   (5e c3)
//   pop rdx ; ret   (5a c3)
__asm__(
    ".text\n"
    ".globl pwn_gadgets\n"
    "pwn_gadgets:\n"
    "    pop %rdi\n    ret\n"
    "    pop %rsi\n    ret\n"
    "    pop %rdx\n    ret\n"
);

void vuln(void) {
    char buf[64];
    read(0, buf, 0x200);        // overflow saved RIP, du cho ROP chain
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    puts("== ret2dlresolve demo ==");
    vuln();
    return 0;
}
