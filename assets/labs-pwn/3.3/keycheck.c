// keycheck.c - lab bai 3.3: truyen code == 0x1337c0de roi lay shell
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

__asm__(".global g\n g:\n pop %rdi\n ret\n");    // gadget pop rdi ; ret

void win(unsigned long code) {
    if (code == 0x1337c0deUL) { puts("[+] dung code. Shell:"); system("/bin/sh"); }
    else printf("[-] code sai: 0x%lx\n", code);
}

void vuln(void) { char buf[72]; puts("code?"); read(0, buf, 200); }

int main(void){ setvbuf(stdout,0,_IONBF,0); vuln(); return 0; }
