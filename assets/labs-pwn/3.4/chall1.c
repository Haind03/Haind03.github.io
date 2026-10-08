// chall1.c - challenge 1 (de): ret2win khong tham so, win dung syscall
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
void win(void){
    char f[64]; int fd=open("flag.txt",O_RDONLY);
    if(fd<0){puts("khong co flag.txt");_exit(1);}
    int n=read(fd,f,64); write(1,"Flag: ",6); write(1,f,n); _exit(0);
}
void vuln(void){ char buf[48]; puts("chall1>"); read(0,buf,200); }
int main(void){ setvbuf(stdout,0,_IONBF,0); vuln(); return 0; }
