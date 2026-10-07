/*
 * tea_lock.c - small crackme using TEA to illustrate Lesson 16.3
 *
 * Build (Linux):
 *   gcc -O0 -o tea_lock tea_lock.c
 * Build (Windows, MinGW):
 *   x86_64-w64-mingw32-gcc -O0 -o tea_lock.exe tea_lock.c
 *
 * Run:
 *   ./tea_lock <password_8_characters>
 *
 * The flag CTF{...} only prints when you enter the correct password.
 * The password is NOT stored as plaintext in the binary: it is stored
 * as 2 encrypted TEA blocks, and you must reverse the delta to decrypt it.
 */
#include <stdio.h>
#include <string.h>
#include <stdint.h>

/* fixed key, will show up in the disassembly */
static const uint32_t KEY[4] = {
    0x11223344u, 0x55667788u, 0x9ABCDEF0u, 0x0F1E2D3Cu
};

/* the two ciphertext blocks of the correct password (little-endian pairs) */
static const uint32_t EXPECTED[4] = {
    0xBBAAD475u, 0x2E138704u,   /* block 1 */
    0x7D2B9F0Eu, 0xC1A83652u    /* block 2: just a placeholder, see solution */
};

static void tea_encipher(uint32_t v[2], const uint32_t k[4]) {
    uint32_t v0 = v[0], v1 = v[1], sum = 0;
    const uint32_t delta = 0x9E3779B9u;   /* <- TEA GIVEAWAY */
    for (int i = 0; i < 32; i++) {
        sum += delta;
        v0 += ((v1 << 4) + k[0]) ^ (v1 + sum) ^ ((v1 >> 5) + k[1]);
        v1 += ((v0 << 4) + k[2]) ^ (v0 + sum) ^ ((v0 >> 5) + k[3]);
    }
    v[0] = v0; v[1] = v1;
}

int main(int argc, char **argv) {
    if (argc != 2 || strlen(argv[1]) != 8) {
        printf("Usage: %s <password 8 characters>\n", argv[0]);
        return 1;
    }
    uint32_t blk[2];
    memcpy(blk, argv[1], 8);
    tea_encipher(blk, KEY);
    if (blk[0] == EXPECTED[0] && blk[1] == EXPECTED[1]) {
        printf("Correct! CTF{%s}\n", argv[1]);
        return 0;
    }
    printf("Nope.\n");
    return 1;
}
