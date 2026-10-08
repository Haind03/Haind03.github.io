// vuln.c - lab 5.1: mot chuong trinh toi thieu de build nhieu to hop mitigation
// roi chay checksec so sanh. Co san mot cho doc input de giong binary that.
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(void) {
    char buf[64];
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("input> ");
    read(0, buf, 0x100);     // co lo tran de binary "thuc te", bai nay chi doc checksec
    printf("len=%ld\n", (long)sizeof buf);
    return 0;
}
