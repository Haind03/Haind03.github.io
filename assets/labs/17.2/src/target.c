// Lab 17.2 - target for a Frida hook
// The program compares the password with strcmp, so hooking strcmp reveals the answer.
//
// Build:
//   Linux:   gcc -O0 target.c -o target
//   Windows: cl /Od target.c   (or mingw: gcc -O0 target.c -o target.exe)

#include <stdio.h>
#include <string.h>

int main(void) {
    char input[128];
    const char *secret = "Fr1da_H00k_Me";

    printf("Enter password: ");
    if (!fgets(input, sizeof(input), stdin)) return 1;
    input[strcspn(input, "\r\n")] = 0;   // strip the newline

    if (strcmp(input, secret) == 0)
        printf("Correct!\n");
    else
        printf("Nope.\n");
    return 0;
}
