// vuln.c (lab 4.2): buffer overflow co dien, NX TAT (stack thuc thi duoc).
// Dat shellcode len stack roi ep RIP nhay vao no.
//
// Build (xem build.sh):
//   gcc -z execstack -fno-stack-protector -no-pie -fcf-protection=none -O0 -g
//   -z execstack        : stack co quyen execute (NX tat) -> shellcode-on-stack chay duoc
//   -fno-stack-protector : bo canary de tran thang toi saved RIP
//   -no-pie             : dia chi code co dinh -> gadget jmp rsp co dia chi co dinh
//   -fcf-protection=none : bo endbr64 cho sach (khong anh huong bai nay)
#include <stdio.h>
#include <unistd.h>

// Gadget "jmp rsp" (opcode ff e4) nhet san o dia chi co dinh (no-PIE).
// Ham nay KHONG bao gio duoc goi; ta chi muon 2 byte ff e4 nam trong vung
// .text thuc thi duoc, de dung lam gadget khi ASLR bat.
void gadget(void) {
    __asm__ __volatile__("jmp *%rsp");
}

void vuln(void) {
    char buf[64];
    puts("du lieu:");
    read(0, buf, 400);          // doc 400 byte vao buf[64]: tran
}

int main(void) {
    setvbuf(stdout, 0, 2, 0);
    vuln();
    return 0;
}
