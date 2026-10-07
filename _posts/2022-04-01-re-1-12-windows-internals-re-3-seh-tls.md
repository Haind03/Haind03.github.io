---
title: "Lesson 1.12: Windows internals for RE (3), SEH, TLS callbacks and the syscall layer"
date: 2022-04-01 16:44:00 +0700
categories: ["Technique Reverse", "Part 01 · Computer Fundamentals for RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
The three things in this lesson share an annoying trait: they let code run in places you don't expect. An exception jumps the flow to a handler you haven't read. A TLS callback runs before `main` even starts. And a syscall drops straight into the kernel, skipping every Win32 function you're watching. Malware loves all three for exactly that reason. Understanding them plugs three big holes in what you can observe.

## SEH, when an error doesn't kill the program

Structured Exception Handling (SEH) is the Windows mechanism for handling exceptions: divide by zero, bad memory access, or an error the code throws itself. Instead of crashing right away, Windows looks for a registered handler and hands control to it.

On x86, the SEH handler chain is a linked list on the stack, and the head pointer lives at `fs:[0]` (the first field of the TEB, see [Lesson 1.11](/posts/re-1-11-windows-internals-2-peb-teb-handles/)). Each record has two fields: a pointer to the next record, and a pointer to the handler function.

```asm
; x86: manually registering an SEH handler, the classic pattern
push offset my_handler   ; handler address
push fs:[0]              ; link to the old handler
mov  fs:[0], esp         ; make the new record the head of the chain
```

On x64 it's completely different: SEH no longer lives on the stack, it relies on a static table in the PE (the `.pdata` section, the exception directory structure). That's safer against handler-overwrite attacks, but for you it means looking up a table instead of reading a chain off the stack.

VEH (Vectored Exception Handling) is an add-on: the handler is registered through `AddVectoredExceptionHandler`, runs before SEH, and isn't tied to any function frame. Malware likes VEH because it covers the whole process.

### Why a reverser should care

Malware abuses SEH/VEH to hide control flow and to resist analysis in a few ways. One is steering the flow with deliberate faults. The code deliberately triggers an exception (for example writing to a null address, or running `int 3`), and the real logic is in the handler. Someone reading statically and following the straight-line flow will miss the handler, because on the surface it looks like dead code.

The other is debugger detection. When a debugger is attached, some exceptions (like the `int 3` breakpoint) get swallowed by the debugger and never reach the handler. The program registers a handler, throws an exception itself, then checks whether the handler ran. If it didn't, a debugger is poking around. Details of this trick are in [Lesson 15.3](https://github.com/Haind03/Technique-Reverse/tree/main/phan-15-anti-reverse).

When analyzing, if you see an `AddVectoredExceptionHandler` or a manual SEH registration pattern, put a breakpoint right at that handler function, because the logic you're after is probably in there and not in the main flow. In x64dbg, turn on the option to pass exceptions to the application instead of swallowing them, otherwise you'll never see the handler run.

## TLS callbacks, code that runs before main

Thread Local Storage (TLS) exists so each thread gets its own copy of a variable. But it comes with a feature that gets abused more than its original purpose: TLS callbacks, functions called automatically whenever a process or thread starts up and exits.

The key point is that TLS callbacks run before the program's entry point (`AddressOfEntryPoint`). So before the very first line of code you thought was the start, other code has already run.

For anti-debug this is a gift. The program stuffs a debugger check into a TLS callback. A beginner sets a breakpoint at the entry point and then runs it, and by the time that breakpoint hits, the TLS callback has long finished and already spotted you. You showed up late to the party.

The TLS callback lives in the PE's TLS Directory, which points to a null-terminated array of function pointers:

```
TLS Directory -> AddressOfCallBacks -> [callback1, callback2, ..., NULL]
```

To deal with it, open the TLS Directory in PE-bear or CFF Explorer to see whether there are any callbacks and where they point. In x64dbg, go to Options and enable breaking on "TLS Callbacks" (and also "System Breakpoint" and "Entry Breakpoint"). The debugger then stops right at the first callback, before the entry point, so you can read it before it gets a chance to probe you.

Not every TLS callback is malicious. Plenty of runtimes and libraries use it legitimately. But if you see a TLS callback in a suspicious file, always read it first.

## Native API and the syscall layer

This part clears up the whole path of a system call, and explains why tracing Win32 APIs sometimes still misses things.

Recall from [Lesson 1.10](/posts/re-1-10-windows-internals-1-win32-api-dlls/): kernel32 doesn't do the heavy lifting itself, it calls down into ntdll. The functions in ntdll have an `Nt` or `Zw` prefix (for example `NtCreateFile`, `NtAllocateVirtualMemory`), and this is the Native API layer, the closest to the kernel in user mode. The full chain:

```
Program
   -> CreateFileW        (kernel32.dll, Win32 layer)
      -> NtCreateFile    (ntdll.dll, Native API)
         -> syscall      (switch down to kernel mode)
            -> the kernel half of NtCreateFile
```

The `syscall` instruction (x64) works like this: put an identifying number (the system service number) into the `eax` register, then execute `syscall`, the CPU switches to kernel mode, and the kernel looks that number up in the service table (SSDT) to know which function to call.

A typical ntdll stub looks like this:

```asm
NtCreateFile:
    mov  r10, rcx          ; syscall calling convention
    mov  eax, 0x55         ; syscall number (example, varies by Windows version)
    syscall
    ret
```

Two things matter here for a reverser. First, syscall numbers are not fixed. The `0x55` above is only right for one specific Windows version. Microsoft changes these numbers between versions, even between updates. So don't memorize numbers, look them up for the Windows build you're analyzing (there are public lookup tables per build).

Second, direct syscalls are how malware dodges hooks. Many EDRs and monitoring tools install hooks at the start of the `Nt*` functions in ntdll (inline hooks, [Lesson 17.3](https://github.com/Haind03/Technique-Reverse/tree/main/phan-17-patch-hook-frida)) to catch every call. Malware counters by embedding `mov eax, <number>; syscall` straight into its own code, no longer going through ntdll, so the hook in ntdll never triggers. This is called a direct syscall, and variants like "indirect syscall" jump to the `syscall` instruction that already sits inside ntdll so it looks more natural.

To be clear, here we learn the mechanism so we can detect and analyze it, not so we can write it. When reversing, the tell is a `syscall` instruction in the code of the module you're analyzing (not in ntdll), or a snippet that loads a number into `eax` and then does `syscall` without going through an import. Then you know the program is trying to avoid the usual monitoring layer, and you have to move to observing at a lower level (kernel callbacks, ETW, or a hardware breakpoint on the syscall instruction itself).

Practical consequence: if you only hook or set breakpoints at the kernel32 level, a program that calls ntdll directly slips through. To be safe, set breakpoints at the `Nt*` layer in ntdll. And if even that misses, it's likely using direct syscalls.

## Key takeaways
SEH/VEH let code jump to a handler that the straight-line flow doesn't show, and malware throws exceptions on purpose to hide logic or probe for debuggers, so put a breakpoint at the handler and let the debugger pass the exception to the program. x86 keeps the SEH chain on the stack at `fs:[0]`, while x64 uses a static table in `.pdata`.

TLS callbacks run before the entry point, so always check the TLS Directory and enable breaking on TLS callbacks in x64dbg before running.

The call chain is Win32 (kernel32), then Native API (ntdll, `Nt`/`Zw`), then `syscall`, then the kernel. Syscall numbers change by Windows version, so look them up and don't memorize them. Direct syscalls are a way to dodge hooks in ntdll, and the tell is a `syscall` instruction inside the module's code, not via imports. When you hit one, move your observation down a level.
