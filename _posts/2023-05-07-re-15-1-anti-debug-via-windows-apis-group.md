---
title: "Lesson 15.1: Anti-debug via Windows APIs, the group you meet most"
date: 2023-05-07 09:13:00 +0700
categories: ["Technique Reverse", "Part 15 · Anti-Reversing and Bypasses"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
When a program doesn't want you to attach a debugger to it, the first thing it usually tries is asking the OS directly: "hey, is my process being debugged?". Windows has a few APIs that answer exactly that question, and this is also the first anti-debug group you meet. Luckily it's also the easiest to get past, because wherever it asks, there's a return value there for you to change.

This lesson looks at anti-debug from the analyst's side: understanding the mechanism so you can recognize it in code and get past it, not to write anti-analysis software. Understanding how to break a layer of protection is also understanding how it protects.

## General principle: wherever it asks, you can change it

Every check in this lesson follows the same mold: call an API, get the result, compare, then branch (exit, run wrong, or pretend everything is normal). Once you've located that API call, three ways to get past it always work. You can set a breakpoint right after the API returns and change the value in rax (or the variable holding the result) to the "not being debugged" value. You can patch the branch, changing `jne` to `jmp` or nopping it out. Or you can use a plugin like ScyllaHide or TitanHide to automatically lie in answer to all of these APIs, so you don't do each by hand.

Keep this principle in mind, and the rest is just recognizing each API.

## IsDebuggerPresent

The simplest. This API reads a flag in the PEB (Process Environment Block, see [Lesson 1.11](/posts/re-1-11-windows-internals-2-peb-teb-handles/)) called BeingDebugged and returns 1 if being debugged.

In code you'll see something like:

```asm
call    IsDebuggerPresent
test    eax, eax
jnz     debugger_found        ; eax != 0 means being debugged
```

To bypass it, set a breakpoint at `IsDebuggerPresent`, run until it returns, and set `eax = 0`. Or faster, patch `jnz` to nop. Since it only reads one byte in the PEB, you can also just set BeingDebugged in memory to 0 directly and be done for the whole process permanently.

## CheckRemoteDebuggerPresent

A relative of the one above but it asks about a process (including itself) through a handle. It writes the result into a pointer variable passed in instead of returning it through rax:

```c
BOOL present = FALSE;
CheckRemoteDebuggerPresent(GetCurrentProcess(), &present);
if (present) exit(1);
```

To bypass it, put a breakpoint after the call and change the value at the address of `present` (the second parameter, on Win64 what rdx points to) to 0.

## NtQueryInformationProcess

This is the workhorse of anti-debug APIs. This native function in ntdll takes an information code and returns all sorts of things about the process. Three codes often get abused. ProcessDebugPort (0x07) returns a nonzero value (the debug port) if being debugged, and the program checks for nonzero and knows. ProcessDebugFlags (0x1F) returns 0 when being debugged, which is backwards, because the "no debug inherit" flag is turned off. ProcessDebugObjectHandle (0x1E) returns a nonzero handle if a debug object is attached.

To recognize it in code, look for the `NtQueryInformationProcess` call and watch the second parameter (the constant 7, 0x1E or 0x1F) to know what it's probing. IsDebuggerPresent only reads the PEB so it's easy to fool, while NtQueryInformationProcess asks the kernel directly so it's more "real", and patching the PEB byte doesn't work on it.

To bypass it, put a breakpoint after the call and change the result buffer (ProcessDebugPort to 0, ProcessDebugObjectHandle to 0, ProcessDebugFlags to 1). Or let ScyllaHide hook it in advance.

## NtSetInformationThread (ThreadHideFromDebugger)

This one has a different nature: it's not for detecting but for hiding. Calling `NtSetInformationThread` with the code ThreadHideFromDebugger (0x11) makes the thread stop sending debug events to the debugger, so the debugger is "blind" to that thread, and breakpoints sometimes don't stop.

You recognize it by a `NtSetInformationThread` call with the parameter 0x11. To bypass it, nop that call out, or let ScyllaHide block it.

## OutputDebugString

An old trick: call `OutputDebugString` and watch the behavior. On older Windows, when there's no debugger, this function sets an error (GetLastError nonzero); when a debugger catches the string it doesn't. The usage is outdated but you still see it in old samples. Recognize it by an OutputDebugString + GetLastError pair right next to each other.

## CloseHandle with a junk handle

When the process is being debugged, calling `CloseHandle` (or NtClose) with an invalid handle throws an EXCEPTION_INVALID_HANDLE exception; when not being debugged it just quietly returns an error. The program wraps the call in try/except, and if it catches the exception it knows there's a debugger.

You recognize it by `CloseHandle` with an odd handle value (like 0x1234) inside an SEH block. To bypass it, swallow the exception, or patch the handling branch.

## Lab

The folder `labs/15.1/` has `antidebug.c` bundling a few of the checks above into a program that prints "clean" or "debugger detected". Build and run it normally and see it report clean. Then run it under x64dbg and see which check it reports detected on. Bypass each check by changing the return value, then try again with ScyllaHide to be quicker.

Instructions and the solution are in `labs/15.1/README.md` and `solution.md`.

## Key takeaways
Every anti-debug API follows the same mold: call the API, compare the result, branch. Locate the API and you can bypass it. IsDebuggerPresent and CheckRemoteDebuggerPresent only read the PEB, so they're easy to get past (change eax or the BeingDebugged byte).

NtQueryInformationProcess asks the kernel directly (ProcessDebugPort 0x07, DebugFlags 0x1F, DebugObjectHandle 0x1E), so it's stronger and you have to change the result buffer. NtSetInformationThread + 0x11 is for hiding from the debugger, not detecting. The lazy but effective way is ScyllaHide, which lies in answer to this whole group of APIs for you.

## Common pitfalls
Patching the BeingDebugged byte in the PEB doesn't get past NtQueryInformationProcess, because it asks the kernel and doesn't read the PEB. A program also usually has many checks scattered around, so getting past one doesn't mean you're done. Use ScyllaHide to sweep them out first and then look at what remains.
