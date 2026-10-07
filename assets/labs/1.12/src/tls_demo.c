/*
 * tls_demo.c
 * Demonstrates a TLS callback running BEFORE the entry point (main).
 *
 * Build with MSVC (Developer Command Prompt):
 *     cl /nologo tls_demo.c
 *
 * Build with MinGW:
 *     gcc tls_demo.c -o tls_demo.exe
 *
 * Run: tls_demo.exe
 * Observe: the "[TLS] callback ran" line is printed BEFORE the "[main] started" line.
 *
 * The way a TLS callback is registered differs between MSVC and MinGW, below is
 * the MSVC version. If you use MinGW, see the note at the end of the file.
 */

#include <windows.h>
#include <stdio.h>

/* The callback. Windows calls it when a process/thread starts and when it ends. */
void NTAPI tls_callback(PVOID handle, DWORD reason, PVOID reserved)
{
    if (reason == DLL_PROCESS_ATTACH) {
        printf("[TLS] callback ran (before main)\n");
        /*
         * This is where malware likes to hide debugger checks.
         * Illustrative example (harmless):
         */
        if (IsDebuggerPresent()) {
            printf("[TLS] debugger detected right from the TLS callback!\n");
        }
    }
}

/* Register the callback in the .CRT$XLB section so the loader finds it. MSVC syntax. */
#ifdef _MSC_VER
#pragma comment(linker, "/INCLUDE:_tls_used")   /* x86 */
#pragma comment(linker, "/INCLUDE:tls_used")    /* x64 */
#pragma const_seg(".CRT$XLB")
EXTERN_C const PIMAGE_TLS_CALLBACK p_tls_callback = tls_callback;
#pragma const_seg()
#endif

int main(void)
{
    printf("[main] started\n");
    printf("[main] if you saw the [TLS] line above, the callback ran first\n");
    return 0;
}

/*
 * Note for MinGW:
 * MinGW uses __attribute__((section(".CRT$XLB"))) and the _tls_used variable.
 * If you use MinGW, the simple way to practice is to build this file with MSVC,
 * or to download a crackme that already has a TLS callback from crackmes.one
 * and practice locating it in PE-bear and catching it in x64dbg (Tasks 1 and 2
 * still work).
 */
