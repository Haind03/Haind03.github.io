/*
 * Lab 1.4: observing calling conventions
 *
 * Build without optimization to keep the stack frame and the parameter-copy
 * instructions intact:
 *   Linux/macOS (System V):   gcc -O0 -g -o params params.c
 *   Windows (MSVC, Win64):    cl /Od /Zi params.c
 *   Windows (MinGW, Win64):   gcc -O0 -g -o params.exe params.c
 *
 * After building, open it in IDA/Ghidra/objdump and confirm:
 *   - Which register holds the i-th parameter (differs between Win64 and System V).
 *   - Where the 5th and 6th parameters spill onto the stack.
 *   - The 32-byte shadow space in the Win64 code.
 *   - Local variables show up as [rbp-x] (var_x in IDA).
 *
 * Quick disassembly without IDA:
 *   objdump -d -M intel params | less      (Linux)
 *   gdb -batch -ex "disassemble sum3" ./params
 */

#include <stdio.h>

/* 3 parameters: fits in registers under both conventions */
int sum3(int a, int b, int c) {
    int total = a + b + c;   /* total is a local variable -> [rbp-x] */
    return total;
}

/* 6 parameters: System V still fits them all in registers (rdi..r9),
 * while Win64 has only 4 parameter registers so parameters 5 and 6 go on the stack. */
int sum6(int a, int b, int c, int d, int e, int f) {
    return a + b + c + d + e + f;
}

/* Mixed data types to see whether the compiler uses a 32-bit (ecx) or 64-bit (rcx) register */
long mix(char x, int y, long z, int *p) {
    long r = (long)x + y + z;
    if (p) r += *p;
    return r;
}

int main(void) {
    int q = 100;
    printf("sum3 = %d\n", sum3(10, 20, 30));
    printf("sum6 = %d\n", sum6(1, 2, 3, 4, 5, 6));
    printf("mix  = %ld\n", mix('A', 7, 1000L, &q));
    return 0;
}
