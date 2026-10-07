// crackme 3.5 - lab for lesson 3.5
// Build Linux:   gcc -O0 -no-pie -fno-stack-protector -o crackme crackme.c
// Build MinGW:   x86_64-w64-mingw32-gcc -O0 -o crackme.exe crackme.c
// Build MSVC:    cl /Od crackme.c
//
// Learning goal: find the correct password. The password is NOT in plaintext
// in strings because it has been transformed (XOR + sum check).

#include <stdio.h>
#include <string.h>

// constant array: the expected result after transforming each character
static const unsigned char expected[] = {
    0x08, 0x3F, 0x2C, 0x3F, 0x28, 0x29, 0x3F, 0x05, 0x6A, 0x6B
};
#define PASSLEN 10
#define XORKEY  0x5A

static int check_password(const char *input)
{
    if (strlen(input) != PASSLEN)
        return 0;

    int checksum = 0;
    for (int i = 0; i < PASSLEN; i++) {
        unsigned char t = (unsigned char)input[i] ^ XORKEY;
        if (t != expected[i])
            return 0;
        checksum += (unsigned char)input[i];
    }

    // second layer of protection: the sum of the ASCII codes must match
    if (checksum != 0x39C)
        return 0;

    return 1;
}

int main(void)
{
    char buf[64];
    printf("Enter password: ");
    if (!fgets(buf, sizeof(buf), stdin))
        return 1;
    buf[strcspn(buf, "\r\n")] = 0;

    if (check_password(buf))
        printf("Correct! Congratulations.\n");
    else
        printf("Wrong password.\n");
    return 0;
}
