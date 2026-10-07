// crackme for lesson 18.3 (symbolic execution with angr)
// The check logic is a system of constraints over 8 input bytes with many
// branches, a good fit for angr to explore automatically instead of solving by hand.
//
// Build:
//   gcc -O0 -no-pie -fno-stack-protector -o crackme crackme.c
// Run:
//   ./crackme <serial>
//
// The correct serial is not printed anywhere (you cannot filter it out with `strings`).

#include <stdio.h>
#include <string.h>

#define LEN 8

// Check each byte with a chain of transformations + comparisons.
// Each condition is a separate branch, used to illustrate path exploration.
int check(const unsigned char *s) {
    if (s[0] ^ 0x41)                 return 0;   // s[0] == 'A'
    if ((s[1] + s[2]) != 0xE1)       return 0;   // s[1] + s[2] == 225
    if ((s[3] ^ s[0]) != 0x33)       return 0;   // s[3] == 'A' ^ 0x33 = 'r'
    if ((s[4] * 2) != 0xDC)          return 0;   // s[4] == 0x6E = 'n'
    if ((s[5] - s[1]) != 0x04)       return 0;   // s[5] == s[1] + 4
    if ((s[6] ^ 0x5A) != 0x2B)       return 0;   // s[6] == 0x71 = 'q'
    if (((s[7] + s[6]) & 0xFF) != 0xC5) return 0; // s[7] == 0x54 = 'T'
    // extra final constraint on s[1]: s[1] == 0x6F = 'o'  => s[2] = 0x72 = 'r', s[5] = 0x73 = 's'
    if (s[1] != 0x6F)                return 0;
    return 1;
}

int main(int argc, char **argv) {
    if (argc != 2 || strlen(argv[1]) != LEN) {
        puts("Usage: ./crackme <8-char serial>");
        return 1;
    }
    if (check((const unsigned char *)argv[1])) {
        puts("Correct! Access granted.");
        return 0;
    }
    puts("Nope.");
    return 1;
}
