// login_v2.c  -  the PATCHED version
// Build: gcc -O1 -o login_v2 login_v2.c
//
// Differs from v1 ONLY in copy_name: it adds a length check before copying.
// This is exactly the "difference" that binary diffing needs to find.
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

__attribute__((noinline)) static void copy_name(const char *src) {
    char buf[16];
    // FIX: limit the length, use strncpy and guarantee NUL termination
    if (strlen(src) >= sizeof(buf)) {
        printf("Name too long\n");
        return;
    }
    strncpy(buf, src, sizeof(buf) - 1);
    buf[sizeof(buf) - 1] = '\0';
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
