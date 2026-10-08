// admin.c - lab bai 3.1: ghi gia tri cu the (0x80000001) vao bien role de in flag
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>

void print_flag(void){
    char f[64]; int fd = open("flag.txt", O_RDONLY);
    if (fd < 0){ puts("thieu flag.txt"); _exit(1); }
    int n = read(fd, f, 64); write(1, "Flag: ", 6); write(1, f, n); _exit(0);
}

int main(void){
    struct { char name[48]; unsigned int role; } u;
    u.role = 0;
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("Ten: ");
    gets(u.name);
    if (u.role == 0x80000001) print_flag();     // role = admin
    else printf("role=0x%x, ban chi la user.\n", u.role);
    return 0;
}
