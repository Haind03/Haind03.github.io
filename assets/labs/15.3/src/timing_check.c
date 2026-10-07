/*
 * Lab 15.3: anti-debug using timing (RDTSC) and a trap (INT 3).
 * EDUCATIONAL purpose: shows how debugger detection works so you can learn to get past it.
 *
 * Build on Windows:
 *   MinGW:  gcc -O0 timing_check.c -o timing_check.exe
 *   MSVC:   cl /Od timing_check.c
 *
 * Note: because it uses __rdtsc and SEH, it only makes full sense on Windows.
 * On Linux only the RDTSC part compiles (the SEH __try/__except part is dropped).
 */
#include <stdio.h>
#include <stdint.h>

#if defined(_WIN32)
#include <windows.h>
#include <intrin.h>  /* __rdtsc */
#endif

/* ---- Check 1: timing with RDTSC ----
 * Measures the CPU cycles elapsed between two points. If the code is being single-stepped,
 * the difference will be abnormally large.
 */
static int timing_rdtsc_detected(void)
{
#if defined(_WIN32) || defined(__x86_64__)
    uint64_t t1, t2;
    volatile int dummy = 0;

#if defined(_WIN32)
    t1 = __rdtsc();
#else
    unsigned int lo, hi;
    __asm__ __volatile__("rdtsc" : "=a"(lo), "=d"(hi));
    t1 = ((uint64_t)hi << 32) | lo;
#endif

    /* measured section: very short, running freely it costs only a few hundred cycles */
    for (int i = 0; i < 10; i++) dummy += i;

#if defined(_WIN32)
    t2 = __rdtsc();
#else
    {
        unsigned int lo2, hi2;
        __asm__ __volatile__("rdtsc" : "=a"(lo2), "=d"(hi2));
        t2 = ((uint64_t)hi2 << 32) | lo2;
    }
#endif

    uint64_t delta = t2 - t1;
    printf("[timing] delta = %llu cycles\n", (unsigned long long)delta);

    /* Threshold 100000: free running is usually a few hundred, single-stepping is millions. */
    return delta > 100000ULL;
#else
    return 0;
#endif
}

/* ---- Check 2: trap with INT 3 (Windows only, with SEH) ----
 * Raises an int 3 itself and catches the exception. If our OWN handler runs
 * it means we are NOT being debugged. If execution flows straight through (the handler is not
 * called) it means a debugger swallowed the breakpoint.
 */
#if defined(_WIN32)
static int int3_trap_detected(void)
{
    int handled = 0;
    __try {
        __debugbreak();   /* raises int 3 */
        /* reaching here = handler did not catch it = a debugger swallowed int 3 */
        handled = 0;
    }
    __except (EXCEPTION_EXECUTE_HANDLER) {
        /* our handler caught it = no debugger */
        handled = 1;
    }
    return handled ? 0 : 1;  /* not caught -> being debugged */
}
#endif

int main(void)
{
    int detected = 0;

    if (timing_rdtsc_detected()) {
        printf("[!] RDTSC timing: debugger detected\n");
        detected = 1;
    }

#if defined(_WIN32)
    if (int3_trap_detected()) {
        printf("[!] INT 3 trap: debugger detected\n");
        detected = 1;
    }
#endif

    if (detected)
        printf("=> Verdict: DEBUGGER DETECTED\n");
    else
        printf("=> Verdict: no debugger found, running normally\n");

    return 0;
}
