/*
 * Level 1 (tier 1): direct string comparison. The password sits right in the binary.
 * Build: gcc -O0 -o level1 level1.c
 * Practice goal: read the password straight out statically (strings / decompiler),
 * or patch je/jne to get past the check without knowing the password.
 */
#include <stdio.h>
#include <string.h>

int main(void) {
    char buf[64];
    const char *pass = "letmein123";
    printf("Enter password: ");
    if (!fgets(buf, sizeof buf, stdin)) return 1;
    buf[strcspn(buf, "\n")] = 0;
    if (strcmp(buf, pass) == 0)
        puts("Correct! Flag: FLAG{level1_strings_win}");
    else
        puts("Nope.");
    return 0;
}
