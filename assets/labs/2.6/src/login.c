/*
 * Lab 2.6 - target for practicing GDB + pwndbg
 *
 * Build on Linux (x86-64):
 *   gcc -g -O0 -no-pie -o login login.c
 *
 * Flag explanation:
 *   -g       keeps debug symbols so breakpoints can be set by name
 *   -O0      no optimization, code stays close to the source, easy to read when learning
 *   -no-pie  disables PIE so addresses are fixed (0x4011xx...), no need to compute the base.
 *            Once comfortable, rebuild WITHOUT -no-pie to practice with ASLR.
 *
 * Run:
 *   ./login              then type any password
 *
 * Goal: do NOT edit the file, do NOT guess the password by eye.
 * Use GDB to either read out the correct password or force check_password to return 1.
 */
#include <stdio.h>
#include <string.h>

/* Check function: returns 1 if correct, 0 if wrong.
   The comparison is kept separate so you can easily set a breakpoint here. */
int check_password(const char *input)
{
    const char *secret = "r3v3rs3_m3";
    if (strcmp(input, secret) == 0)
        return 1;
    return 0;
}

int main(void)
{
    char buf[64];

    printf("Enter password: ");
    if (!fgets(buf, sizeof(buf), stdin))
        return 1;

    /* strip the trailing newline */
    buf[strcspn(buf, "\n")] = '\0';

    if (check_password(buf))
        printf("Correct! Welcome.\n");
    else
        printf("Wrong password.\n");

    return 0;
}
