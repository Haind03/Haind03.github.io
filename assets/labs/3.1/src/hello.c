#include <stdio.h>

/*
 * Lab 3.1: Hello world under the microscope.
 * Goal: start at the entry point and trace your way to the real main.
 *
 * Build on Linux (gcc):
 *   gcc -O0 -o hello_gcc hello.c
 *   # static build (bloated CRT, easy to see the difference):
 *   gcc -O0 -static -o hello_gcc_static hello.c
 *
 * Build on Windows (MSVC, open the "x64 Native Tools Command Prompt"):
 *   cl /Od hello.c /Fe:hello_msvc.exe
 *
 * Build on Windows (MinGW):
 *   x86_64-w64-mingw32-gcc -O0 -o hello_mingw.exe hello.c
 */

int main(void)
{
    printf("Hello, world\n");
    return 0;
}
