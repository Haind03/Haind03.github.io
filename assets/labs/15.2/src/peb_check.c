/*
 * peb_check.c  -  Anti-debug that reads the PEB directly, no API.
 *
 * Demo for Lesson 15.2. The program does NOT call IsDebuggerPresent.
 * It fetches the PEB itself through gs:[0x60] (x64), then reads BeingDebugged and NtGlobalFlag.
 *
 * Build on Windows (x64):
 *   MSVC:   cl /O2 peb_check.c
 *   MinGW:  x86_64-w64-mingw32-gcc -O2 peb_check.c -o peb_check.exe
 *
 * Run normally    -> "No debugger detected."
 * Run in x64dbg  -> "Debugger detected (PEB)."
 *
 * Honest note: this file is meant for Windows x64. Linux has no PEB, so it
 * cannot be built or run there; reading the code is enough to understand the mechanism.
 */

#include <stdio.h>
#include <windows.h>

/* Read the PEB through gs:[0x60] without using any Windows function.
   __readgsqword is an intrinsic that turns into a single mov gs:[...] instruction. */
static unsigned char* get_peb(void) {
#if defined(_M_X64) || defined(__x86_64__)
    return (unsigned char*)__readgsqword(0x60);
#else
    return (unsigned char*)__readfsdword(0x30);
#endif
}

int check_being_debugged(void) {
    unsigned char* peb = get_peb();
    /* offset 0x2: BeingDebugged (1 byte) */
    return peb[0x2] != 0;
}

int check_nt_global_flag(void) {
    unsigned char* peb = get_peb();
#if defined(_M_X64) || defined(__x86_64__)
    unsigned int flag = *(unsigned int*)(peb + 0xBC);
#else
    unsigned int flag = *(unsigned int*)(peb + 0x68);
#endif
    /* 0x70 = FLG_HEAP_ENABLE_TAIL_CHECK | FREE_CHECK | VALIDATE_PARAMETERS */
    return (flag & 0x70) == 0x70;
}

int main(void) {
    int bd  = check_being_debugged();
    int ngf = check_nt_global_flag();

    printf("BeingDebugged = %d\n", bd);
    printf("NtGlobalFlag debug bits = %d\n", ngf);

    if (bd || ngf) {
        printf("Debugger detected (PEB).\n");
        return 1;
    }
    printf("No debugger detected.\n");
    return 0;
}
