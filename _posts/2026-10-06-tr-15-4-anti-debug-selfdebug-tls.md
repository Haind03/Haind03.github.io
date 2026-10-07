---
title: "Lesson 15.4: Advanced anti-debug, self-debug and TLS callbacks"
date: 2026-10-06 09:29:00 +0700
categories: ["Technique Reverse", "Part 15 · Anti-Reversing and Bypasses"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
The previous three lessons covered checks you run into midway through a program: asking an API, reading the PEB, measuring time. This one is nastier in a different way: it doesn't give you time to attach, or it takes the debugger's seat so you can't get in. This is the group of anti-debug where beginners often get "the program exits right as it starts and I have no idea why".

## Self-debugging: taking the debugger's seat

Windows has a simple rule that this whole family of techniques relies on: a process can only be attached to by exactly one debugger at a time. If the program sets up a debugger for itself, that slot is already taken, and your x64dbg will fail to attach.

There are two common variants. In the first, the program creates a child process and lets the child debug the parent: it calls `CreateProcess` on a copy of itself with a flag, and then the child calls `DebugActiveProcess` on the parent. From then on the parent already has a debugger (its own child), and you can't squeeze in. The second variant self-debugs through a separate thread, which is less common but similar in idea.

You can recognize it when reading statically: you see `CreateProcess` creating its own path, together with `DebugActiveProcess`, `WaitForDebugEvent`, `ContinueDebugEvent`. When you see a parent-child pair like this, you're looking at a self-debugger.

Don't try to attach to a process that's already taken. Instead, block the child-creation step right away (put a breakpoint at `CreateProcessW`, or patch it so it doesn't create the child), or analyze the logic in the child process to understand what it does and then neutralize the whole mechanism.

## Parent process check

A cheap but effective kind: the program asks itself "who spawned me?". When you run a file normally from Explorer, the parent is `explorer.exe`. When you run it from inside x64dbg, the parent is `x64dbg.exe`. From cmd it's `cmd.exe`.

The program gets the parent PID (through `NtQueryInformationProcess` with `ProcessBasicInformation`, then looks up the parent process name through `CreateToolhelp32Snapshot`) and compares it against a list of well-known debugger names. If it matches, it knows it's being watched.

You spot it by seeing name strings like "x64dbg", "ollydbg", "ida", "windbg" in the binary, along with code that enumerates processes. To get past it, run it from a "clean" parent, patch the name comparison, or use a plugin that hides the process name.

## Debug object

When a debugger attaches, the kernel creates a debug object tied to the debugged process. The program can ask about it through `NtQueryInformationProcess` with the information class `ProcessDebugObjectHandle` (value 0x1E): if it returns a non-null handle, a debug object exists, meaning it's being debugged. This is one of the hardest checks to fake because it asks the kernel directly about the real state.

The practical way to handle it is ScyllaHide/TitanHide (lesson 15.9), which hook exactly this spot to give a fake answer. By hand, set a breakpoint at `NtQueryInformationProcess`, and when `ProcessInformationClass == 0x1E` change the return value to 0.

## Thread hiding, in more depth

Lesson 15.1 mentioned `NtSetInformationThread(ThreadHideFromDebugger)`. What it means deserves a closer look: when a thread gets the `ThreadHideFromDebugger` flag (value 0x11), the kernel stops sending that thread's debug events to the debugger. As a result, breakpoints and exceptions in that thread are no longer reported to the debugger, and the program runs right past you.

Usually the program sets this flag for the main thread and only then runs the sensitive part. The sign is a call to `NtSetInformationThread` where the information class parameter is 0x11 and the thread handle is `(HANDLE)-2` (the pseudo-handle of the current thread). To get past it, patch that call into a no-op, or let ScyllaHide block it.

## TLS callbacks: running before main

This is where beginners get trapped the most. As lesson 1.12 said, TLS callbacks are functions the PE loader calls before the entry point runs. The sequence is: the loader maps the image, calls the TLS callbacks, and only then jumps to the entry point.

Whoever writes the anti-debug takes advantage of this by putting the check right in the TLS callback. When you open the file in a debugger and hit run, the debugger usually stops first at the entry point (or the system breakpoint). But the TLS callback has already finished running before that. It means that by the time you get to see anything, the program may already have detected the debugger and decided to exit, or quietly switched to another branch.

An illustration of the flow:

```
PE loader maps the image into memory
   |
   v
calls TLS callback 1  <-- anti-debug lives here, runs BEFORE you can look
   |
   v
calls TLS callback 2 (if any)
   |
   v
jumps to the entry point  <-- the debugger usually only stops here, too late
   |
   v
the author's main()
```

To handle it, go to Options > Preferences > Events in x64dbg and turn on the option to stop at TLS Callbacks (and System Breakpoint, Entry Breakpoint). Then the debugger stops right when the first TLS callback is about to run, and you have time to set breakpoints and look. You can also find the TLS callbacks statically first: open the file in PE-bear or CFF Explorer, look at the TLS Directory, and get the callback addresses, then set breakpoints there in advance in IDA/Ghidra. If the callback only does one thing, check and exit, patch it to return early.

Pocket rule: if a program "dies right after starting" in a debugger before the entry point is even reached, suspect a TLS callback immediately.

## Looking at a TLS callback

A TLS callback has the fixed signature `VOID NTAPI cb(PVOID DllHandle, DWORD Reason, PVOID Reserved)`. In a binary it usually looks like a small function, called by the PE loader with `Reason == DLL_PROCESS_ATTACH` (value 1) at startup:

```asm
tls_callback:
    cmp  edx, 1            ; Reason == DLL_PROCESS_ATTACH ?
    jne  short done        ; only runs on process attach
    ; read PEB.BeingDebugged via gs:[0x60]
    mov  rax, gs:[60h]
    movzx eax, byte ptr [rax+2]
    test eax, eax
    je   short done        ; not debugged, return
    ; being debugged: exit or branch to a fake path
    xor  ecx, ecx
    call ExitProcess
done:
    ret
```

You can read it right away: this callback checks `BeingDebugged`, and if it sees a debugger it calls `ExitProcess`. And since it runs before main, you have to catch it from the TLS callback breakpoint, you can't wait until main.

## Lab

See `labs/15.4/`. You build a program that puts its anti-debug in a TLS callback, run it in x64dbg the first time (without the TLS breakpoint on) to see it exit mysteriously, then turn on the option to stop at TLS callbacks and catch the exact check, and finally patch it to get past.

## Common pitfalls

If the entry point hasn't been reached and the program has already exited, it's almost certainly a TLS callback, so don't blame a broken debugger. A failed attach isn't always an error either, since self-debugging may have taken the slot. And if you disable one check (for example BeingDebugged) and it still dies, remember other checks run earlier, especially in TLS.

## Key takeaways
A process only has one debugger, so self-debugging takes the slot and you can't attach. Block it at the child-creation step. A parent process check compares the parent's name against a list of debuggers, so patch it or run from a clean parent.

`ProcessDebugObjectHandle` (0x1E) asks the kernel about the debug object and is very hard to fake, so use ScyllaHide. `ThreadHideFromDebugger` (0x11) makes the kernel stop sending debug events, so patch it to a no-op or use ScyllaHide.

TLS callbacks run before the entry point. Turn on stopping at TLS Callbacks in x64dbg and find the TLS Directory in PE-bear. If the program dies before main, suspect TLS right away.
