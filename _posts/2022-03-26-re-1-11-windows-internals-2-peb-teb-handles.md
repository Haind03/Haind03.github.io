---
title: "Lesson 1.11: Windows internals (2), PEB, TEB, handles and tokens"
date: 2022-03-26 20:50:00 +0700
categories: ["Technique Reverse", "Part 01 · Computer Fundamentals for RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
There's one data structure you'll run into again and again in Windows code, especially malware: the PEB. It sits right inside the process's address space, you don't need to call any API to reach it, and that's exactly why it's a gold mine for both anti-debug and sneaky module enumeration. Understanding the PEB and its few siblings (TEB, handles, tokens) means understanding a big chunk of code that looks like the Matrix if you don't know it.

## TEB and PEB, the process's two notebooks

Every thread has its own notebook called the TEB (Thread Environment Block), and every process has one shared notebook called the PEB (Process Environment Block). The OS builds these two structures in process memory to store all kinds of information about itself: where it's running, which DLLs it has loaded, whether it's being debugged, what the environment variables are.

The key point reversers need to notice is that you can get at them without calling any API. The CPU always keeps a pointer to the TEB in a special segment register:

```asm
; x64: get the TEB pointer, then the PEB
mov rax, gs:[0x30]      ; rax = TEB address
mov rax, gs:[0x60]      ; rax = PEB address (common shortcut)

; x86: use fs instead of gs
mov eax, fs:[0x18]      ; eax = TEB address
mov eax, fs:[0x30]      ; eax = PEB address
```

Seeing `gs:[0x60]` or `fs:[0x30]` in a disassembly should turn a light on right away: the code is reaching into the PEB. It doesn't call `GetModuleHandle` or `IsDebuggerPresent`, it reads directly. This is the number one reason beginners get confused, since there's no API name to look up.

## PEB fields you'll run into

The PEB has many fields, but the three below make up most of the times you'll touch it.

### BeingDebugged (offset +0x2)

This is one byte, equal to 1 when a debugger is attached to the process. Windows' `IsDebuggerPresent` internally reads exactly this byte and nothing more. So malware often skips the API and reads it directly:

```asm
mov rax, gs:[0x60]        ; PEB
movzx eax, byte ptr [rax+2]  ; read BeingDebugged
test eax, eax
jne  found_debugger       ; non-zero: being debugged
```

If you can read this snippet, you recognize a classic anti-debug trick, covered in detail in [Lesson 15.2](https://github.com/Haind03/Technique-Reverse/tree/main/phan-15-anti-reverse). The simplest way around it while debugging is to set that byte to 0.

### Ldr, the list of loaded modules

The `Ldr` field (offset +0x18 on x64) points to a structure holding three linked lists of every module (DLL) loaded into the process, with base address and name. This matters because malware walks the list to find the address of kernel32.dll on its own and then locate `GetProcAddress` and `LoadLibrary` without importing them. That way its import table is squeaky clean and looks harmless at a glance, and this is the foundation of shellcode and many loaders. So when you see code walking a linked list that starts from the PEB and compares name strings (usually by hash rather than the real name, to hide it), it's almost certainly resolving APIs by hand.

### NtGlobalFlag and heap flags

When a process runs under a debugger, Windows sets a few flags differently: `NtGlobalFlag` in the PEB carries bits like `FLG_HEAP_ENABLE_TAIL_CHECK`, and the heap has debug flags. Malware compares these flags against "normal" values to guess whether there's a debugger. Also anti-debug, also read straight from the PEB.

## Handles, how a process holds on to resources

When code opens a file, creates a thread or a mutex, Windows returns a HANDLE: a small integer that acts as a "ticket" referring to the real object living in the kernel. You never touch the object directly, you hand that ticket to APIs.

Two things here are useful for RE. Each process has its own handle table, so you can open a process in Process Hacker or System Informer and look at the Handles tab to see which files, registry keys, mutexes and connections it's holding. With malware this is a quick way to see what it touches before reading any code. The object types you see often are process, thread, file, event, mutex (mutant), section (shared memory) and registry key.

## Mutexes, a malware fingerprint

A mutex (mutual exclusion) is meant for synchronizing threads, but malware abuses it in a way that's very useful to analysts: it creates a mutex with a fixed name as soon as it runs, and if that mutex already exists it exits. The goal is to avoid infecting the same machine twice.

The result is that the mutex name becomes a great IOC (indicator of compromise). When you see `CreateMutexW` with a strange name string, write that string down right away, it can identify a whole malware family. Sometimes you can just create that mutex on the machine ahead of time and the malware thinks it already ran and doesn't run again, a simple "vaccine".

## Access tokens, who's allowed to do what

Every process carries an access token describing identity and rights: which user it runs as, which groups it belongs to, which privileges it has (for example `SeDebugPrivilege`, which lets it open other processes to read/write memory, the basis of injection). When you reverse a sample that tries to escalate privileges, you'll see it call `OpenProcessToken` and `AdjustTokenPrivileges` to enable `SeDebugPrivilege`. Recognizing this combo tells you it's preparing to touch another process.

## Lab

Details in [labs/1.11/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/1.11). In short, open any process in x64dbg, use a command to jump to the PEB, find the `BeingDebugged` byte and confirm it equals 1 (because it's being debugged). Then open Process Hacker or System Informer, look at the Handles tab of a process, and find the mutexes and files it's holding. Finally, check the offsets you see against the offset table in [solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/1.11/solution.md).

## Key takeaways
The TEB (per thread) and PEB (per process) sit right in process memory, reachable via `gs:[0x60]` (x64) or `fs:[0x30]` (x86) with no API needed. Seeing those in code means it's touching the PEB, usually for anti-debug or sneaky API resolution. BeingDebugged (+2) is the guts of `IsDebuggerPresent`, and Ldr holds the list of loaded modules.

A handle is a "ticket" referring to a kernel object, and the handle table in Process Hacker shows what a process touches. A fixed mutex name is a good IOC for identifying malware, and `SeDebugPrivilege` via `AdjustTokenPrivileges` is a sign of preparing for injection.
