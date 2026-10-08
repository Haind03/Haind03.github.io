// Lab 9.2: Use-after-free + type confusion. glibc 2.39, no-PIE.
// BUG: option 3 (free) khong gan con tro ve NULL -> dangling pointer.
//      option 2 (use) van goi o->action() tren vung da free.
// Reclaim: option 4 (spray) malloc cung kich thuoc, ghi raw byte de de len
//          o tri con tro ham action -> type confusion.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void win(void){
    puts("[win] control-flow hijacked -> /bin/sh");
    system("/bin/sh");
    _exit(0);
}

void say_hi(void){ puts("[obj] hi, toi la object binh thuong"); }

typedef struct {
    char info[24];           // offset 0x00
    void (*action)(void);    // offset 0x18
} Obj;

Obj *o = NULL;

static int getint(void){
    char b[32];
    int r = read(0, b, sizeof(b)-1);
    if (r <= 0) exit(0);
    b[r] = 0;
    return atoi(b);
}

int main(void){
    setvbuf(stdout, 0, 2, 0);
    setvbuf(stdin, 0, 2, 0);
    puts("== UAF demo (glibc 2.39) ==");
    for (;;) {
        puts("1) create  2) use  3) free  4) spray  0) exit");
        printf("> ");
        int c = getint();
        if (c == 1) {
            o = malloc(sizeof(Obj));
            o->action = say_hi;
            printf("info> ");
            int r = read(0, o->info, 23); if (r>0) o->info[r-1]=0;
            puts("created");
        } else if (c == 2) {
            if (o) o->action();          // BUG: dung ca khi da free
            else puts("nothing");
        } else if (c == 3) {
            free(o);                     // BUG: khong o=NULL -> UAF
            puts("freed");
        } else if (c == 4) {
            char *p = malloc(sizeof(Obj));   // chiem lai chunk vua free
            printf("data(32)> ");
            read(0, p, 32);                  // ghi raw -> de len action
            puts("sprayed");
        } else if (c == 0) {
            return 0;
        }
    }
}
