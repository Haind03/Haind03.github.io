/*
 * crackme01 for Lab 2.3 (Ghidra)
 *
 * Goal of the lab: open this binary in Ghidra, go from the result messages to
 * the check function, read the decompiler's pseudocode, and find the correct
 * password WITHOUT reading this source file first.
 *
 * Build (pick one):
 *   Linux/macOS:   gcc -O0 -no-pie -o crackme01 crackme01.c
 *   MinGW (Win):   x86_64-w64-mingw32-gcc -O0 -o crackme01.exe crackme01.c
 *   MSVC (Win):    cl /Od crackme01.c
 *
 * Use -O0 so the decompiler output stays closest to the source, which suits beginners.
 */

#include <stdio.h>
#include <string.h>

/* The check is a separate function so it is easy to spot in Ghidra. */
static int check_password(const char *input)
{
    const char *secret = "Gh1dra_R0cks";

    if (strlen(input) != strlen(secret))
        return 0;

    for (size_t i = 0; i < strlen(secret); i++) {
        if (input[i] != secret[i])
            return 0;
    }
    return 1;
}

int main(void)
{
    char buf[64];

    printf("Enter password: ");
    if (scanf("%63s", buf) != 1)
        return 1;

    if (check_password(buf))
        printf("Access granted. Congratulations!\n");
    else
        printf("Wrong password. Try again.\n");

    return 0;
}
