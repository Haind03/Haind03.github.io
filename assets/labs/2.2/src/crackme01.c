/*
 * crackme01 - lab for Lesson 2.2 (IDA basics)
 *
 * Goal: find the correct password by reversing, WITHOUT reading this source.
 * (If you are reading the source you are cheating, open the built file in IDA.)
 *
 * Build on Windows (MSVC Developer Command Prompt):
 *     cl /Fe:crackme01.exe crackme01.c
 * Build on Windows (MinGW):
 *     x86_64-w64-mingw32-gcc crackme01.c -o crackme01.exe
 * Build on Linux:
 *     gcc crackme01.c -o crackme01
 *
 * Hint: build with the default optimization level (-O0), it is easier to
 * read when you are just starting out.
 */

#include <stdio.h>
#include <string.h>

/* The check function shows up in IDA as sub_xxxxxx until you rename it. */
static int check_password(const char *input)
{
    const char *secret = "R3v3rs3_M3";
    if (strlen(input) != strlen(secret))
        return 0;
    if (strcmp(input, secret) == 0)
        return 1;
    return 0;
}

int main(void)
{
    char buffer[64];

    printf("Enter password: ");
    if (!fgets(buffer, sizeof(buffer), stdin))
        return 1;

    /* strip the trailing newline if there is one */
    buffer[strcspn(buffer, "\r\n")] = '\0';

    if (check_password(buffer))
        printf("Correct! Congratulations, you solved the crackme.\n");
    else
        printf("Wrong password. Try again.\n");

    return 0;
}
