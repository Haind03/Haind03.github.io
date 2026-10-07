/*
 * Lab 1.13: practice reading Windows API parameters.
 *
 * The program does two clear things so you can catch them at a breakpoint:
 *   1. CreateFileW: create and write the file lab1_13_output.txt
 *   2. RegOpenKeyExW: open a registry key under HKEY_CURRENT_USER
 *
 * Build 64-bit:
 *   MSVC:  cl /Zi apitarget.c
 *   MinGW: x86_64-w64-mingw32-gcc -g apitarget.c -o apitarget.exe -ladvapi32
 */

#include <windows.h>
#include <stdio.h>

int main(void)
{
    /* --- Part 1: CreateFileW --- */
    const wchar_t *path = L"lab1_13_output.txt";

    HANDLE hFile = CreateFileW(
        path,                       /* rcx: lpFileName                */
        GENERIC_WRITE,              /* rdx: dwDesiredAccess           */
        FILE_SHARE_READ,            /* r8:  dwShareMode               */
        NULL,                       /* r9:  lpSecurityAttributes      */
        CREATE_ALWAYS,              /* [rsp+0x20]: dwCreationDisposition */
        FILE_ATTRIBUTE_NORMAL,      /* [rsp+0x28]: dwFlagsAndAttributes  */
        NULL);                      /* [rsp+0x30]: hTemplateFile      */

    if (hFile != INVALID_HANDLE_VALUE) {
        const char *msg = "lab 1.13\r\n";
        DWORD written = 0;
        WriteFile(hFile, msg, (DWORD)lstrlenA(msg), &written, NULL);
        CloseHandle(hFile);
        wprintf(L"[+] Wrote file: %ls\n", path);
    } else {
        wprintf(L"[-] CreateFileW failed, GetLastError=%lu\n", GetLastError());
    }

    /* --- Part 2: RegOpenKeyExW --- */
    HKEY hKey = NULL;
    LONG rc = RegOpenKeyExW(
        HKEY_CURRENT_USER,                  /* rcx: root hKey         */
        L"Software\\Microsoft\\Windows",   /* rdx: lpSubKey        */
        0,                                  /* r8:  ulOptions       */
        KEY_READ,                           /* r9:  samDesired      */
        &hKey);                             /* [rsp+0x20]: phkResult */

    if (rc == ERROR_SUCCESS) {
        wprintf(L"[+] Opened registry key, HKEY=%p\n", (void *)hKey);
        RegCloseKey(hKey);
    } else {
        wprintf(L"[-] RegOpenKeyExW returned %ld\n", rc);
    }

    return 0;
}
