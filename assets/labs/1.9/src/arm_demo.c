// Lab 1.9: reading ARM64 for people who know x86
// Goal: cross-compile to ARM64, then compare the assembly with the source.
//
// Cross-compile (Linux, needs the gcc-aarch64-linux-gnu package):
//   sudo apt install gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu
//   aarch64-linux-gnu-gcc -O0 -o arm_demo arm_demo.c -static
//   aarch64-linux-gnu-objdump -d arm_demo | less      # view the disassembly
//
// If you want to run it:
//   sudo apt install qemu-user
//   qemu-aarch64 ./arm_demo 12345678
//
// Reading hint: look for the labels <add3>, <is_eight>, <check> in the objdump
// output, and pay attention to x0..x7 (parameters), x0 (return value), and
// the stp x29,x30 in the prologue of check.

#include <stdio.h>
#include <string.h>

// Simple leaf function: 3 parameters -> see them arrive in x0, x1, x2
int add3(int a, int b, int c) {
    return a + b + c;
}

// Returns 1/0: compare with a constant, so cmp + b.ne (or cbz) is easy to spot
int is_eight(int n) {
    if (n != 8)
        return 0;
    return 1;
}

// Non-leaf function: calls strlen and then is_eight -> must save lr on the stack
int check(const char *s) {
    int len = (int)strlen(s);   // there is a bl calling strlen
    return is_eight(len);       // there is a bl calling is_eight
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("usage: %s <string>\n", argv[0]);
        return 1;
    }
    printf("add3(1,2,3) = %d\n", add3(1, 2, 3));
    printf("check(\"%s\") = %d\n", argv[1], check(argv[1]));
    return 0;
}
