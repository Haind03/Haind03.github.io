---
title: "Lesson 1.10: Windows internals (1), Win32 API and DLLs"
image:
  path: /assets/img/covers/re-1-10-windows-internals-1-win32-api-dlls.webp
  alt: "Lesson 1.10: Windows internals (1), Win32 API and DLLs"
date: 2022-03-26 21:45:00 +0700
categories: ["Technique Reverse", "Part 01 · Computer Fundamentals for RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
A Windows program can hardly do anything on its own. To open a file, get memory, create a thread, write to the registry or send a network packet, it has to ask Windows, and it does that by calling APIs. For RE this is useful because the list of APIs a program calls tells you most of what it's trying to do, before you read a single line of assembly.

This lesson is about reading that list.

## What the Win32 API is and where it lives

The Win32 API is the set of public Windows functions for developers. They aren't inside your exe. They live in dynamic link libraries, the `.dll` files. At runtime the exe gets loaded together with the DLLs it needs, then calls functions in them.

A few core DLLs to know by name, because the name tells you the functional area:

| DLL | What it holds |
|---|---|
| `kernel32.dll` | Core: file, process, thread, memory, module (CreateFile, VirtualAlloc, CreateThread, LoadLibrary) |
| `ntdll.dll` | Lowest layer in user mode, the gateway down to the kernel (the Nt*/Zw* functions) |
| `user32.dll` | UI: windows, messages, input (MessageBox, GetWindowText, SetWindowsHookEx) |
| `advapi32.dll` | Registry, services, tokens, legacy crypto (RegSetValueEx, OpenSCManager, CryptEncrypt) |
| `gdi32.dll` | 2D graphics drawing |
| `ws2_32.dll` / `wininet.dll` / `winhttp.dll` | Networking: sockets and HTTP |

## The call chain down to the kernel

A lot of beginners don't know that most functions in `kernel32.dll` don't do the real work. They're wrappers that call down into `ntdll.dll`, and `ntdll` is where the jump into the kernel happens (via the `syscall` instruction). For example:

```
Program -> CreateFileW (kernel32) -> NtCreateFile (ntdll) -> syscall -> kernel
```

This matters for RE because sophisticated malware often skips `kernel32` and calls the `Nt*` functions in `ntdll` directly, or even issues `syscall` itself, to dodge the hooks security tools place at the kernel32 level. If an ordinary-looking program calls `NtCreateFile` or `NtAllocateVirtualMemory` directly, take note. Native API and syscalls get a closer look in lesson [1.12](/posts/re-1-12-windows-internals-re-3-seh-tls/).

## A and W versions

Almost every function has two versions, like `CreateFileA` and `CreateFileW`, or `MessageBoxA` and `MessageBoxW`. The suffix tells you the string type. `A` means ANSI, 1 byte per character (the old style), and `W` means Wide, Unicode UTF-16 with 2 bytes per character (the modern Windows style).

In IDA, the suffix tells you what kind of string to look for in memory. A W string in a hex editor has `00` bytes interleaved (`H.e.l.l.o.`), while an A string is contiguous. If you mix this up you'll search for a string forever without finding it.

## Two ways a program calls an API

This decides where you see the API.

### Static import, through the IAT

In the normal way, at compile time, the linker writes a list into the PE file saying "I need function X from DLL Y". This list sits in the Import Directory, and at load time Windows fills in the real address of each function into a table called the IAT (Import Address Table). Every API call in the code goes through this table.

The import list is right there in the file, readable without running anything. Open DIE or PE-bear and you see every function the program intends to use. It's the first thing I look at after triage.

### Dynamic, through LoadLibrary and GetProcAddress

In the hiding way, the program doesn't declare imports up front, and only calls these at runtime:

```c
HMODULE h = LoadLibrary("wininet.dll");      // load the DLL
void* f = GetProcAddress(h, "InternetOpenA"); // get the function address by name
f(...);                                        // call it
```

The `LoadLibrary` + `GetProcAddress` pair is the classic sign of dynamic API calls. Malware likes this because the static import list looks clean and harmless, and the real functions only show up at runtime. Sometimes the function names are string-encrypted too, to fool a static reader. If you see `GetProcAddress` called many times in a loop, it's building its own private API table, which is suspicious.

Static imports give you the picture on disk, but don't trust that it's complete. Always watch for `LoadLibrary`/`GetProcAddress`.

## Reading intent from API groups

This is the everyday skill. Group functions by purpose, and the presence of a group is a clue:

| Group | Typical functions | What it hints the program does |
|---|---|---|
| File | CreateFile, ReadFile, WriteFile, DeleteFile, FindFirstFile | Reads/writes/scans files. Ransomware that walks files will be full of this group |
| Registry | RegOpenKeyEx, RegSetValueEx, RegQueryValueEx | Reads/writes the registry, usually for config or to set up persistence |
| Process/Thread | CreateProcess, OpenProcess, CreateRemoteThread, CreateThread | Creates/tampers with processes. OpenProcess + CreateRemoteThread is the injection duo |
| Memory | VirtualAlloc, VirtualProtect, WriteProcessMemory | Allocates/changes memory permissions. VirtualAlloc with RWX plus a code write is a sign of unpacking/shellcode |
| Network | socket, connect, send, InternetOpen, HttpSendRequest, WinHttpConnect | Network communication, maybe downloading a payload or calling C2 |
| Crypto | CryptEncrypt, CryptDecrypt, BCryptEncrypt, CryptAcquireContext | Encrypts/decrypts, common in ransomware or for hiding config |
| Service | OpenSCManager, CreateService, StartService | Installs a service, a high-privilege kind of persistence |

If you see `CreateFile` + `CryptEncrypt` + `FindFirstFile` + `RegSetValueEx` all at once, before reading any code you can already suspect the program scans files, encrypts them, and writes something into the registry. That's the profile of ransomware. Static analysis afterwards just has to confirm it.

## Looking at imports in practice

A few quick ways to look at imports. DIE has an Import tab that lists DLLs and functions, which is handy for triage. PE-bear or CFF Explorer give a detailed view of the Import Directory, including the IAT. In IDA, the Imports window (Shift+F3 or View > Open subviews > Imports) gives you the list, and if you double-click a function and press `X` you see where it's called in the code. That's how you go from "the program calls VirtualAlloc" to "which function calls it, and with what arguments".

## Lab

This lab trains the habit of looking at an import list and guessing what the program intends to do before reading any code. You need Detect It Easy (DIE), or PE-bear or CFF Explorer if you prefer. You don't need source code and you don't run anything.

Start by picking three or four exes of different kinds on your Windows machine, for example `notepad.exe` for text editing and file I/O, `calc.exe` or some small GUI app for the interface, a network utility such as `curl.exe` if you have it, and any installer, which usually touches files, the registry and processes. Drag each one into DIE and open the Import tab, then write down the DLLs it imports and a few notable functions. Before looking anything up, guess whether the program touches files, the registry or the network, and whether it creates child processes, then compare the guess with what you already know about the program.

Next, sort each of the following functions into the right group, File, Registry, Process-Thread, Memory, Network, Crypto or Service.

```
CreateFileW        RegSetValueExW     VirtualAllocEx
CreateRemoteThread InternetOpenA      BCryptEncrypt
FindFirstFileW     OpenProcess        HttpSendRequestW
WriteProcessMemory CreateServiceW     RegQueryValueExW
CryptAcquireContextW  ReadFile        connect
```

Then try to infer a profile. Suppose a sample imports exactly these functions and nothing else:

```
FindFirstFileW, FindNextFileW, CreateFileW, ReadFile, WriteFile,
CryptAcquireContextW, CryptEncrypt, RegSetValueExW, DeleteFileW
```

Without running it and without reading code, write one sentence saying what this program most likely does.

As an advanced extra, open a packed sample, or a tiny program whose imports are only a few functions such as `LoadLibraryA`, `GetProcAddress` and `VirtualAlloc`. Explain why such a short import list is suspicious and what the program might be hiding.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Inspecting imports. The real results depend on your Windows version, but the general pattern is stable. `notepad.exe` imports `kernel32.dll` (CreateFileW, ReadFile and WriteFile for reading and writing text files), `user32.dll` for windows and menus, and `comdlg32.dll` for the Open/Save dialogs. So the guess is right, it touches files, it has a GUI and it has no network. A small GUI app leans heavily on `user32.dll` and `gdi32.dll` for drawing and windows, with few or no file or network functions. `curl.exe` shows `ws2_32.dll` (sockets) or `wininet`/`libcurl`, plus file functions to write the output, so it's obviously a network tool. An installer usually has file (CreateFile), registry (RegSetValueEx) and process (CreateProcess to launch the next install step) functions all together. Many installers are packed, so their imports may look poor, see the last task. Even before running anything, the shape of the imports shows what kind of program it is.

Grouping the functions:

| Function | Group |
|---|---|
| CreateFileW, FindFirstFileW, ReadFile | File |
| RegSetValueExW, RegQueryValueExW | Registry |
| OpenProcess, CreateRemoteThread | Process/Thread (and injection) |
| VirtualAllocEx, WriteProcessMemory | Memory (writing into another process, injection) |
| InternetOpenA, HttpSendRequestW, connect | Network |
| BCryptEncrypt, CryptAcquireContextW | Crypto |
| CreateServiceW | Service |

Note that `OpenProcess` + `VirtualAllocEx` + `WriteProcessMemory` + `CreateRemoteThread` appearing together is the usual API combination for DLL or shellcode injection (see Part 17).

Inferring the profile. The functions enumerate files (`FindFirstFileW`/`FindNextFileW`), open and read/write them (`CreateFileW`, `ReadFile`, `WriteFile`), encrypt (`CryptAcquireContextW`, `CryptEncrypt`), write to the registry (`RegSetValueExW`) and delete files (`DeleteFileW`). My conclusion is that the program sweeps through files, reads their contents, encrypts them and writes the result over the original or as a new encrypted copy, deletes the original, and leaves a trace in the registry. That's the profile of ransomware. You can't be 100% sure from imports alone, but it's enough to put the sample in the dangerous bucket and analyze it in an isolated VM.

When the imports are too clean. A real PE almost always imports dozens of functions. When the list shrinks to `LoadLibraryA`, `GetProcAddress`, `VirtualAlloc` and a few odds and ends, the program resolves its APIs at runtime, and `GetProcAddress` fetches the real function addresses by name, so the static list looks harmless. `VirtualAlloc`, often with execute permission, allocates a region where decrypted code is written, which is typical of packers and shellcode loaders. A tiny import list doesn't mean a simple program. Usually it means the program is packed or is trying to hide its behavior. The next step is dynamic analysis, which is to set breakpoints on `GetProcAddress` and `VirtualAlloc` to catch the real APIs as they appear at runtime, or unpack first (Part 14) and read the real imports afterwards.

</details>

## Key takeaways
The Win32 API lives in DLLs (kernel32, user32, advapi32, ntdll...), and the exe calls into them to ask Windows to do things. kernel32 usually calls down into ntdll and then syscalls into the kernel, so calling Nt*/syscall directly is suspicious. The suffix A means ANSI and W means Unicode UTF-16 (with interleaved 00 bytes in memory).

Static imports show up in the IAT and can be read from the file (DIE/PE-bear). LoadLibrary + GetProcAddress is how APIs get hidden, so always watch for it. Group APIs by purpose (file, registry, process, memory, network, crypto) to guess intent before reading code.
