/*
 * Level 3 (tier 3): checks username + serial with an algorithm, so you have to
 * write a keygen that generates a serial for any username. The serial is an
 * 8-character hex string from a linear hash of the username.
 * Build: gcc -O0 -o level3 level3.c
 */
#include <stdio.h>
#include <string.h>

static unsigned int gen(const char *name) {
    unsigned int acc = 0x1337;
    for (const char *p = name; *p; p++)
        acc = (acc * 33u) + (unsigned char)(*p);
    acc ^= 0xC0FFEE;
    return acc & 0xFFFFFFFFu;
}

int main(void) {
    char name[64], serial[64], expected[16];
    printf("Username: ");
    if (!fgets(name, sizeof name, stdin)) return 1;
    name[strcspn(name, "\n")] = 0;
    printf("Serial: ");
    if (!fgets(serial, sizeof serial, stdin)) return 1;
    serial[strcspn(serial, "\n")] = 0;
    if (strlen(name) == 0) { puts("Nope."); return 0; }
    snprintf(expected, sizeof expected, "%08X", gen(name));
    if (strcmp(serial, expected) == 0)
        puts("Correct! Valid serial. Flag: FLAG{level3_keygen_done}");
    else
        puts("Nope.");
    return 0;
}
