/*
 * selfcheck.c  -  demonstrates an integrity check (self-checksum)
 *
 * Idea: the function check_license() decides pass/fail. A separate
 * function verify_integrity() computes a checksum over the byte range
 * belonging to check_license() and compares it against an embedded
 * value. If someone patches check_license (for example NOPing a jump),
 * the checksum changes, verify_integrity notices, and it refuses to run.
 *
 * Build (Linux):
 *   gcc -O0 -no-pie -fno-pic -o selfcheck selfcheck.c
 *   (-no-pie keeps function addresses stable, easier to read in objdump)
 *
 * Step to print EXPECTED: set MODE_PRINT = 1, build and run, take the real
 * checksum, paste it into EXPECTED, then build again with MODE_PRINT = 0.
 */
#include <stdio.h>
#include <string.h>
#include <stdint.h>

#define MODE_PRINT 0

/* The embedded checksum (taken from a MODE_PRINT=1 build). */
static uint32_t EXPECTED = 0xDEADBEEF;

/* The protected function. We checksum its byte range. */
int check_license(const char *key) {
    /* The real logic: only the correct key passes. */
    if (strcmp(key, "INTEGRITY_OK") == 0)
        return 1;
    return 0;
}

/* Marker for the end of the code range to checksum. */
void end_marker(void) { }

/* A simple bitwise CRC32 over the range [start, end). */
static uint32_t crc32(const unsigned char *p, size_t n) {
    uint32_t c = 0xFFFFFFFFu;
    for (size_t i = 0; i < n; i++) {
        c ^= p[i];
        for (int k = 0; k < 8; k++)
            c = (c >> 1) ^ (0xEDB88320u & (-(int32_t)(c & 1)));
    }
    return ~c;
}

int verify_integrity(void) {
    const unsigned char *start = (const unsigned char *)check_license;
    const unsigned char *end   = (const unsigned char *)end_marker;
    size_t n = (size_t)(end - start);
    uint32_t got = crc32(start, n);
#if MODE_PRINT
    printf("[build] checksum = 0x%08X , size = %zu\n", got, n);
    return 1;
#else
    if (got != EXPECTED) {
        printf("[!] Integrity check FAILED (0x%08X != 0x%08X). The code was modified.\n",
               got, EXPECTED);
        return 0;
    }
    return 1;
#endif
}

int main(int argc, char **argv) {
    if (argc < 2) { printf("Usage: %s <key>\n", argv[0]); return 2; }

    if (!verify_integrity()) {
        /* Anti-tamper: refuse to run when the code has been modified. */
        return 3;
    }

    if (check_license(argv[1]))
        printf("Correct! License is valid.\n");
    else
        printf("Nope. Wrong key.\n");
    return 0;
}
