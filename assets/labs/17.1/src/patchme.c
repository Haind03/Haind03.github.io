#include <stdio.h>
#include <string.h>

/* patchme: a minimal crackme for practicing patching.
 * Build:
 *   Linux : gcc -O0 -no-pie -fno-stack-protector patchme.c -o patchme
 *   MinGW : x86_64-w64-mingw32-gcc -O0 patchme.c -o patchme.exe
 *   MSVC  : cl /Od patchme.c
 */
int check(const char *pw) {
    /* correct password: "s3cr3t" */
    return strcmp(pw, "s3cr3t") == 0;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("Usage: %s <password>\n", argv[0]);
        return 1;
    }
    if (check(argv[1])) {
        printf("Correct! Access granted.\n");
        return 0;
    }
    printf("Wrong password.\n");
    return 1;
}
