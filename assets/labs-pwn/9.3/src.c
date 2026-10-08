// Lab 9.3: double free + tcache poisoning (safe-linking), glibc 2.39, no-PIE.
// Menu note size co dinh 0x30. BUG: free khong xoa con tro (UAF doc/ghi tren chunk da free).
// Muc tieu: tcache poisoning de malloc tra ve &hook, ghi &win vao hook, goi hook -> shell.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define N 16
#define SZ 0x30

char *slots[N];

void win(void){ puts("[win] hook bi chiem -> /bin/sh"); system("/bin/sh"); _exit(0); }
void safe_hook(void){ puts("[hook] khong co gi de lam"); }

/* con tro ham toan cuc, can 16 de qua check aligned_OK cua tcache_get */
void (*hook)(void) __attribute__((aligned(16))) = safe_hook;

static int getint(void){ char b[32]; int r=read(0,b,sizeof(b)-1); if(r<=0)exit(0); b[r]=0; return atoi(b); }
static int getidx(void){ printf("idx> "); int i=getint(); return (i<0||i>=N)?-1:i; }

int main(void){
    setvbuf(stdout,0,2,0);
    puts("== heap note (glibc 2.39) ==");
    for(;;){
        puts("1) alloc  2) free  3) edit  4) show  5) run-hook  0) exit");
        printf("> ");
        int c=getint(), i;
        if(c==1){ if((i=getidx())<0) continue; slots[i]=malloc(SZ); puts("ok"); }
        else if(c==2){ if((i=getidx())<0) continue; free(slots[i]); puts("freed"); }     /* UAF: khong NULL */
        else if(c==3){ if((i=getidx())<0) continue; printf("data> "); read(0, slots[i], SZ); puts("edited"); } /* UAF write */
        else if(c==4){ if((i=getidx())<0) continue; write(1, slots[i], 8); }              /* UAF read: leak 8 byte fd */
        else if(c==5){ hook(); }
        else if(c==0){ return 0; }
    }
}
