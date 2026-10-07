/*
 * Lab 16.1: recognizing crypto constants.
 * A minimal MD5 implementation (only the init part + constant table) so the binary
 * contains exactly the magic constants that findcrypt will catch.
 *
 * Build (Linux):   gcc -O0 -o hashdemo hashdemo.c
 * Build (Windows): cl hashdemo.c   /   gcc -O0 -o hashdemo.exe hashdemo.c
 *
 * Goal: open hashdemo in IDA/Ghidra, run findcrypt (or search by hand for
 * the byte sequence 01 23 45 67), and confirm these are the MD5 init values.
 */
#include <stdio.h>
#include <stdint.h>

/* MD5 init values: the classic fingerprint 0x67452301 ... */
static uint32_t md5_state[4] = {
    0x67452301u, 0xefcdab89u, 0x98badcfeu, 0x10325476u
};

/* MD5 per-round constants T[i] = floor(2^32 * abs(sin(i+1))), first 16 values */
static const uint32_t md5_T[16] = {
    0xd76aa478u, 0xe8c7b756u, 0x242070dbu, 0xc1bdceeeu,
    0xf57c0fafu, 0x4787c62au, 0xa8304613u, 0xfd469501u,
    0x698098d8u, 0x8b44f7afu, 0xffff5bb1u, 0x895cd7beu,
    0x6b901122u, 0xfd987193u, 0xa679438eu, 0x49b40821u
};

/* TEA also leaves its delta mark 0x9E3779B9 */
static uint32_t tea_round(uint32_t sum) {
    return sum + 0x9e3779b9u; /* golden ratio delta */
}

int main(void) {
    uint32_t acc = md5_state[0] ^ md5_T[0];
    uint32_t sum = tea_round(0);
    printf("acc=%08x sum=%08x\n", acc, sum);
    return 0;
}
