// target.c: a tiny file so you have a PE of your own to inspect in a hex editor.
// Build:
//   x86_64-w64-mingw32-gcc target.c -o target.exe   (x64)
//   i686-w64-mingw32-gcc  target.c -o target32.exe   (x86, to compare machine 0x14C)
#include <stdio.h>

int main(void) {
    const char *msg = "HEXLAB-MARKER-7788";  // a string that is easy to find in a hex editor
    printf("%s\n", msg);
    return 0;
}
