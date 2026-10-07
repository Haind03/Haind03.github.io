---
title: "Lesson 1.13: Recognizing Windows APIs when reversing, reading parameters like a sentence"
date: 2023-09-10 14:31:00 +0700
categories: ["Technique Reverse", "Part 01 · Computer Fundamentals for RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
In lesson [1.10](/posts/re-1-10-windows-internals-1-win32-api-dlls/) you saw that the API list is a map of what a program intends to do. In lesson [1.4](/posts/re-1-4-x86-x64-assembly-2-stack-frames/) you learned where parameters get passed. This lesson puts those two together into a daily skill: look at any API call in a disassembly or debugger, and read off which file it's opening, which registry key it's writing, where it's connecting.

This isn't theory anymore. It's something you'll do a few hundred times every reversing session.

## Step one: know the function's prototype

To read the parameters you need to know how many the function takes and what each one is. The standard source is MSDN (Microsoft Learn). Type the function name in and you get the prototype right away.

Take `CreateFileW` as an example, here's its prototype:

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

Seven parameters, returns a HANDLE. Remember the `W` suffix means the Unicode version (`A` is ANSI), covered in lesson 1.10. The first parameter, the file name, is the one we care about most.

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

Now look at real asm right before the call:

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

Read backwards from the call: `rcx` points to the string `aConfigIni`, so the program is opening the file `config.ini`. `edx` = 0x80000000 is `GENERIC_READ`, so it's opened for reading. `[rsp+0x20]` = 3 is `OPEN_EXISTING`, open an existing file rather than creating a new one. `rax` is then stashed away, that's the file handle.

Just by reading the parameters, you know: "the program opens config.ini for reading". No need to run it, no need to guess. That's the whole game.

A small convention that saves time: values like `0x80000000`, `3`, `0x80` are constants predefined in the Windows SDK (GENERIC_READ, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL). Look them up on MSDN or let IDA/Ghidra translate them (next step).

## Step three: let the tools do the boring part

Luckily you don't have to look things up by hand every time. When IDA or Ghidra recognizes a call as a known API, they annotate it for you.

In IDA, enable the right type library and it shows parameter names right next to the setup instructions, like `; lpFileName`. The decompiler (F5) even merges the call into a single readable line of C: `CreateFileW(L"config.ini", 0x80000000, 1, 0, 3, 0x80, 0)`. In Ghidra, the decompiler applies the prototype from its own data, and you may have to "apply" the right signature if it doesn't recognize the function. Once applied correctly, the pseudocode shows clear parameter names. Both can translate constants into constant names (enums) if you assign the right type to that parameter, and seeing `3` turn into `OPEN_EXISTING` makes reading much faster.

That doesn't mean skipping the manual reading. When you hit a rare API or the tool doesn't recognize it, you still have to look up MSDN yourself and count registers. The manual skill is what saves you when the tool goes quiet.

## Catching APIs at runtime, when static isn't enough

Sometimes a parameter only has its real value at runtime (a file name built from several strings, a registry key decrypted dynamically). Then switch to dynamic.

In x64dbg, set a breakpoint right at the API function by name:

```
bp CreateFileW
```

When the program calls it, the debugger stops at the start of the function, before it runs. At this point the parameters are sitting intact in `rcx`, `rdx`, `r8`, `r9` and on the stack. In the register window, right-click `rcx` and choose "Follow in Dump" and you see the file name string right away. This is the fastest way to find out "what is it opening right now".

A more specialized tool is API Monitor: it catches every API call with the parameters already decoded, laid out in a table, so you don't have to read registers manually. Very handy when you want the big picture of what a program touches. The tradeoff is that it's noisy, so you need to know how to filter.

## When the API is hidden

Software authors (malware especially) don't always call APIs openly through the IAT. There are two tricks you'll see often.

The first is calling indirectly via GetProcAddress. Instead of importing `CreateFileW` directly, the program calls `LoadLibrary("kernel32.dll")` then `GetProcAddress(h, "CreateFileW")` to get the function address at runtime, then `call`s through the pointer. In the static IAT you won't see `CreateFileW` anywhere. The tell is `GetProcAddress` getting called many times, or a function pointer getting called with `call rax` and no clear name. To deal with it, set a breakpoint at `GetProcAddress` to see which function it's asking for, or run to the indirect call and see where `rax` points.

The second is API hashing, which is more sophisticated. The program doesn't contain the API name string at all, only a hash of the name, then walks the DLL's export table itself, hashing each name and comparing. The point is to hide the API name completely from strings and the IAT. When you see a loop walking the module list in the PEB (see lesson [1.11](/posts/re-1-11-windows-internals-2-peb-teb-handles/)) and then computing a hash, you're looking at this trick. Tools like Apiscout or hash-resolving scripts (compare the hash against a prebuilt table of API names) help recover the real names. This topic comes back in detail in the malware part.

You don't need to master the API-hiding tricks right now. Just notice "wait, this program touches files but the IAT has no file function", that's the signal it's hiding something, and you know to switch to dynamic.

## Lab

The exercise is at [labs/1.13/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/1.13): build a small C program that calls `CreateFileW` and `RegOpenKeyExW`, then use x64dbg to set breakpoints at those two APIs and read all the parameters in the right register order, and compare with the API Monitor output. The solution is in `solution.md`, but read the parameters yourself first.

## Key takeaways
Always look up the prototype on MSDN first, to know the number and types of parameters. On Win64, parameters 1 to 4 are in `rcx rdx r8 r9`, parameter 5 onwards is at `[rsp+0x20]` going up, and the return is in `rax`. Read backwards from the `call` instruction to gather the prepared parameters.

Constants (0x80000000, 3...) are Windows macros, so look them up on MSDN or let IDA/Ghidra translate them into constant names. For parameters only known at runtime, use `bp CreateFileW` in x64dbg and read the registers, or use API Monitor. If the IAT lacks the API you expected, suspect indirect calls via GetProcAddress or API hashing, and switch to dynamic.
