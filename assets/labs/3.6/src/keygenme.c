/*
 * keygenme.c  -  Lab 3.6: write a keygen
 *
 * Build (Linux):
 *   gcc -O0 -no-pie -fno-stack-protector -o keygenme keygenme.c
 * Build (Windows, MinGW):
 *   x86_64-w64-mingw32-gcc -O0 -o keygenme.exe keygenme.c
 * Build (Windows, MSVC Developer Prompt):
 *   cl /Od keygenme.c
 *
 * Run:
 *   ./keygenme <username> <serial>
 * Example:
 *   ./keygenme alice XXXX-XXXX-XXXX-XXXX
 *
 * Your task: read validate(), understand the username -> serial relationship,
 * then write a keygen that produces a valid serial for any username.
 *
 * This algorithm CAN be reversed (it does not use a real one-way function),
 * on purpose, for illustration. Do not use it as a security model.
 */
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <ctype.h>

/*
 * Compute 4 16-bit "blocks" from the username.
 * Each block is a weighted sum of the characters, with different weights per block.
 * A valid serial = the 4 blocks printed as 4-digit hex, separated by '-'.
 *
 *   block[k] = ( SEED[k] + sum_i( (username[i] + 1) * (i + 1 + k) ) ) & 0xFFFF
 *
 * Since the serial is derived directly from the username, a keygen only needs
 * to recompute this formula.
 */
static const uint16_t SEED[4] = { 0x1337, 0xBEEF, 0xCAFE, 0x5A5A };

static void compute_blocks(const char *user, uint16_t out[4]) {
    size_t n = strlen(user);
    for (int k = 0; k < 4; k++) {
        uint32_t acc = SEED[k];
        for (size_t i = 0; i < n; i++) {
            uint8_t c = (uint8_t)user[i];
            acc += ((uint32_t)c + 1u) * (uint32_t)(i + 1 + k);
        }
        out[k] = (uint16_t)(acc & 0xFFFF);
    }
}

/*
 * Normalize the serial the user typed: keep only hex characters, drop '-' and
 * spaces, convert to uppercase. Returns the number of hex characters kept.
 */
static int normalize_serial(const char *in, char *out, int out_sz) {
    int j = 0;
    for (int i = 0; in[i] && j < out_sz - 1; i++) {
        char c = in[i];
        if (isxdigit((unsigned char)c)) {
            out[j++] = (char)toupper((unsigned char)c);
        }
    }
    out[j] = '\0';
    return j;
}

static int validate(const char *user, const char *serial) {
    if (strlen(user) == 0)
        return 0;

    uint16_t blk[4];
    compute_blocks(user, blk);

    char expected[32];
    snprintf(expected, sizeof(expected), "%04X%04X%04X%04X",
             blk[0], blk[1], blk[2], blk[3]);

    char got[64];
    int len = normalize_serial(serial, got, (int)sizeof(got));
    if (len != 16)
        return 0;

    return strcmp(expected, got) == 0;
}

int main(int argc, char **argv) {
    if (argc != 3) {
        printf("Usage: %s <username> <serial>\n", argv[0]);
        printf("The serial looks like XXXX-XXXX-XXXX-XXXX (hex).\n");
        return 1;
    }

    if (validate(argv[1], argv[2])) {
        printf("Correct! Valid serial for user '%s'.\n", argv[1]);
        return 0;
    } else {
        printf("Wrong serial. Try again.\n");
        return 1;
    }
}
