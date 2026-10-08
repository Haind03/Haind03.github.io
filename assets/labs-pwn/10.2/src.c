// Lab 10.2 - challenge "guestbook" (writeup mau phan 10.2).
// Mitigation: NX bat, no-PIE, KHONG canary, Partial RELRO. Chay voi ASLR BAT.
// Dang bai dien hinh: mot overflow stack + co puts de leak libc -> ret2libc.
//
// gcc 13 no-PIE khong con 'pop rdi ; ret' san (da bo __libc_csu_init), ma giai
// doan 1 (leak) can gadget NGAY TRONG binary vi chua biet base libc. Nen ta tu
// nhet mot gadget kieu ROP Emporium vao source. Day la cach ta mo phong "mot
// challenge that" tren chinh may minh de co transcript that.
#include <stdio.h>
#include <unistd.h>

// Gadget tu nhet: pop rdi ; ret (bytes 5f c3). ROPgadget/pwntools se tim thay.
__asm__(
    ".text\n"
    ".globl g_pop_rdi\n"
    "g_pop_rdi:\n"
    "    pop %rdi\n"
    "    ret\n"
);

void banner(void) {
    puts("====================================");
    puts("      PTIT Guestbook  v1.0");
    puts("====================================");
}

void sign(void) {
    char name[64];
    printf("Moi ban ky ten: ");
    read(0, name, 256);          // BUG: doc 256 byte vao name[64] -> tran saved RIP
    printf("Cam on, ");
    printf("%s", name);          // in bang %s (KHONG phai loi format string)
    puts(" da ghi so luu niem.");
}

int main(void) {
    setvbuf(stdout, 0, 2, 0);
    banner();
    sign();
    return 0;
}
