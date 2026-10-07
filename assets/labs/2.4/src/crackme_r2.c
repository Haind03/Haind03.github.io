/*
 * crackme_r2.c  -  practice target for Lab 2.4
 *
 * Build (Linux):
 *   gcc -O0 -no-pie -o crackme_r2 crackme_r2.c
 * Build (Windows, MinGW):
 *   gcc -O0 -o crackme_r2.exe crackme_r2.c
 *
 * Run: enter a password and the program says whether it is right or wrong.
 * Task: find the correct password by analyzing the binary only (r2/Cutter/BN).
 * Do not read this source file if you want real practice.
 */
#include <stdio.h>
#include <string.h>

static int check_password(const char *input)
{
    const char *secret = "r2_rocks_2024";
    if (strlen(input) != strlen(secret))
        return 0;
    return strcmp(input, secret) == 0;
}

int main(void)
{
    char buf[64];

    printf("Enter password: ");
    if (!fgets(buf, sizeof(buf), stdin))
        return 1;

    /* strip the trailing newline */
    buf[strcspn(buf, "\r\n")] = '\0';

    if (check_password(buf))
        printf("Correct! You passed.\n");
    else
        printf("Wrong password, try again.\n");

    return 0;
}
