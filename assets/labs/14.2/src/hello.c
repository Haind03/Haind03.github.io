#include <stdio.h>
#include <string.h>

/* Target program for practicing UPX unpacking.
   Build and pack:
     Linux:
       gcc -O2 -static -o hello hello.c
       upx --best -o hello.upx hello
     Windows (MinGW):
       x86_64-w64-mingw32-gcc -O2 -o hello.exe hello.c
       upx --best -o hello_upx.exe hello.exe
   Note: a file that is too small may fail with "NotCompressibleException";
   use -static (Linux) or add code so the file is large enough for UPX to compress. */

int check(const char *s) { return strcmp(s, "UPX_s3cr3t") == 0; }

int main(int argc, char **argv) {
    if (argc > 1 && check(argv[1]))
        puts("Correct!");
    else
        puts("Nope. Usage: hello <password>");
    return 0;
}
