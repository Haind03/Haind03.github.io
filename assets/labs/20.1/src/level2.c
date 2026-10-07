/*
 * Level 2 (tier 2): a simple formula-based serial. The password is not stored
 * as plaintext but transformed and then compared with a constant array. It can
 * still be read out statically, but you have to reverse the transformation.
 * Build: gcc -O0 -o level2 level2.c
 */
#include <stdio.h>
#include <string.h>

/* the correct password transforms as: enc[i] = (pw[i] ^ 0x2A) + 3 */
static const unsigned char TARGET[] = {
    0x5C, 0x1C, 0x4C, 0x5B, 0x1C, 0x61, 0x21, 0x1B
};

int main(void) {
    char buf[64];
    printf("Enter serial (8 characters): ");
    if (!fgets(buf, sizeof buf, stdin)) return 1;
    buf[strcspn(buf, "\n")] = 0;
    if (strlen(buf) != 8) { puts("Nope."); return 0; }
    int ok = 1;
    for (int i = 0; i < 8; i++) {
        unsigned char enc = (unsigned char)((buf[i] ^ 0x2A) + 3);
        if (enc != TARGET[i]) ok = 0;
    }
    if (ok) puts("Correct! Flag: FLAG{level2_serial_math}");
    else    puts("Nope.");
    return 0;
}
