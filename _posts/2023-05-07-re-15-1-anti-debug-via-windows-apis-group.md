---
title: "Lesson 15.1: Anti-debug via Windows APIs"
image:
  path: /assets/img/covers/re-15-1-anti-debug-via-windows-apis-group.webp
  alt: "Lesson 15.1: Anti-debug via Windows APIs"
date: 2022-07-14 12:56:00 +0700
categories: ["Reverse Engineering", "Part 15 · Anti-Reversing and Bypasses"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
When a program doesn't want a debugger attached, the first thing it usually tries is asking the OS directly whether it is being debugged. Windows has a few APIs that answer exactly that, and this is the first anti-debug group you'll meet. It's also the easiest to get past, because wherever it asks, there's a return value you can change.

![Anti-debug API check and three bypasses](/assets/img/re/re-15-1-anti-debug-via-windows-apis-group.svg)
_Each check is call, result, compare, branch, and any of the three steps can be changed._

This lesson looks at anti-debug from the analyst's side, meaning understanding the mechanism so you can recognize it in code and get past it, not so you can write anti-analysis software.

## General principle: wherever it asks, you can change it

Every check in this lesson follows the same pattern, which is to call an API, get the result, compare, then branch (exit, run wrong, or pretend everything is normal). Once you've found that API call, three ways to get past it always work. You can set a breakpoint right after the API returns and change the value in rax (or the variable holding the result) to the "not being debugged" value. You can patch the branch, changing `jne` to `jmp` or nopping it out. Or you can use a plugin like ScyllaHide or TitanHide to lie automatically in answer to all of these APIs, so you don't do each by hand.

Keep this in mind and the rest is just recognizing each API.

## IsDebuggerPresent

The simplest. This API reads a flag in the PEB (Process Environment Block, see [Lesson 1.11](/posts/re-1-11-windows-internals-2-peb-teb-handles/)) called BeingDebugged and returns 1 if being debugged.

In code you'll see something like:

```asm
call    IsDebuggerPresent
test    eax, eax
jnz     debugger_found        ; eax != 0 means being debugged
```

To bypass it, set a breakpoint at `IsDebuggerPresent`, run until it returns, and set `eax = 0`. Or faster, patch `jnz` to nop. Since it only reads one byte in the PEB, you can also set BeingDebugged in memory to 0 and that covers the whole process.

## CheckRemoteDebuggerPresent

A relative of the one above, but it asks about a process (including itself) through a handle. It writes the result into a pointer variable passed in, instead of returning it through rax:

```c
BOOL present = FALSE;
CheckRemoteDebuggerPresent(GetCurrentProcess(), &present);
if (present) exit(1);
```

To bypass it, put a breakpoint after the call and change the value at the address of `present` (the second parameter, on Win64 what rdx points to) to 0.

## NtQueryInformationProcess

This is the workhorse of anti-debug APIs. This native function in ntdll takes an information code and returns all sorts of things about the process. Three codes get abused often. ProcessDebugPort (0x07) returns a nonzero value (the debug port) if being debugged, and the program checks for nonzero. ProcessDebugFlags (0x1F) returns 0 when being debugged, which is backwards, because the "no debug inherit" flag is turned off. ProcessDebugObjectHandle (0x1E) returns a nonzero handle if a debug object is attached.

To recognize it in code, look for the `NtQueryInformationProcess` call and watch the second parameter (the constant 7, 0x1E or 0x1F) to see what it's probing. IsDebuggerPresent only reads the PEB so it's easy to fool, while NtQueryInformationProcess asks the kernel directly, so patching the PEB byte doesn't work on it.

To bypass it, put a breakpoint after the call and change the result buffer (ProcessDebugPort to 0, ProcessDebugObjectHandle to 0, ProcessDebugFlags to 1). Or let ScyllaHide hook it in advance.

## NtSetInformationThread (ThreadHideFromDebugger)

This one is different, since it's not for detecting but for hiding. Calling `NtSetInformationThread` with the code ThreadHideFromDebugger (0x11) makes the thread stop sending debug events to the debugger, so the debugger is blind to that thread, and breakpoints sometimes don't stop.

You recognize it by a `NtSetInformationThread` call with the parameter 0x11. To bypass it, nop that call out, or let ScyllaHide block it.

## OutputDebugString

An old trick is to call `OutputDebugString` and watch the behavior. On older Windows, when there's no debugger, this function sets an error (GetLastError nonzero), and when a debugger catches the string it doesn't. It's outdated but you still see it in old samples. Recognize it by an OutputDebugString + GetLastError pair right next to each other.

## CloseHandle with a junk handle

When the process is being debugged, calling `CloseHandle` (or NtClose) with an invalid handle throws an EXCEPTION_INVALID_HANDLE exception. When not being debugged it just quietly returns an error. The program wraps the call in try/except, and if it catches the exception it knows there's a debugger.

You recognize it by `CloseHandle` with an odd handle value (like 0x1234) inside an SEH block. To bypass it, swallow the exception, or patch the handling branch.

## Lab

The goal is to train your eye to recognize Windows API based anti-debug checks in a binary and get past them while analyzing it. This is a defensive and analytical skill, meant for your own binaries or for learning samples inside an isolated lab (see Lesson 0.3).

There's no bundled binary for this one, so pick one of two ways to get a target. The closest to real practice is to grab a crackme with anti-debug from crackmes.one, filtered by the "anti-debug" tag, picking something at level 1 or 2. Alternatively, build a minimal target yourself, which is a small Windows program that calls `IsDebuggerPresent` and prints the result, just a few lines around that call, enough to have a spot to set a breakpoint and watch the return value. You only need one observable check, not a whole anti-analysis suite.

Start by triaging it. Open the binary in Detect It Easy, then look at the Imports table in IDA or Ghidra for suspicious APIs, such as `IsDebuggerPresent`, `CheckRemoteDebuggerPresent`, `NtQueryInformationProcess`, `NtSetInformationThread`, `OutputDebugStringA/W`. Their presence is the first sign. For each one, use cross-reference (the X key in IDA) to jump to where it's called, and read the code right after the call for a `test`/`cmp` plus a jump that decides "debugged or not".

Then observe it under a debugger. Open the binary in x64dbg and set a breakpoint on each API (`bp IsDebuggerPresent`, `bp NtQueryInformationProcess`, and so on). Run it, and once it stops, use "Execute till return" (Ctrl+F9) to get to where the API returns and look at the value in rax or in the result buffer.

Bypass each check using one of three approaches. You can change the return value right at the breakpoint, patch the branch (turning `jne` into `jmp`, or nopping it out), or enable the ScyllaHide plugin and run again to let it handle everything automatically. Afterward, compare the effort, meaning how long it took to handle each check by hand versus flipping on ScyllaHide once, and work out when each approach makes sense.

Two questions to think about. Why does patching the BeingDebugged byte in the PEB defeat `IsDebuggerPresent` but not `NtQueryInformationProcess` with ProcessDebugPort? And if a program calls the same check from five different places, which bypass approach is the least tedious?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Try it yourself before reading this.

The x64dbg and ScyllaHide steps below describe the standard procedure, and the details differ from binary to binary. The identification part, through Imports and cross-references, applies on any disassembler.

Identifying and scoping the checks. In the Imports table, the presence of these APIs is telling:

| API | Usually used for |
|---|---|
| IsDebuggerPresent | reading the BeingDebugged flag in the PEB |
| CheckRemoteDebuggerPresent | asking about debugging through a process handle |
| NtQueryInformationProcess | asking the kernel directly: DebugPort / DebugFlags / DebugObjectHandle |
| NtSetInformationThread | ThreadHideFromDebugger (hiding) |
| OutputDebugStringA/W | an old trick based on GetLastError |

Cross-referencing to each call, the code right after it usually looks like this:

```asm
call    IsDebuggerPresent
test    eax, eax
jnz     bad          ; jump if being debugged
```

The `jnz`/`jne` leading to the "detected" branch is what you need to handle.

Observing under the debugger. In x64dbg's Command box:

```
bp IsDebuggerPresent
bp NtQueryInformationProcess
```

Run it (F9). Once it stops at the API, press Ctrl+F9 to run to the `ret`, then look at the result. For `IsDebuggerPresent`, check the value in `eax` (1 means detected), and for `NtQueryInformationProcess`, check the buffer at the third argument (on Win64, pointed to by r8), reading the DebugPort or DebugObjectHandle value after it returns.

Bypassing each check. Three approaches, picked based on the situation. You can fix the result in place. After the API returns, set `eax = 0` for IsDebuggerPresent, or write 0 into the DebugPort/DebugObjectHandle buffer, or write 1 into DebugFlags, so the program thinks there's no debugger. You can patch the branch instead. At `jnz bad`, change it to a nop (or a jump to the good branch), which is the right choice when you want the fix to be permanent on the file (Ctrl+P saves the patch). Or you can use ScyllaHide. Install the plugin, enable the matching options (hooking IsDebuggerPresent, NtQueryInformationProcess, and so on), and it answers all of these APIs with a lie automatically, so you don't have to handle each one by hand.

Comparing the effort, handling each check by hand makes sense when there are only one or two spots and you want to understand them well. When a binary scatters checks everywhere, ScyllaHide saves a lot of time.

Why does patching the PEB defeat IsDebuggerPresent but not NtQueryInformationProcess? `IsDebuggerPresent` only reads the BeingDebugged byte in the process's PEB, a user-mode region, so changing that byte fools it. `NtQueryInformationProcess` with ProcessDebugPort is a syscall that asks the kernel directly for the process's real debug port, it doesn't read the PEB at all, so the PEB byte you changed has no effect on it. You have to fix the result buffer of that specific call instead, or hook at the ntdll level (ScyllaHide/TitanHide).

What about a check repeated in five places? ScyllaHide (user-mode) or TitanHide (kernel-mode) is the least tedious option, because they hook at the source (the API or syscall), so every call site gets fooled at once instead of you patching five separate branches.

</details>

## Key takeaways
Every anti-debug API follows the same pattern, which is to call the API, compare the result and branch. Find the API and you can bypass it. IsDebuggerPresent and CheckRemoteDebuggerPresent only read the PEB, so they're easy to get past (change eax or the BeingDebugged byte).

NtQueryInformationProcess asks the kernel directly (ProcessDebugPort 0x07, DebugFlags 0x1F, DebugObjectHandle 0x1E), so it's harder and you have to change the result buffer. NtSetInformationThread + 0x11 is for hiding from the debugger, not detecting. The lazy but effective way is ScyllaHide, which lies in answer to this whole group of APIs for you.

## Common pitfalls
Patching the BeingDebugged byte in the PEB doesn't get past NtQueryInformationProcess, because it asks the kernel and doesn't read the PEB. A program also usually has many checks scattered around, so getting past one doesn't mean you're done. Use ScyllaHide to sweep them out first and then look at what remains.
