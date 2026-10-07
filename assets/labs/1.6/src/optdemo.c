/*
 * Lab 1.6: one source file, see how the optimizer transforms it.
 * Build it at -O0, -O2 (with and without strip) and -O3, then compare the disassembly.
 */
#include <stdio.h>
#include <string.h>

/* Small function: a candidate for the optimizer to inline into its caller. */
static int square(int x) {
    return x * x;
}

/* Fixed-count loop: a candidate for loop unrolling. */
static int sum_fixed(void) {
    int s = 0;
    for (int i = 0; i < 4; i++) {
        s += i;
    }
    return s;
}

/* Multiplication and division by constants: look for strength reduction. */
static int scale(int x) {
    int a = x * 8;      /* likely becomes shl x, 3 */
    int b = x / 3;      /* likely becomes multiply by reciprocal + shift */
    return a + b;
}

/* "Main logic" function, so the functions above have somewhere to be inlined into. */
static int compute(int n) {
    int r = square(n);      /* square may disappear, inlined */
    r += sum_fixed();       /* the loop may be flattened */
    r += scale(n);
    return r;
}

int main(int argc, char **argv) {
    int n = 5;
    if (argc > 1) {
        n = (int)strlen(argv[1]);
    }
    printf("compute(%d) = %d\n", n, compute(n));
    return 0;
}
