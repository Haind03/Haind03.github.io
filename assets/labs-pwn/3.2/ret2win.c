// ret2win.c - demo bai 3.2: de saved RIP, nhay vao win (win dung syscall)
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>

void win(void) {
    char flag[64];
    int fd = open("flag.txt", O_RDONLY);
    if (fd < 0) { puts("Khong mo duoc flag.txt"); _exit(1); }
    int n = read(fd, flag, sizeof(flag));
    write(1, "[+] win() da chay. Flag: ", 25);
    write(1, flag, n);
    _exit(0);
}

void vuln(void) {
    char buf[64];
    puts("Ban noi gi di:");
    read(0, buf, 256);           // doc 256 byte vao buf 64 byte: tran
    puts("Oke, tam biet.");
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    vuln();
    return 0;
}
