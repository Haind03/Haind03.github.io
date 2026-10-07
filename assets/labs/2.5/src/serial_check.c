/*
 * Lab 2.5 - a small crackme for x64dbg
 *
 * The program reads a serial from the command line (or stdin) and compares
 * it with the correct serial computed in code. The goals of the lab:
 *   1. Use x64dbg to catch the comparison and read the correct serial
 *      straight from the registers.
 *   2. Patch one jump so the program accepts any serial.
 *
 * Build on Windows:
 *   MSVC:   cl /Od /Zi serial_check.c
 *   MinGW:  gcc -O0 -g serial_check.c -o serial_check.exe
 *
 * Use /Od (MSVC) or -O0 (gcc) to keep it readable, same as in Lesson 1.6.
 */

#include <stdio.h>
#include <string.h>

/* Build the correct serial from a fixed "name", like a simple keygen.
 * The logic is kept light so a learner can work it out both statically
 * and dynamically. */
static void make_serial(char *out)
{
    const char *name = "reverser";
    int sum = 0;
    size_t i;

    for (i = 0; i < strlen(name); i++)
        sum += (unsigned char)name[i];

    /* serial looks like "RE-XXXX" where XXXX is sum times 7, printed in decimal */
    sprintf(out, "RE-%d", sum * 7);
}

static int check(const char *input)
{
    char correct[32];
    make_serial(correct);
    /* strcmp returns 0 when equal. This is where to put the breakpoint. */
    return strcmp(input, correct) == 0;
}

int main(int argc, char **argv)
{
    char buf[64];

    if (argc >= 2) {
        strncpy(buf, argv[1], sizeof(buf) - 1);
        buf[sizeof(buf) - 1] = '\0';
    } else {
        printf("Enter serial: ");
        if (!fgets(buf, sizeof(buf), stdin))
            return 1;
        buf[strcspn(buf, "\r\n")] = '\0';
    }

    if (check(buf)) {
        printf("Correct! Welcome.\n");
        return 0;
    } else {
        printf("Wrong serial.\n");
        return 1;
    }
}
