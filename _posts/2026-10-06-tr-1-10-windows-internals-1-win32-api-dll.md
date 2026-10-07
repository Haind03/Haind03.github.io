---
title: "Lesson 1.10: Windows internals (1), Win32 API and DLLs, reading intent from the function list"
date: 2026-10-06 08:13:00 +0700
categories: ["Technique Reverse", "Part 01 · Computer Fundamentals for RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
A Windows program can hardly do anything on its own. To open a file, it has to ask Windows. To get memory, create a thread, write to the registry or send a network packet, it all has to go through the OS. It asks by calling APIs. And this is the best news for anyone doing RE: **the list of APIs a program calls tells you almost the whole story of what it's trying to do, before you read a single line of assembly.**

This lesson teaches you to read that story.

## What is the Win32 API, and where does it live

The Win32 API is the set of public Windows functions for developers. They aren't inside your exe. They live in dynamic link libraries, the `.dll` files (Dynamic Link Library). At runtime the exe gets loaded together with the DLLs it needs, then calls functions in them.

A few core DLLs you should know by name, because the name alone tells you the functional area:

| DLL | What it holds |
|---|---|
| `kernel32.dll` | Core: file, process, thread, memory, module (CreateFile, VirtualAlloc, CreateThread, LoadLibrary) |
| `ntdll.dll` | Lowest layer in user mode, the gateway down to the kernel (the Nt*/Zw* functions) |
| `user32.dll` | UI: windows, messages, input (MessageBox, GetWindowText, SetWindowsHookEx) |
| `advapi32.dll` | Registry, services, tokens, legacy crypto (RegSetValueEx, OpenSCManager, CryptEncrypt) |
| `gdi32.dll` | 2D graphics drawing |
| `ws2_32.dll` / `wininet.dll` / `winhttp.dll` | Networking: sockets and HTTP |

## The call chain down to the kernel

Something a lot of beginners don't know: most functions in `kernel32.dll` don't do the real work themselves. They're just wrappers that call down into `ntdll.dll`, and `ntdll` is where the jump into the kernel happens (via the `syscall` instruction). For example:

```
Program -> CreateFileW (kernel32) -> NtCreateFile (ntdll) -> syscall -> kernel
```

Why this matters for RE: sophisticated malware often skips `kernel32` and calls the `Nt*` functions in `ntdll` directly, or even issues `syscall` itself, to dodge the hooks security tools place at the kernel32 level. If an ordinary-looking program calls `NtCreateFile` or `NtAllocateVirtualMemory` directly, that's worth noticing. Native API and syscalls get a deeper look in lesson [1.12](/posts/tr-1-12-windows-internals-3-seh-tls-syscall/).

## A and W, two versions of almost every function

You'll see `CreateFileA` and `CreateFileW`, `MessageBoxA` and `MessageBoxW`. The suffix tells you the string type. `A` means ANSI, strings with 1 byte per character (the old style), and `W` means Wide, Unicode UTF-16 strings with 2 bytes per character (the modern Windows style).

When reading in IDA, knowing the suffix tells you what kind of string to look for in memory. A W string in a hex editor has `00` bytes interleaved (`H.e.l.l.o.`), while an A string is contiguous. Mix this up and you'll search for a string forever without finding it.

## Two ways a program calls an API

This is the core part, because it decides where you see the API.

### Static import, through the IAT

The normal way: at compile time, the linker writes a list into the PE file saying "I need function X from DLL Y". This list sits in the Import Directory, and at load time Windows fills in the real address of each function into a table called the IAT (Import Address Table). Every API call in the code goes through this table.

What's great for you: the import list is right there in the file, readable without running anything. Open DIE or PE-bear and you see every function the program intends to use. This is the first thing you look at after triage.

### Dynamic, through LoadLibrary and GetProcAddress

The hiding way: the program doesn't declare imports up front, and only calls these at runtime:

```c
HMODULE h = LoadLibrary("wininet.dll");      // load the DLL
void* f = GetProcAddress(h, "InternetOpenA"); // get the function address by name
f(...);                                        // call it
```

The `LoadLibrary` + `GetProcAddress` pair is the classic signature of dynamic API calls. Malware likes this because the static import list looks clean and harmless, and the real functions only show up at runtime. Sometimes the function names are even string-encrypted to fool a static reader too. If you see `GetProcAddress` called many times in a loop, it's building its own private API table, a red flag.

Practical takeaway: static imports give you the picture on disk, but don't trust that it's complete. Always keep an eye out for `LoadLibrary`/`GetProcAddress`.

## Reading intent from API groups

This is the bread-and-butter skill. Group functions by purpose, and the presence of a group is a clue:

| Group | Typical functions | What it hints the program does |
|---|---|---|
| File | CreateFile, ReadFile, WriteFile, DeleteFile, FindFirstFile | Reads/writes/scans files. Ransomware that walks files will be full of this group |
| Registry | RegOpenKeyEx, RegSetValueEx, RegQueryValueEx | Reads/writes the registry, usually for config or to set up persistence |
| Process/Thread | CreateProcess, OpenProcess, CreateRemoteThread, CreateThread | Creates/tampers with processes. OpenProcess + CreateRemoteThread is the injection duo |
| Memory | VirtualAlloc, VirtualProtect, WriteProcessMemory | Allocates/changes memory permissions. VirtualAlloc with RWX plus a code write is a sign of unpacking/shellcode |
| Network | socket, connect, send, InternetOpen, HttpSendRequest, WinHttpConnect | Network communication, maybe downloading a payload or calling C2 |
| Crypto | CryptEncrypt, CryptDecrypt, BCryptEncrypt, CryptAcquireContext | Encrypts/decrypts, common in ransomware or for hiding config |
| Service | OpenSCManager, CreateService, StartService | Installs a service, a high-privilege kind of persistence |

Putting it together: if you see `CreateFile` + `CryptEncrypt` + `FindFirstFile` + `RegSetValueEx` all at once, before reading any code you can already suspect the program scans files, encrypts them, and writes something into the registry. That's the profile of ransomware. Static analysis afterwards just has to confirm it.

## Looking at imports in practice

A few quick ways to look at imports. DIE has an Import tab that lists DLLs and functions, which is handy for triage. PE-bear or CFF Explorer give a detailed view of the Import Directory, including the IAT. In IDA, the Imports window (Shift+F3 or View > Open subviews > Imports) gives you the list, and if you double-click a function and press `X` you see where it's called in the code. This is how you go from "the program calls VirtualAlloc" to "which function calls it, and with what arguments".

## Lab

The exercise is at [labs/1.10/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/1.10): open the imports of a few different exes and practice guessing their functionality from the API list alone, and put each function into the right purpose group. A sample writeup is in `solution.md`.

## Key takeaways
The Win32 API lives in DLLs (kernel32, user32, advapi32, ntdll...), and the exe calls into them to ask Windows to do things. kernel32 usually calls down into ntdll and then syscalls into the kernel, so calling Nt*/syscall directly is suspicious. The suffix A means ANSI and W means Unicode UTF-16 (with interleaved 00 bytes in memory).

Static imports show up in the IAT and can be read from the file (DIE/PE-bear). But LoadLibrary + GetProcAddress is how APIs get hidden, so always watch for it. Group APIs by purpose (file, registry, process, memory, network, crypto) to guess intent before reading code.
