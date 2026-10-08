// Lab 6.1: ret2libc. NX bat, no-PIE, khong canary.
// Binary nho nay KHONG chua san gadget 'pop rdi ; ret' (gcc 13 da bo
// __libc_csu_init), nen exploit lay gadget tu chinh libc sau khi da biet
// base libc. Day la y do: minh hoa ret2libc "muon" ca gadget lan ham tu libc.
#include <stdio.h>
#include <unistd.h>

void vuln() {
    char buf[64];
    read(0, buf, 256);          // overflow: doc 256 byte vao buf[64]
}

int main() {
    setvbuf(stdout, 0, 2, 0);
    vuln();
    return 0;
}
