// Lab 7.2: format string ghi bo nho bang %n.
// Loi: printf(buf) truyen input nguoi dung lam format string truc tiep.
// Muc tieu: dung %n ghi de mot GOT entry (exit@got) -> tro toi win() -> shell.
//
// Bien dich: no-PIE (dia chi win va GOT co dinh, khong can leak du ASLR bat),
//   khong canary, FORTIFY tat (neu khong %n bi chan), Partial RELRO (GOT ghi duoc).
// Neu la Full RELRO thi .got.plt chi doc -> phai doi muc tieu (xem README/bai hoc).
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void win() {
    puts("[win] control flow hijacked bang %n write!");
    system("/bin/sh");
    _exit(0);
}

int main() {
    char buf[256];
    setvbuf(stdout, NULL, 2, 0);
    puts("== fmtstr write demo (glibc 2.39) ==");
    printf("fmt> ");
    int n = read(0, buf, sizeof(buf) - 1);
    if (n <= 0) return 1;
    buf[n] = 0;
    printf(buf);     // <--- LOI format string: ghi %n o day
    puts("");
    exit(0);         // exit di qua PLT/GOT -> ghi de exit@got se nhay vao win
    return 0;
}
