// original.c: a serial check function written normally, with a clear flow.
// Build: gcc -O0 -o original original.c
#include <stdio.h>
#include <string.h>

// Returns 1 if the serial is valid, 0 otherwise.
// Rules: length exactly 8, byte sum divisible by 7, first character is 'R'.
int check(const char *s) {
    int len = (int)strlen(s);
    if (len != 8)
        return 0;
    if (s[0] != 'R')
        return 0;
    int sum = 0;
    for (int i = 0; i < len; i++)
        sum += (unsigned char)s[i];
    if (sum % 7 != 0)
        return 0;
    return 1;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("Usage: %s <serial>\n", argv[0]);
        return 1;
    }
    puts(check(argv[1]) ? "Correct!" : "Nope.");
    return 0;
}
