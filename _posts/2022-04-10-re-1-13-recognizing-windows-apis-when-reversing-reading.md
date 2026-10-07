---
title: "Lesson 1.13: Recognizing Windows APIs when reversing"
image:
  path: /assets/img/covers/re-1-13-recognizing-windows-apis-when-reversing-reading.webp
  alt: "Lesson 1.13: Recognizing Windows APIs when reversing"
date: 2022-04-10 15:08:00 +0700
categories: ["Technique Reverse", "Part 01 · Computer Fundamentals for RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
In lesson [1.10](/posts/re-1-10-windows-internals-1-win32-api-dlls/) you saw that the API list shows what a program intends to do. In lesson [1.4](/posts/re-1-4-x86-x64-assembly-2-stack-frames/) you learned where parameters get passed. This lesson combines the two, so you can look at any API call in a disassembly or debugger and read off which file it's opening, which registry key it's writing, where it's connecting.

You'll do this a few hundred times every reversing session.

## Step one: know the function's prototype

To read the parameters you need to know how many the function takes and what each one is. The standard source is MSDN (Microsoft Learn). Type the function name in and you get the prototype.

Take `CreateFileW` as an example:

```c
HANDLE CreateFileW(
  LPCWSTR               lpFileName,            // param 1: file name (Unicode string)
  DWORD                 dwDesiredAccess,       // param 2: access rights
  DWORD                 dwShareMode,           // param 3: share mode
  LPSECURITY_ATTRIBUTES lpSecurityAttributes,  // param 4
  DWORD                 dwCreationDisposition,  // param 5
  DWORD                 dwFlagsAndAttributes,   // param 6
  HANDLE                hTemplateFile           // param 7
);
```

Seven parameters, returns a HANDLE. The `W` suffix means the Unicode version (`A` is ANSI), covered in lesson 1.10. The first parameter, the file name, is the one we care about most.

## Step two: where the parameters live

On Windows x64 (the Win64 calling convention, see lesson 1.4 again), the order is fixed. Parameters 1 to 4 go in `rcx`, `rdx`, `r8`, `r9`. Parameter 5 onwards is on the stack, at `[rsp+0x20]`, `[rsp+0x28]`, and so on (the first 0x20 bytes are shadow space, ignore them). The return value is in `rax`.

Mapped onto `CreateFileW`:

| Parameter | Location | Meaning |
|---|---|---|
| 1 lpFileName | `rcx` | pointer to the file name |
| 2 dwDesiredAccess | `rdx` | access (read/write) |
| 3 dwShareMode | `r8` | share mode |
| 4 lpSecurityAttributes | `r9` | usually 0 |
| 5 dwCreationDisposition | `[rsp+0x20]` | create new or open existing |
| 6 dwFlagsAndAttributes | `[rsp+0x28]` | attributes |
| 7 hTemplateFile | `[rsp+0x30]` | usually 0 |

Now real asm right before the call:

```asm
lea     r9, [rsp+0x40]        ; param 4 = lpSecurityAttributes (a pointer here, rare)
mov     dword ptr [rsp+0x28], 0x80   ; param 6 = FILE_ATTRIBUTE_NORMAL
mov     dword ptr [rsp+0x20], 3      ; param 5 = OPEN_EXISTING (3)
xor     r9d, r9d              ; param 4 = 0 (overwrite, lpSecurityAttributes = NULL)
mov     r8d, 1               ; param 3 = FILE_SHARE_READ
mov     edx, 0x80000000      ; param 2 = GENERIC_READ
lea     rcx, aConfigIni      ; param 1 = pointer to the string "config.ini"
call    CreateFileW
mov     [rbp+hFile], rax     ; save the returned HANDLE
```

Read backwards from the call. `rcx` points to the string `aConfigIni`, so the program is opening the file `config.ini`. `edx` = 0x80000000 is `GENERIC_READ`, so it's opened for reading. `[rsp+0x20]` = 3 is `OPEN_EXISTING`, open an existing file rather than creating a new one. `rax` is then stored, that's the file handle.

From the parameters alone you know the program opens config.ini for reading. No need to run it or guess.

Values like `0x80000000`, `3`, `0x80` are constants predefined in the Windows SDK (GENERIC_READ, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL). Look them up on MSDN or let IDA/Ghidra translate them (next step).

## Step three: let the tools do the boring part

You don't have to look things up by hand every time. When IDA or Ghidra recognizes a call as a known API, they annotate it for you.

In IDA, enable the right type library and it shows parameter names next to the setup instructions, like `; lpFileName`. The decompiler (F5) even merges the call into a single line of C, such as `CreateFileW(L"config.ini", 0x80000000, 1, 0, 3, 0x80, 0)`. In Ghidra, the decompiler applies the prototype from its own data, and you may have to apply the right signature if it doesn't recognize the function. Once that's done, the pseudocode shows clear parameter names. Both can turn constants into names (enums) if you assign the right type to that parameter, and seeing `3` become `OPEN_EXISTING` makes reading much faster.

Don't skip the manual reading, though. When you hit a rare API or the tool doesn't recognize it, you still have to look up MSDN yourself and count registers.

## Catching APIs at runtime

Sometimes a parameter only has its real value at runtime (a file name built from several strings, a registry key decrypted dynamically). Then switch to dynamic.

In x64dbg, set a breakpoint on the API function by name:

```
bp CreateFileW
```

When the program calls it, the debugger stops at the start of the function, before it runs. The parameters are still intact in `rcx`, `rdx`, `r8`, `r9` and on the stack. In the register window, right-click `rcx` and choose "Follow in Dump" and you see the file name string. It's the fastest way to find out what the program is opening right now.

API Monitor is more specialized, since it catches every API call with the parameters already decoded in a table, so you don't have to read registers manually. It's handy when you want the big picture of what a program touches. It's noisy though, so you need to know how to filter.

## When the API is hidden

Software authors (malware especially) don't always call APIs openly through the IAT. Two tricks come up often.

The first is calling indirectly via GetProcAddress. Instead of importing `CreateFileW` directly, the program calls `LoadLibrary("kernel32.dll")` then `GetProcAddress(h, "CreateFileW")` to get the function address at runtime, then `call`s through the pointer. In the static IAT you won't see `CreateFileW` anywhere. Look for `GetProcAddress` being called many times, or a function pointer called with `call rax` and no clear name. Set a breakpoint at `GetProcAddress` to see which function it's asking for, or run to the indirect call and see where `rax` points.

The second is API hashing, which is more sophisticated. The program doesn't contain the API name string at all, only a hash of the name, and it walks the DLL's export table itself, hashing each name and comparing. This hides the API name from strings and the IAT. A loop walking the module list in the PEB (see lesson [1.11](/posts/re-1-11-windows-internals-2-peb-teb-handles/)) followed by a hash computation is this trick. Tools like Apiscout or hash-resolving scripts (compare the hash against a prebuilt table of API names) help recover the real names. This comes back in detail in the malware part.

You don't need to master these tricks right now. If you think "this program touches files but the IAT has no file function", it's probably hiding something, and you should switch to dynamic.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 1.13</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/1.13.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/1.13/src/apitarget.c" download><i class="fa-solid fa-download"></i>src/apitarget.c</a>
</div>
</div>

The target is a small C program, `apitarget.c`, that does two clear things. It opens (or creates) a file with `CreateFileW`, writes a line and closes it, then it opens a registry key with `RegOpenKeyExW`. The goal is to practice reading the parameters of an API call in the right Win64 register order, both by hand in x64dbg and with an automatic tool (API Monitor), and then compare the two. The program is harmless and fine to run on a normal machine.

Build a 64-bit version so it matches the Win64 register order from the lesson. With MSVC, from a Developer Command Prompt:

```
cl /Zi apitarget.c
```

Or with MinGW:

```
x86_64-w64-mingw32-gcc -g apitarget.c -o apitarget.exe -ladvapi32
```

If you build 32-bit instead, the parameters live on the stack under stdcall, so go back to lesson 1.4.

Open `apitarget.exe` in x64dbg and run to the entry point. In the Command box type `bp CreateFileW` and then `bp RegOpenKeyExW`, and press Run (F9). When it stops at `CreateFileW`, read the parameters. `rcx` points to the file name, so right-click it, choose Follow in Dump, and read the Unicode string. `rdx` is the desired access, so look the value up on MSDN and work out what GENERIC_WRITE is. `r8` is the share mode. The fifth parameter, `dwCreationDisposition`, is at `[rsp+0x20]`, so read it and look up its meaning. Then keep running to `RegOpenKeyExW` and read `rcx` (the root HKEY, to compare against HKEY_CURRENT_USER) and `rdx` (a pointer to the subkey name, again via Follow in Dump). Finally, run the program under API Monitor (filtering on the advapi32 and kernel32 modules) and compare its automatic output with what you read by hand.

Along the way, answer these questions. What is the full name of the file the program opens? Does it open it for reading or writing, and which parameter tells you? Which registry key is opened, under which root HKEY? And where does the return value (`rax`) land after each call, and what does it mean? Answer them all before opening the solution.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

When x64dbg stops at the start of `CreateFileW`, the registers carry exactly the Win64 prototype:

| Register / location | Parameter | Value in the lab | Meaning |
|---|---|---|---|
| `rcx` | lpFileName | pointer to `L"lab1_13_output.txt"` | the file to open; Follow in Dump to read the Unicode string (characters interleaved with 00 bytes) |
| `rdx` | dwDesiredAccess | `0x40000000` | GENERIC_WRITE, opened for writing |
| `r8` | dwShareMode | `1` | FILE_SHARE_READ |
| `r9` | lpSecurityAttributes | `0` | NULL |
| `[rsp+0x20]` | dwCreationDisposition | `2` | CREATE_ALWAYS, always create a new file (overwrite if it exists) |
| `[rsp+0x28]` | dwFlagsAndAttributes | `0x80` | FILE_ATTRIBUTE_NORMAL |
| `[rsp+0x30]` | hTemplateFile | `0` | NULL |

After the function finishes (step over with F8, or Ctrl+F9 to run to the ret), `rax` holds the file HANDLE. If `rax` is `0xFFFFFFFFFFFFFFFF` (INVALID_HANDLE_VALUE), the open failed. To read the Unicode string at rcx, right-click rcx, Follow in Dump, then in the Dump window right-click, Text, and choose UTF-16. You will see `lab1_13_output.txt`. From the parameters alone you can conclude that the program creates (overwriting) the file `lab1_13_output.txt` for writing.

For `RegOpenKeyExW` the prototype is:

```c
LSTATUS RegOpenKeyExW(HKEY hKey, LPCWSTR lpSubKey, DWORD ulOptions, REGSAM samDesired, PHKEY phkResult);
```

| Register / location | Parameter | Value in the lab | Meaning |
|---|---|---|---|
| `rcx` | hKey | `0x80000001` | HKEY_CURRENT_USER (a constant identifying the root) |
| `rdx` | lpSubKey | pointer to `L"Software\Microsoft\Windows"` | the subkey to open, via Follow in Dump |
| `r8` | ulOptions | `0` | no special flags |
| `r9` | samDesired | `0x20019` | KEY_READ |
| `[rsp+0x20]` | phkResult | pointer to an output variable | where the resulting HKEY is stored |

`rax` after the call is an LSTATUS return code, where `0` (ERROR_SUCCESS) means success. To recognize the root HKEY by value, `0x80000000` is HKEY_CLASSES_ROOT, `0x80000001` is HKEY_CURRENT_USER, `0x80000002` is HKEY_LOCAL_MACHINE and `0x80000003` is HKEY_USERS. So the program opens the key `HKEY_CURRENT_USER\Software\Microsoft\Windows` with read access.

API Monitor already shows the function name, each parameter decoded (including constant names like CREATE_ALWAYS and KEY_READ) and the return value, so its output should match the tables above. The only difference is that you do not have to look up the constants yourself. Reading by hand still matters when you meet an unfamiliar API, or cannot use API Monitor (for example against a sample that detects the tool).

Three things to take away. The Win64 order is fixed as `rcx rdx r8 r9`, then `[rsp+0x20]` and upward. Values like `0x80000001`, `0x40000000` and `0x20019` are Windows constants that you look up on MSDN or learn to recognize over time. And reading the parameters right at the start of the function, just after the breakpoint, is the most accurate, because no instruction has had the chance to overwrite the registers yet.

</details>

## Key takeaways
Always look up the prototype on MSDN first, to know the number and types of parameters. On Win64, parameters 1 to 4 are in `rcx rdx r8 r9`, parameter 5 onwards is at `[rsp+0x20]` going up, and the return is in `rax`. Read backwards from the `call` instruction to gather the prepared parameters.

Constants (0x80000000, 3...) are Windows macros, so look them up on MSDN or let IDA/Ghidra translate them into constant names. For parameters only known at runtime, use `bp CreateFileW` in x64dbg and read the registers, or use API Monitor. If the IAT lacks the API you expected, suspect indirect calls via GetProcAddress or API hashing, and switch to dynamic.
