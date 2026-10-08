// jump.c - lab bai 3.2: buffer khac co, tu do offset bang cyclic
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>

void win(void) {
    char f[64]; int fd = open("flag.txt", O_RDONLY);
    if (fd < 0) { puts("thieu flag.txt"); _exit(1); }
    int n = read(fd, f, 64); write(1, "WIN: ", 5); write(1, f, n); _exit(0);
}

void vuln(void) {
    char buf[120];               // buffer khac co de offset khac demo
    puts("noi di:");
    read(0, buf, 300);
}

int main(void){ setvbuf(stdout,0,_IONBF,0); vuln(); return 0; }
