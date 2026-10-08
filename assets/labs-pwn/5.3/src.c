// src.c - lab 5.3: ASLR/PIE leak.
// Binary PIE: moi lan chay base image ngau nhien (ASLR bat). Co hai lo:
//   (1) printf(buf) -> format string, dung de LEAK mot con tro .text cua image;
//   (2) read lan hai tran buf -> overflow, nhay toi win() = base + offset(win).
// Vi PIE nen phai leak base truoc, khong hardcode dia chi duoc. Khong canary
// de tap trung vao chuyen PIE (mot mitigation mot luc).
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void win(void) {
    puts("[+] PIE base tinh dung. Shell:");
    system("/bin/sh");
}

void vuln(void) {
    char buf[64];
    printf("leak> ");
    read(0, buf, 0x100);
    printf(buf);              // lo format string: leak con tro .text -> suy base
    puts("");
    printf("pwn> ");
    read(0, buf, 0x100);      // overflow: nhay toi win() = base + offset
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    vuln();
    return 0;
}
