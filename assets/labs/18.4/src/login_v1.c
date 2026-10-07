// login_v1.c  -  the VULNERABLE version
// Build: gcc -O1 -o login_v1 login_v1.c
//
// copy_name does not check the length of src before copying it into a
// fixed 16-byte buffer, so it has a classic stack buffer overflow.
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

__attribute__((noinline)) static void copy_name(const char *src) {
    char buf[16];
    // BUG: no length limit, strcpy copies until it hits a NUL
    strcpy(buf, src);
    printf("Hello, %s\n", buf);
}

__attribute__((noinline)) static int check_pin(int pin) {
    return pin == 4242;
}

int main(int argc, char **argv) {
    if (argc < 3) {
        printf("Usage: %s <name> <pin>\n", argv[0]);
        return 1;
    }
    copy_name(argv[1]);
    if (check_pin(atoi(argv[2])))
        printf("PIN correct\n");
    else
        printf("PIN wrong\n");
    return 0;
}
