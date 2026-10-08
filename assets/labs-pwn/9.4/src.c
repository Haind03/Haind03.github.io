// Lab 9.4 (capstone): Note Manager co UAF. glibc 2.39, no-PIE, Partial RELRO.
// Muc tieu: tcache poisoning ghi de atoi@got bang backdoor() -> shell -> doc flag.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define N 24
char *notes[N];
int   sizes[N];

void backdoor(void){
    puts("[backdoor] GOT bi ghi de -> /bin/sh");
    system("/bin/sh");
    _exit(0);
}

static int getint(void){ char b[0x20]; int r=read(0,b,sizeof(b)-1); if(r<=0)exit(0); b[r]=0; return atoi(b); }
static int idx(void){ printf("idx> "); int i=getint(); return (i<0||i>=N)?-1:i; }

void add(void){ int i=idx(); if(i<0)return; printf("size> "); int s=getint(); if(s<1||s>0x400)return;
                notes[i]=malloc(s); sizes[i]=s; puts("added"); }
void del(void){ int i=idx(); if(i<0)return; free(notes[i]); puts("deleted"); }   /* UAF: khong NULL */
void edit(void){ int i=idx(); if(i<0)return; printf("data> "); read(0, notes[i], sizes[i]); puts("ok"); } /* UAF write */
void view(void){ int i=idx(); if(i<0)return; write(1, notes[i], 8); }            /* UAF read: leak */

int main(void){
    setvbuf(stdout,0,2,0);
    puts("== Note Manager (glibc 2.39) ==");
    for(;;){
        printf("[add/del/edit/view/exit]> ");
        char cmd[0x10]; int r=read(0,cmd,sizeof(cmd)-1); if(r<=0)break; cmd[r]=0;
        if(!strncmp(cmd,"add",3)) add();
        else if(!strncmp(cmd,"del",3)) del();
        else if(!strncmp(cmd,"edit",4)) edit();
        else if(!strncmp(cmd,"view",4)) view();
        else if(!strncmp(cmd,"exit",4)) break;
    }
    return 0;
}
