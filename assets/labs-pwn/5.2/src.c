// src.c - lab 5.2: Stack canary.
// Co hai lo: (1) printf(buf) -> format string, dung de LEAK canary ra;
//            (2) read lan hai tran buf -> overflow, phai ghi LAI dung canary
//                de qua epilogue roi moi toi saved RIP -> win().
// win() in banner roi system("/bin/sh") (ret2win lay shell).
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void win(void) {
    puts("[+] qua duoc canary. Shell:");
    system("/bin/sh");
}

void vuln(void) {
    char buf[64];
    printf("echo> ");
    read(0, buf, 0x100);
    printf(buf);              // lo format string: leak canary qua %p
    puts("");
    printf("lan 2> ");
    read(0, buf, 0x100);      // overflow lan hai, phai xuyen qua canary
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    vuln();
    return 0;
}
