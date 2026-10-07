/*
 * antidump.c  -  Anti-dump demo: wipes its own PE header in memory
 *                after startup, so that an image dump turns into garbage.
 *
 * For learning on your own machine only. Build on Windows:
 *   cl antidump.c              (MSVC)
 *   x86_64-w64-mingw32-gcc antidump.c -o antidump.exe   (MinGW)
 *
 * Idea: GetModuleHandle(NULL) returns the exe's own ImageBase (the address
 * where the "MZ" header starts). We make that region writable and then blank
 * out the MZ and PE signatures. After this point, an ordinary image-dumping
 * tool no longer recognizes it as a valid PE.
 */
#include <windows.h>
#include <stdio.h>

static void wipe_pe_header(void) {
    BYTE *base = (BYTE *)GetModuleHandleA(NULL);   /* ImageBase, points at "MZ" */
    DWORD old;

    /* Make the first page writable (it holds the DOS + NT headers). */
    if (!VirtualProtect(base, 0x1000, PAGE_READWRITE, &old)) {
        printf("VirtualProtect failed: %lu\n", GetLastError());
        return;
    }

    /* Read the offset to the NT headers from e_lfanew before wiping. */
    LONG e_lfanew = *(LONG *)(base + 0x3C);

    /* Blank out the "MZ" signature (first 2 bytes). */
    base[0] = 0;
    base[1] = 0;

    /* Blank out the "PE\0\0" signature at the NT headers. */
    if (e_lfanew > 0 && e_lfanew < 0x1000) {
        BYTE *nt = base + e_lfanew;
        nt[0] = 0; nt[1] = 0;   /* 'P' 'E' */
    }

    VirtualProtect(base, 0x1000, old, &old);
    printf("Wiped the PE header in memory. Try dumping the image now.\n");
}

int main(void) {
    printf("The program is running normally (OEP already passed).\n");
    printf("ImageBase = %p\n", (void *)GetModuleHandleA(NULL));

    wipe_pe_header();

    /* Keep the process alive so you have time to attach and dump. */
    printf("Press Enter to exit...\n");
    getchar();
    return 0;
}
