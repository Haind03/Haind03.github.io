/*
 * Lab 3.4: compare a static vs a dynamic binary and apply FLIRT.
 *
 * The program is deliberately small: only two functions are written by the
 * "author" (make_tag and main). Everything else that shows up in the static
 * binary is libc/CRT code, and that is what FLIRT will name for you.
 *
 * Build (Linux):
 *   Dynamic:  gcc -O0 -no-pie greet.c -o greet_dyn
 *   Static :  gcc -O0 -no-pie -static greet.c -o greet_static
 *
 * Compare sizes:  ls -l greet_dyn greet_static
 * (the static one is usually many times larger)
 *
 * Hint: -no-pie keeps addresses stable, easier to compare with the lesson.
 */
#include <stdio.h>
#include <string.h>

/* Author function no. 1: builds a simple tag. */
static void make_tag(const char *name, char *out, size_t cap)
{
    size_t n = strlen(name);
    snprintf(out, cap, "[user:%s len=%zu]", name, n);
}

/* Author function no. 2: main. */
int main(int argc, char **argv)
{
    char tag[64];
    const char *who = (argc > 1) ? argv[1] : "reverser";

    make_tag(who, tag, sizeof(tag));
    printf("Hello, %s\n", who);
    printf("Tag: %s\n", tag);
    return 0;
}
