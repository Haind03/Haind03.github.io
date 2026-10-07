/*
 * Lab 15.4: anti-debug placed in a TLS callback (runs before main).
 *
 * Educational purpose: show why a check running in a TLS callback can decide
 * the program's fate BEFORE the entry point/main runs, which confuses
 * beginners with "it dies as soon as I run it in the debugger".
 *
 * Build (MSVC, recommended because declaring the TLS callback is concise):
 *   cl /GS- tls_antidebug.c
 *
 * Build (MinGW-w64):
 *   gcc tls_antidebug.c -o tls_antidebug.exe
 *
 * Normal run: prints "main: running normally".
 * Run under a debugger (TLS breakpoint not enabled): it may exit before you
 * see main, because the TLS callback detects the debugger and calls ExitProcess.
 *
 * Use only on your own machine/VM for learning, see Lesson 0.3.
 */

#include <windows.h>
#include <stdio.h>

/* Read PEB.BeingDebugged without an API (see Lesson 15.2). */
static int being_debugged(void)
{
#if defined(_WIN64)
    /* The PEB is at gs:[0x60], BeingDebugged is at offset 0x02 */
    PBYTE peb = (PBYTE)__readgsqword(0x60);
    return peb[2];
#else
    PBYTE peb = (PBYTE)__readfsdword(0x30);
    return peb[2];
#endif
}

/* TLS callback: the PE loader calls this function BEFORE the entry point. */
static void NTAPI tls_cb(PVOID handle, DWORD reason, PVOID reserved)
{
    (void)handle; (void)reserved;
    if (reason == DLL_PROCESS_ATTACH) {
        if (being_debugged()) {
            /* In practice malware may take a fake branch instead of exiting. */
            MessageBoxA(NULL, "Debugger detected in TLS callback", "anti-debug", MB_OK);
            ExitProcess(1);
        }
    }
}

/* Register the TLS callback in the .CRT$XLB section (the MSVC way). */
#ifdef _MSC_VER
#pragma comment(linker, "/INCLUDE:_tls_used")
#ifdef _WIN64
#pragma const_seg(".CRT$XLB")
const PIMAGE_TLS_CALLBACK p_tls_cb = tls_cb;
#pragma const_seg()
#else
#pragma data_seg(".CRT$XLB")
PIMAGE_TLS_CALLBACK p_tls_cb = tls_cb;
#pragma data_seg()
#endif
#else
/* MinGW: place it in .CRT$XLB via the section attribute. */
PIMAGE_TLS_CALLBACK p_tls_cb __attribute__((section(".CRT$XLB"))) = tls_cb;
#endif

int main(void)
{
    printf("main: running normally\n");
    return 0;
}
