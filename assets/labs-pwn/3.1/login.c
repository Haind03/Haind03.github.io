// login.c - demo bai 3.1: ghi de bien cuc bo (co xac thuc) de lay shell
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void win(void) {
    puts("[+] authed != 0, mo khoa thanh cong!");
    system("/bin/sh");
}

int main(void) {
    // Dat trong struct de field giu dung thu tu khai bao:
    // buf o dia chi thap, authed ngay sau (dia chi cao hon).
    struct {
        char buf[32];
        int  authed;
    } s;

    s.authed = 0;
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("Nhap ten dang nhap: ");
    gets(s.buf);                 // trace loi: khong gioi han do dai

    if (s.authed != 0) {
        win();
    } else {
        printf("authed hien tai = %d. Tu choi.\n", s.authed);
    }
    return 0;
}
