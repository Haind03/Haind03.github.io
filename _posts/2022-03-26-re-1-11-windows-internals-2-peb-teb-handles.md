---
title: "Lesson 1.11: Windows internals (2), PEB, TEB, handles and tokens"
image:
  path: /assets/img/covers/re-1-11-windows-internals-2-peb-teb-handles.webp
  alt: "Lesson 1.11: Windows internals (2), PEB, TEB, handles and tokens"
date: 2022-03-26 20:50:00 +0700
categories: ["Technique Reverse", "Part 01 · Computer Fundamentals for RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
The PEB is a data structure you'll keep running into in Windows code, especially malware. It lives in the process's own address space and you can read it without calling any API. That makes it useful for anti-debug tricks and for finding modules quietly. Once you know the PEB and the structures around it (TEB, handles, tokens), a lot of confusing-looking code starts to make sense.

## TEB and PEB

Every thread has a TEB (Thread Environment Block) and every process has one PEB (Process Environment Block). The OS builds both in process memory and stores information about the process there: where it's running, which DLLs are loaded, whether it's being debugged, the environment variables.

What matters for reversing is that you can reach them without any API call. The CPU keeps a pointer to the TEB in a segment register:

```asm
; x64: get the TEB pointer, then the PEB
mov rax, gs:[0x30]      ; rax = TEB address
mov rax, gs:[0x60]      ; rax = PEB address (common shortcut)

; x86: use fs instead of gs
mov eax, fs:[0x18]      ; eax = TEB address
mov eax, fs:[0x30]      ; eax = PEB address
```

When you see `gs:[0x60]` or `fs:[0x30]` in a disassembly, the code is reading the PEB. It doesn't call `GetModuleHandle` or `IsDebuggerPresent`, it just reads memory. Beginners get stuck here a lot because there's no API name to look up.

## PEB fields you'll run into

The PEB has many fields, but three of them cover most of what you'll see.

### BeingDebugged (offset +0x2)

One byte, equal to 1 when a debugger is attached. `IsDebuggerPresent` internally reads this byte and nothing else, so malware often skips the API and reads it directly:

```asm
mov rax, gs:[0x60]        ; PEB
movzx eax, byte ptr [rax+2]  ; read BeingDebugged
test eax, eax
jne  found_debugger       ; non-zero: being debugged
```

If you can read this snippet, you've recognized a classic anti-debug trick, covered in [Lesson 15.2](/technique-reverse/). The easy bypass while debugging is to set that byte to 0.

### Ldr, the list of loaded modules

The `Ldr` field (offset +0x18 on x64) points to a structure with three linked lists of every module (DLL) loaded in the process, with base address and name. Malware walks one of these lists to find kernel32.dll by itself, then finds `GetProcAddress` and `LoadLibrary` without importing them. Its import table stays clean and looks harmless, and shellcode and many loaders are built on this. So if you see code walking a linked list that starts from the PEB and compares names (usually hashes rather than the real names), it's almost certainly resolving APIs by hand.

### NtGlobalFlag and heap flags

Under a debugger Windows sets a few flags differently. `NtGlobalFlag` in the PEB carries bits like `FLG_HEAP_ENABLE_TAIL_CHECK`, and the heap gets debug flags too. Malware compares these against the normal values to guess whether a debugger is there. It's another anti-debug check read straight from the PEB.

## Handles

When code opens a file or creates a thread or a mutex, Windows returns a HANDLE. It's a small integer that refers to the real object in the kernel. You never touch the object directly, you pass the handle to APIs.

Two things are useful for RE. Each process has its own handle table, so you can open a process in Process Hacker or System Informer and look at the Handles tab to see which files, registry keys, mutexes and connections it holds. With malware this is a quick way to see what it touches before reading any code. Common object types are process, thread, file, event, mutex (mutant), section (shared memory) and registry key.

## Mutexes as a malware identifier

A mutex (mutual exclusion) is meant for synchronizing threads, but malware uses it to avoid infecting the same machine twice. It creates a mutex with a fixed name when it starts, and if that mutex already exists it exits.

This makes the mutex name a good IOC (indicator of compromise). When you see `CreateMutexW` with a strange name string, write it down. It can identify a whole malware family. Sometimes you can create that mutex on the machine ahead of time, and the malware thinks it already ran and doesn't start. A simple "vaccine".

## Access tokens

Every process carries an access token with its identity and rights: which user it runs as, which groups it belongs to, which privileges it has. One example is `SeDebugPrivilege`, which lets a process open other processes to read and write memory, and injection depends on it. When you reverse a sample that tries to escalate privileges, you'll see `OpenProcessToken` and `AdjustTokenPrivileges` used to enable `SeDebugPrivilege`. That combination means it's getting ready to touch another process.

## Lab

This lab needs no code. You watch a running process with x64dbg and Process Hacker (or System Informer), and the goal is to find the offsets from this lesson yourself. You need the 64-bit build of x64dbg, Process Hacker or System Informer, and any process to look at. `notepad.exe` is a safe choice, or any 64-bit program you wrote.

Start with `BeingDebugged` in the PEB. Open `notepad.exe` in x64dbg (File > Open) and let it stop at the entry point. Don't bother typing `mov rax, gs:[0x60]` in the Command box. Type the following instead, which makes the Dump window jump to the PEB, because x64dbg understands `peb()` as the PEB address of the debugged process.

```
dump peb()
```

In the Dump window, count two bytes from the start of the PEB (offset +0x2). That's `BeingDebugged`, and since you're debugging it should be `01`. Edit it to `00` (right-click > Binary > Edit, or type over it). This is the manual bypass for `IsDebuggerPresent`.

Next, `NtGlobalFlag` sits at offset +0xBC on x64. In the Dump window jump to `peb()+0xBC`. While being debugged the value is usually `0x70` (three heap debug bits on), and when the program runs normally it's 0. Write down the number you see.

Finally, handles and mutexes. Open Process Hacker and pick a process, ideally an app with a lot of open files or an offline game. Double-click it, go to the Handles tab and filter by type. `File` shows the open files, `Mutant` is the mutex (note the names, since in malware analysis they're IOCs), and `Key` shows registry keys. See if you can guess what the process is doing from this list alone, before reading any code.

When you're done you should have four things written down: the PEB address of the process you inspected, the value of `BeingDebugged` before and after the edit, the value of `NtGlobalFlag` while debugging, and one mutex name you found.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Try it yourself first. These are the PEB offsets you'll use most often on x64.

| Offset | Field | Meaning |
|---|---|---|
| +0x002 | BeingDebugged | 1 byte, equals 1 when being debugged |
| +0x018 | Ldr | pointer to PEB_LDR_DATA, the module list |
| +0x020 | ProcessParameters | command line, paths |
| +0x0BC | NtGlobalFlag | flags, equals 0x70 when debugged (heap debug bits) |
| +0x0F0 | HeapSegmentReserve | related to heap flags |

On x86 the offsets differ: BeingDebugged is +0x2, NtGlobalFlag is +0x68 and Ldr is +0x0C.

For the first task, after `dump peb()` the Dump window points at the start of the PEB. The third byte (offset +2) is `BeingDebugged`, and because you're debugging it reads `01`. After you set it to `00`, any call to `IsDebuggerPresent` reads this byte and returns 0, meaning no debugger. Anti-anti-debug plugins such as ScyllaHide work the same way: they keep this byte at 0 automatically and also patch `NtGlobalFlag` and many other checks. Lesson 15.9 covers it in detail.

For the second task, `NtGlobalFlag` is at `peb()+0xBC`. The value `0x70` is three bits: `FLG_HEAP_ENABLE_TAIL_CHECK` (0x10), `FLG_HEAP_ENABLE_FREE_CHECK` (0x20) and `FLG_HEAP_VALIDATE_PARAMETERS` (0x40). Outside a debugger all three are off, so the value is 0. Malware compares `NtGlobalFlag & 0x70` against 0 and assumes a debugger when it isn't zero. The bypass is to force the field back to 0.

For the third task, the `File` type in the Handles tab shows which files the process has open, so you can tell where it reads and writes. A `Mutant` (mutex) with a strange fixed name, like a GUID or a meaningless string, is worth writing down when you analyze malware, since many known families are recognized by their mutex name alone. The `Key` type shows registry keys, which is often where persistence gets installed.

Before you even open a disassembler, the handle table already tells you about half of what a process does. It's a very fast bit of dynamic triage.

</details>

## Key takeaways
The TEB (per thread) and PEB (per process) sit in process memory and can be reached through `gs:[0x60]` (x64) or `fs:[0x30]` (x86) with no API call. Code that does this is touching the PEB, usually for anti-debug or hand-rolled API resolution. BeingDebugged (+2) is what `IsDebuggerPresent` reads, and Ldr holds the list of loaded modules.

A handle refers to a kernel object, and the handle table in Process Hacker shows what a process touches. A fixed mutex name is a good IOC for identifying malware, and `SeDebugPrivilege` enabled through `AdjustTokenPrivileges` suggests it's preparing for injection.
