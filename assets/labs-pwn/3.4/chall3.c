// chall3.c - challenge 3 (kho hon): ret2win hai tham so, pop rdi + pop rsi
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
__asm__(
    ".global gadgets\n"
    ".type gadgets, @function\n"
    "gadgets:\n"
    "    pop %rdi\n"
    "    ret\n"
    "    pop %rsi\n"
    "    ret\n"
);
void win(unsigned long a, unsigned long b){
    if(a==0xc0ffee && b==0x1337){ puts("[+] hai tham so dung. Shell:"); system("/bin/sh"); }
    else printf("[-] sai: a=0x%lx b=0x%lx\n", a, b);
}
void vuln(void){ char buf[40]; puts("Nhap:"); read(0,buf,200); }
int main(void){ setvbuf(stdout,0,_IONBF,0); vuln(); return 0; }
