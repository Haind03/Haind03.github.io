// callme.c - demo bai 3.3: truyen tham so bang pop rdi, xu ly can stack movaps
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

// Gadget "muon" dat san (giong cach ROP Emporium lam), vi tren glibc moi
// __libc_csu_init da bi bo nen binary tu no khong con pop rdi.
__asm__(
    ".global pop_rdi_ret\n"
    ".type pop_rdi_ret, @function\n"
    "pop_rdi_ret:\n"
    "    pop %rdi\n"
    "    ret\n"
);

void win(unsigned long magic) {
    if (magic == 0xdeadbeefcafebabeUL) {
        puts("[+] magic dung. Shell:");
        system("/bin/sh");
    } else {
        printf("[-] magic sai: 0x%lx\n", magic);
    }
}

void vuln(void) {
    char buf[64];
    puts("Du lieu:");
    read(0, buf, 256);
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    vuln();
    return 0;
}
