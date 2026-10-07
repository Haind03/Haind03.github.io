#include <stdio.h>
#include <string.h>

/* Lab 16.4: a crackme meant to be solved with Z3.
 * The flag is 12 characters long. The program does NOT compare the input
 * directly against the flag, it checks a system of constraints on the
 * input bytes instead. You read this constraint system out of the binary
 * and hand it straight to Z3. */

static const unsigned char A[11] = {3,5,7,3,5,7,3,5,7,3,5};
static const unsigned char C[11] = {65,94,235,107,181,39,12,158,235,59,122};

int check(const unsigned char *f) {
    int i;
    for (i = 0; i < 12; i++)
        if (f[i] < 0x20 || f[i] > 0x7e) return 0;   /* printable */
    for (i = 0; i < 11; i++)
        if ((unsigned char)(A[i]*f[i] + f[i+1]) != C[i]) return 0;  /* chain */
    if ((f[0] ^ f[11]) != 0x7b) return 0;           /* cross xor 1 */
    if ((f[2] ^ f[5]) != 0x33) return 0;            /* cross xor 2 */
    unsigned int s = 0;
    for (i = 0; i < 12; i++) s += f[i];
    if (s != 988) return 0;                         /* sum */
    return 1;
}

int main(void) {
    unsigned char buf[64];
    printf("Enter flag: ");
    if (!fgets((char*)buf, sizeof buf, stdin)) return 1;
    size_t n = strlen((char*)buf);
    while (n && (buf[n-1]=='\n' || buf[n-1]=='\r')) buf[--n] = 0;
    if (n != 12) { printf("Wrong length.\n"); return 1; }
    if (check(buf)) printf("Correct! Valid flag.\n");
    else            printf("Nope.\n");
    return 0;
}
