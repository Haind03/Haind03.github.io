/* strcrypt_demo.c
 * A program with several strings XORed with a single byte, decrypted at run time.
 * Build it to get a real binary for practicing writing a bulk string-decryption script.
 *   gcc -O0 -o strcrypt_demo strcrypt_demo.c
 * In IDA/Ghidra, the enc_* arrays are the encrypted strings (XOR 0x5A).
 */
#include <stdio.h>
#include <string.h>

#define KEY 0x5A

/* "Hello, reverser!" XOR 0x5A, terminated by the original 0 byte -> 0x5A */
static unsigned char enc_1[] = {0x12,0x3f,0x36,0x36,0x35,0x76,0x7a,0x28,0x3f,0x2c,0x3f,0x28,0x29,0x3f,0x28,0x7b,0x5a};
/* "secret_flag_42"  */
static unsigned char enc_2[] = {0x29,0x3f,0x39,0x28,0x3f,0x2e,0x05,0x3c,0x36,0x3b,0x3d,0x05,0x6e,0x68,0x5a};
/* "api: VirtualAlloc" */
static unsigned char enc_3[] = {0x3b,0x2a,0x33,0x60,0x7a,0x0c,0x33,0x28,0x2e,0x2f,0x3b,0x36,0x1b,0x36,0x36,0x35,0x39,0x5a};

static char *decrypt(unsigned char *enc, char *out) {
    int i = 0;
    while (enc[i] != KEY) { out[i] = enc[i] ^ KEY; i++; }
    out[i] = 0;
    return out;
}

int main(void) {
    char buf[64];
    printf("%s\n", decrypt(enc_1, buf));
    printf("%s\n", decrypt(enc_2, buf));
    printf("%s\n", decrypt(enc_3, buf));
    return 0;
}
