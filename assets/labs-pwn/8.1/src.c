// Lab 8.1: GOT overwrite bang format string.
// Ubuntu 24.04, glibc 2.39, gcc 13.3. No-PIE, khong canary, Partial RELRO.
//
// Lo hong: printf(buf) voi buf lay tu nguoi dung -> format string bug, dung
// lam write primitive (ghi tuy y bang %n). Ta ghi de o GOT cua puts bang dia
// chi ham win(). Sau printf, chuong trinh goi puts("tam biet") nhung thuc chat
// nhay vao win() -> mo shell.
//
// Vi sao can Partial RELRO: GOT phai ghi duoc. Full RELRO (mac dinh glibc 2.39)
// khoa GOT chi doc, se crash khi ghi. Build bang -z relro -z lazy.
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void win(void) {
    // KHONG dung puts o day: puts@got vua bi ghi de thanh win, goi puts se
    // de quy vo han. Dung write (GOT entry khac, khong bi dong toi).
    write(1, "[win] GOT cua puts da bi ghi de, dang mo shell:\n", 48);
    system("/bin/sh");
    _exit(0);
}

int main(void) {
    char buf[256];
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);

    puts("== format string -> GOT overwrite ==");  // lan goi puts dau: resolve puts@got
    printf("nhap payload: ");
    int n = read(0, buf, sizeof(buf) - 1);
    if (n > 0) buf[n] = 0;

    printf(buf);          // LO HONG format string (write primitive)

    puts("tam biet");     // puts@got da bi ghi de -> nhay vao win()
    return 0;
}
