// chall2.c - challenge 2 (trung binh): ret2win mot tham so, win goi system
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
__asm__(".global g\n g:\n pop %rdi\n ret\n");    // gadget pop rdi ; ret nhet san
void win(unsigned long k){
    if(k==0xcafed00d){ puts("[+] ok"); system("/bin/sh"); }
    else printf("[-] k=0x%lx\n",k);
}
void vuln(void){ char buf[32]; puts("chall2>"); read(0,buf,200); }
int main(void){ setvbuf(stdout,0,_IONBF,0); vuln(); return 0; }
