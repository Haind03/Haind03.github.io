/*
 * Lab 3.2: variables, pointers, arrays and strings under the microscope.
 *
 * Build (Linux / WSL), keep -O0 so it stays readable:
 *   gcc -O0 -g -o datatypes datatypes.c
 *
 * Build 64-bit on Windows (MinGW):
 *   x86_64-w64-mingw32-gcc -O0 -g -o datatypes.exe datatypes.c
 *
 * Or MSVC:
 *   cl /Od /Zi datatypes.c
 *
 * Goal: open it in IDA/Ghidra and recognize each kind yourself, following
 * the tasks in the lesson.
 */
#include <stdio.h>
#include <string.h>

/* global variables: in .data (with a value) and .bss (zero-initialized) */
int g_initialized = 1337;      /* .data */
int g_zero;                    /* .bss  */
char g_name[] = "ReverseMe";   /* global string in .rdata/.data */

/* returns the string length, hand-written to expose the null-terminated loop */
int my_strlen(const char *s)
{
    int n = 0;
    while (*s != '\0') {       /* *s = pointer dereference */
        n++;
        s++;                   /* the pointer advances one byte at a time */
    }
    return n;
}

/* sums an int array: shows the [base + index*4] pattern */
int sum_array(const int *arr, int len)
{
    int total = 0;
    for (int i = 0; i < len; i++)
        total += arr[i];       /* arr[i] = *(arr + i) */
    return total;
}

/* pointer to pointer: changes what the outer pointer points to */
void retarget(char **pp, char *newtarget)
{
    *pp = newtarget;           /* writes into the cell that pp points to */
}

int main(void)
{
    int local = 42;                 /* local variable on the stack: [rbp-x] */
    int numbers[5] = {10, 20, 30, 40, 50}; /* local array */
    char *p = g_name;               /* pointer to the global string */
    char *q = "second";

    g_zero = local + g_initialized;

    printf("len(%s) = %d\n", p, my_strlen(p));
    printf("sum = %d\n", sum_array(numbers, 5));

    retarget(&p, q);                /* pass the address of the pointer p */
    printf("p now = %s\n", p);

    return 0;
}
