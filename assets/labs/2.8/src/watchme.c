/*
 * watchme.c - target for the system monitoring practice in Lesson 2.8
 *
 * The program deliberately does a few things that are easy to spot in Procmon:
 *   1. Create and write a temporary file in the TEMP directory.
 *   2. Read a registry value (Windows only).
 *   3. Read an environment variable.
 *   4. Sleep for a moment so you have time to observe.
 *
 * Goal: run it under Procmon, filter by process name,
 * then find these file and registry operations in the sea of events.
 *
 * Build on Windows (MSVC Developer Prompt):
 *   cl /nologo watchme.c advapi32.lib
 * Build with MinGW:
 *   gcc watchme.c -o watchme.exe -ladvapi32
 *
 * On Linux the registry part is skipped, the file and env parts still run,
 * observe them with strace:
 *   gcc watchme.c -o watchme
 *   strace -f -e trace=open,openat,read,write,connect ./watchme
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>

static void do_file(void) {
    char path[MAX_PATH];
    char tmp[MAX_PATH];
    DWORD n = GetTempPathA(sizeof(tmp), tmp);
    if (n == 0 || n > sizeof(tmp)) {
        strcpy(tmp, ".\\");
    }
    snprintf(path, sizeof(path), "%swatchme_marker.txt", tmp);

    HANDLE h = CreateFileA(path, GENERIC_WRITE, 0, NULL,
                           CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (h != INVALID_HANDLE_VALUE) {
        const char *msg = "hello from watchme\r\n";
        DWORD written = 0;
        WriteFile(h, msg, (DWORD)strlen(msg), &written, NULL);
        CloseHandle(h);
        printf("[file] wrote: %s\n", path);
    } else {
        printf("[file] CreateFile failed: %lu\n", GetLastError());
    }
}

static void do_registry(void) {
    /* Read a harmless read-only value, change nothing. */
    HKEY hk;
    LONG r = RegOpenKeyExA(HKEY_LOCAL_MACHINE,
        "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
        0, KEY_READ, &hk);
    if (r == ERROR_SUCCESS) {
        char buf[256];
        DWORD sz = sizeof(buf);
        DWORD type = 0;
        if (RegQueryValueExA(hk, "ProductName", NULL, &type,
                             (LPBYTE)buf, &sz) == ERROR_SUCCESS) {
            printf("[registry] ProductName = %s\n", buf);
        }
        RegCloseKey(hk);
    } else {
        printf("[registry] RegOpenKeyEx failed: %ld\n", r);
    }
}

static void do_sleep(void) {
    printf("[sleep] sleeping 3 seconds so you can observe...\n");
    Sleep(3000);
}

#else /* Linux/macOS */
#include <unistd.h>

static void do_file(void) {
    const char *tmp = getenv("TMPDIR");
    char path[512];
    snprintf(path, sizeof(path), "%s/watchme_marker.txt",
             tmp ? tmp : "/tmp");
    FILE *f = fopen(path, "w");
    if (f) {
        fputs("hello from watchme\n", f);
        fclose(f);
        printf("[file] wrote: %s\n", path);
    } else {
        printf("[file] fopen failed\n");
    }
}

static void do_registry(void) {
    printf("[registry] skipped on this platform\n");
}

static void do_sleep(void) {
    printf("[sleep] sleeping 3 seconds so you can observe...\n");
    sleep(3);
}
#endif

int main(void) {
    const char *user = getenv(
#ifdef _WIN32
        "USERNAME"
#else
        "USER"
#endif
    );
    printf("[env] user = %s\n", user ? user : "(unknown)");

    do_file();
    do_registry();
    do_sleep();

    printf("done.\n");
    return 0;
}
