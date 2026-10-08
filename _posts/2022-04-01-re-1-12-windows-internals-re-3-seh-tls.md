---
title: "Lesson 1.12: Windows internals for RE (3): SEH, TLS callbacks and syscalls"
image:
  path: /assets/img/covers/re-1-12-windows-internals-re-3-seh-tls.webp
  alt: "Lesson 1.12: Windows internals for RE (3): SEH, TLS callbacks and syscalls"
date: 2022-04-01 16:44:00 +0700
categories: ["Reverse Engineering", "Part 01 · Computer Fundamentals for RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
The three things in this lesson have one annoying thing in common, which is that they let code run in places you don't expect. An exception jumps the flow to a handler you haven't read. A TLS callback runs before `main` even starts. A syscall drops straight into the kernel and skips every Win32 function you're watching. Malware uses all three for that reason, so it's worth knowing how each one works.

## SEH

Structured Exception Handling (SEH) is the Windows mechanism for handling exceptions, such as divide by zero, bad memory access, or an error the code throws itself. Instead of crashing right away, Windows looks for a registered handler and hands control to it.

On x86, the SEH handler chain is a linked list on the stack, and the head pointer lives at `fs:[0]` (the first field of the TEB, see [Lesson 1.11](/posts/re-1-11-windows-internals-2-peb-teb-handles/)). Each record has two fields, a pointer to the next record and a pointer to the handler function.

```asm
; x86: manually registering an SEH handler, the classic pattern
push offset my_handler   ; handler address
push fs:[0]              ; link to the old handler
mov  fs:[0], esp         ; make the new record the head of the chain
```

On x64 it's different. SEH no longer lives on the stack, it relies on a static table in the PE (the `.pdata` section, the exception directory structure). That's safer against handler-overwrite attacks, but for you it means looking up a table instead of reading a chain off the stack.

VEH (Vectored Exception Handling) is an add-on. The handler is registered through `AddVectoredExceptionHandler`, runs before SEH, and isn't tied to any function frame. Malware likes VEH because it covers the whole process.

### Why it matters in RE

Malware abuses SEH/VEH to hide control flow and to resist analysis. One way is steering the flow with deliberate faults. The code triggers an exception (for example writing to a null address, or running `int 3`), and the real logic is in the handler. If you read statically and follow the straight-line flow, you'll miss the handler, because it looks like dead code.

The other way is debugger detection. When a debugger is attached, some exceptions (like the `int 3` breakpoint) get swallowed by the debugger and never reach the handler. The program registers a handler, throws an exception itself, then checks whether the handler ran. If it didn't, a debugger is attached. Details of this trick are in [Lesson 15.3](/reverse-engineering/).

If you see an `AddVectoredExceptionHandler` or a manual SEH registration pattern, put a breakpoint on that handler, because the logic you're after is probably in there and not in the main flow. In x64dbg, turn on the option to pass exceptions to the application instead of swallowing them, otherwise you'll never see the handler run.

## TLS callbacks

Thread Local Storage (TLS) exists so each thread gets its own copy of a variable. It also has a feature that gets abused more than its original purpose, namely TLS callbacks, which are functions called automatically whenever a process or thread starts up and exits.

TLS callbacks run before the program's entry point (`AddressOfEntryPoint`). So before the first line of code you thought was the start, other code has already run.

That's handy for anti-debug. The program puts a debugger check in a TLS callback. A beginner sets a breakpoint at the entry point and runs it, and by the time that breakpoint hits, the TLS callback has long finished and already spotted the debugger.

The TLS callback lives in the PE's TLS Directory, which points to a null-terminated array of function pointers:

```
TLS Directory -> AddressOfCallBacks -> [callback1, callback2, ..., NULL]
```

Open the TLS Directory in PE-bear or CFF Explorer to see whether there are any callbacks and where they point. In x64dbg, go to Options and enable breaking on "TLS Callbacks" (and also "System Breakpoint" and "Entry Breakpoint"). The debugger then stops at the first callback, before the entry point, so you can read it before it probes you.

Not every TLS callback is malicious. Plenty of runtimes and libraries use it legitimately. But if you see one in a suspicious file, read it first.

## Native API and the syscall layer

This part covers the whole path of a system call, and why tracing Win32 APIs sometimes still misses things.

From [Lesson 1.10](/posts/re-1-10-windows-internals-1-win32-api-dlls/) we know that kernel32 doesn't do the heavy lifting itself, it calls down into ntdll. The functions in ntdll have an `Nt` or `Zw` prefix (for example `NtCreateFile`, `NtAllocateVirtualMemory`). This is the Native API layer, the closest to the kernel in user mode. The full chain:

```
Program
   -> CreateFileW        (kernel32.dll, Win32 layer)
      -> NtCreateFile    (ntdll.dll, Native API)
         -> syscall      (switch down to kernel mode)
            -> the kernel half of NtCreateFile
```

The `syscall` instruction (x64) works like this. Put an identifying number (the system service number) into the `eax` register, then execute `syscall`. The CPU switches to kernel mode, and the kernel looks that number up in the service table (SSDT) to know which function to call.

A typical ntdll stub looks like this:

```asm
NtCreateFile:
    mov  r10, rcx          ; syscall calling convention
    mov  eax, 0x55         ; syscall number (example, varies by Windows version)
    syscall
    ret
```

Two things matter here. First, syscall numbers are not fixed. The `0x55` above is only right for one specific Windows version. Microsoft changes these numbers between versions, even between updates. Don't memorize numbers, look them up for the Windows build you're analyzing (there are public lookup tables per build).

Second, direct syscalls are how malware dodges hooks. Many EDRs and monitoring tools install hooks at the start of the `Nt*` functions in ntdll (inline hooks, [Lesson 17.3](/reverse-engineering/)) to catch every call. Malware gets around that by embedding `mov eax, <number>; syscall` in its own code and not going through ntdll, so the hook never triggers. This is called a direct syscall. Variants like "indirect syscall" jump to the `syscall` instruction that already sits inside ntdll so it looks more natural.

We learn the mechanism here to detect and analyze it, not to write it. When reversing, the sign is a `syscall` instruction in the code of the module you're analyzing (not in ntdll), or a snippet that loads a number into `eax` and then does `syscall` without an import. That means the program is trying to avoid the usual monitoring layer, and you have to observe at a lower level (kernel callbacks, ETW, or a hardware breakpoint on the syscall instruction itself).

In practice, if you only hook or set breakpoints at the kernel32 level, a program that calls ntdll directly slips through. Set breakpoints at the `Nt*` layer in ntdll instead. If even that misses, it's likely using direct syscalls.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 1.12</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/1.12.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/1.12/src/tls_demo.c" download><i class="fa-solid fa-download"></i>src/tls_demo.c</a>
</div>
</div>

In this lab you check that a TLS callback runs before the entry point, find it inside the PE, and watch a system call go down to the `Nt*` layer of ntdll. Everything here uses a binary you build or a clean system file, so it's safe to run on a normal machine, and there's no malware involved. You need x64dbg (x32dbg for a 32-bit build), PE-bear or CFF Explorer, and a compiler, either MSVC (`cl.exe`) or MinGW (`gcc`), to build the demo `tls_demo.c`.

Build it with one of these and run it directly:

```
cl /nologo tls_demo.c
gcc tls_demo.c -o tls_demo.exe
```

Watch the order of the printed lines. The one from the TLS callback shows up before the one from `main`, which proves the callback runs before the entry point. Then open the file in PE-bear, go to Directories, find the TLS Directory, and note down `AddressOfCallBacks` and the address of the callback it points to.

Next, catch the callback in x64dbg. Open the file without running it, go to Options, Preferences, Events tab, and enable System Breakpoint, TLS Callbacks and Entry Breakpoint. Press Run. The debugger should stop first at the TLS callback, before the entry point, and the address should match the callback address you read in PE-bear. Press Run again and it stops at the entry point.

Finally, follow a call down into ntdll. In x64dbg, with any process (the demo file works), set a breakpoint on a Win32 function by typing `bp CreateFileW` in the command box. When it hits, keep pressing Step Into (F7) and you'll see it call `NtCreateFile` in ntdll. Once you reach the `NtCreateFile` stub, look for `mov r10, rcx`, then `mov eax, <number>`, then `syscall`, and write down the syscall number on your machine. That's the Native API layer right next to the kernel.

Two questions to think about. If a program puts its debugger check in a TLS callback, why is a breakpoint on `main` too late? And if you only break on `CreateFileW` (kernel32) but the malware calls `NtCreateFile` directly or uses a direct syscall, will your breakpoint hit, and why?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Task 1, TLS callback before main. After building and running `tls_demo.exe`, the output should be:

```
[TLS] callback ran (before main)
[main] started
[main] if you saw the [TLS] line above, the callback ran first
```

The `[TLS]` line comes first even though `main` is the main function in the source. The Windows loader calls every TLS callback while initializing the process, before handing control to the entry point, which is where the CRT startup code then calls `main`.

In PE-bear, open the file and look in the Directories tab, or in the tree on the left, for TLS. `AddressOfCallBacks` is an address pointing to an array of callback pointers. The first element is the address of `tls_callback` and the next element is null, which ends the array. Write down the callback address, for example `0x140001070` (the exact number depends on the machine and compiler).

Task 2, catching it in x64dbg. After enabling System Breakpoint, TLS Callbacks and Entry Breakpoint in Options and pressing Run, the first stop leaves the instruction pointer at the TLS callback address, which equals the one you read in Task 1. The x64dbg log window usually says "TLS Callback 1" explicitly. The next Run stops at the Entry Point. If a program hides a debugger check in a callback, you have to stop at this first break to read it in time.

Task 3, going down to ntdll. Set `bp CreateFileW` and Step Into several times once it hits. The path you see looks like this:

```
CreateFileW        (kernel32.dll)   ; Win32 layer, normalizes parameters
  -> NtCreateFile  (ntdll.dll)      ; Native API
       mov r10, rcx
       mov eax, 0x55                ; syscall number, AN EXAMPLE, yours may differ
       syscall                      ; switch down to the kernel
       ret
```

The number after `mov eax,` is the system service number. It differs between Windows versions, so the one you see is almost certainly not `0x55`. Don't memorize the numbers.

Why is a breakpoint on main too late for a TLS callback? The TLS callback runs before the entry point, and `main` runs even after the entry point (via the CRT startup). By the time a breakpoint on `main` hits, the callback finished long ago. If it probed for a debugger and already reacted (exited, took a fake branch, corrupted data), all you get to see is the aftermath. You have to stop at the TLS callback.

Will a breakpoint on `CreateFileW` hit when the malware calls `NtCreateFile` directly or uses a direct syscall? No. `bp CreateFileW` only stops when kernel32's `CreateFileW` is called. If the malware calls `NtCreateFile` in ntdll directly, it skips kernel32 and your breakpoint never fires. If it uses a direct syscall (placing `mov eax, <number>; syscall` into its own code), even a breakpoint on `NtCreateFile` in ntdll misses, because it never calls any ntdll function at all.

The lower you put the breakpoint, the harder it is to dodge. From weakest to strongest, the order is kernel32, ntdll (`Nt*`), the `syscall` instruction itself. When you suspect direct syscalls, find the `syscall` instructions and put hardware breakpoints on them, or observe at the kernel callback and ETW level, which user-mode code can't reach.

</details>

## Key takeaways
SEH/VEH let code jump to a handler that the straight-line flow doesn't show, and malware throws exceptions on purpose to hide logic or probe for debuggers. Put a breakpoint at the handler and let the debugger pass the exception to the program. x86 keeps the SEH chain on the stack at `fs:[0]`, while x64 uses a static table in `.pdata`.

TLS callbacks run before the entry point, so check the TLS Directory and enable breaking on TLS callbacks in x64dbg before running.

The call chain is Win32 (kernel32), then Native API (ntdll, `Nt`/`Zw`), then `syscall`, then the kernel. Syscall numbers change by Windows version, so look them up. Direct syscalls dodge hooks in ntdll, and the sign is a `syscall` instruction inside the module's own code, not via imports. When you hit one, move your observation down a level.
