/*
 * antivm.c - demonstrates anti-VM checks for Lesson 15.5
 *
 * ONLY use this to learn about anti-VM, run it on your own machine/VM.
 * The program checks a few VM indicators and prints a conclusion.
 *
 * Build on Windows (MSVC):   cl antivm.c
 * Build on Windows (MinGW):  x86_64-w64-mingw32-gcc antivm.c -o antivm.exe
 * Build on Linux (only the CPUID part runs, the registry part is skipped):
 *     gcc antivm.c -o antivm -DLINUX_BUILD
 *
 * Note: the registry/MAC part only makes sense on Windows. On Linux only
 * the CPUID check runs, which is still enough to see the hypervisor bit
 * differ between a real machine and a VM.
 */

#include <stdio.h>
#include <string.h>

/* Read CPUID: returns the 4 registers eax/ebx/ecx/edx for a given leaf */
static void do_cpuid(unsigned int leaf, unsigned int regs[4]) {
#if defined(_MSC_VER)
    int r[4];
    __cpuid(r, (int)leaf);
    regs[0]=r[0]; regs[1]=r[1]; regs[2]=r[2]; regs[3]=r[3];
#else
    unsigned int a,b,c,d;
    __asm__ volatile("cpuid"
                     : "=a"(a), "=b"(b), "=c"(c), "=d"(d)
                     : "a"(leaf), "c"(0));
    regs[0]=a; regs[1]=b; regs[2]=c; regs[3]=d;
#endif
}

#if defined(_MSC_VER)
#include <intrin.h>
#endif

/* Check 1: hypervisor present bit = bit 31 of ECX at CPUID leaf 1 */
static int check_hypervisor_bit(void) {
    unsigned int regs[4];
    do_cpuid(1, regs);
    return (regs[2] >> 31) & 1;   /* 1 = running under a hypervisor */
}

/* Check 2: vendor string at leaf 0x40000000 (e.g. "VMwareVMware") */
static void get_hypervisor_vendor(char out[13]) {
    unsigned int regs[4];
    do_cpuid(0x40000000u, regs);
    memcpy(out + 0, &regs[1], 4);   /* ebx */
    memcpy(out + 4, &regs[2], 4);   /* ecx */
    memcpy(out + 8, &regs[3], 4);   /* edx */
    out[12] = '\0';
}

#if defined(_WIN32) && !defined(LINUX_BUILD)
#include <windows.h>

/* Check 3: VM registry artifacts (illustrating just a few keys) */
static int check_registry_artefacts(void) {
    const char *keys[] = {
        "SOFTWARE\\VMware, Inc.\\VMware Tools",
        "SOFTWARE\\Oracle\\VirtualBox Guest Additions",
        "HARDWARE\\ACPI\\DSDT\\VBOX__",
    };
    int hits = 0;
    for (int i = 0; i < 3; i++) {
        HKEY h;
        if (RegOpenKeyExA(HKEY_LOCAL_MACHINE, keys[i], 0, KEY_READ, &h) == ERROR_SUCCESS) {
            hits++;
            RegCloseKey(h);
        }
    }
    return hits;
}
#endif

int main(void) {
    int in_vm = 0;

    if (check_hypervisor_bit()) {
        printf("[+] Hypervisor present bit (CPUID.1:ECX[31]) = 1\n");
        in_vm = 1;
    } else {
        printf("[-] Hypervisor present bit = 0\n");
    }

    char vendor[13];
    get_hypervisor_vendor(vendor);
    printf("    CPUID 0x40000000 vendor: \"%s\"\n", vendor);
    if (vendor[0] != '\0') in_vm = 1;

#if defined(_WIN32) && !defined(LINUX_BUILD)
    int reg = check_registry_artefacts();
    printf("[%c] Registry VM artefacts: %d\n", reg ? '+' : '-', reg);
    if (reg) in_vm = 1;
#endif

    printf("\n==> Conclusion: %s\n", in_vm ? "running inside a VM/hypervisor" : "looks like a real machine");
    return 0;
}
