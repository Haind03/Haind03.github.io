---
title: "Lesson 15.9: Bypassing anti-debug, from a mouse click to a kernel driver"
date: 2026-10-06 09:34:00 +0700
categories: ["Technique Reverse", "Part 15 · Anti-Reversing and Bypasses"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
The previous four lessons (15.1 to 15.4) showed you all kinds of anti-debug: asking an API, reading the PEB, measuring time, setting traps, hiding in a TLS callback. If you had to patch each one by hand, a malware sample with twenty checks would eat your whole afternoon. This lesson is good news: most of that work has already been packaged into plugins by someone, and you just turn them on. And when the plugin isn't enough, there's a handful of tidy manual techniques to fill in.

First the general principle: almost every anti-debug check boils down to one question, "am I being watched", answered by reading a flag, a value, or a system behavior. Bypassing it isn't about deleting the question, it's about answering falsely: making every source of information say "there's no debugger at all". The tools below do exactly that lying, differing in which layer they lie at.

## ScyllaHide: the first line of defense, in user-mode

ScyllaHide is a plugin for x64dbg (and IDA, OllyDbg too). It hooks the functions in ntdll inside the process you're debugging, then adjusts return values and flags so every user-mode check misses. Turn it on once and it handles a whole batch of things you've already learned:

It forces `IsDebuggerPresent` and `PEB.BeingDebugged` to 0, and clears the flags in `PEB.NtGlobalFlag` and the heap flags that expose the debugger (lesson 15.2). For `NtQueryInformationProcess` with ProcessDebugPort/DebugFlags/DebugObjectHandle it returns the values of a clean process (lesson 15.1). It swallows `NtSetInformationThread` with ThreadHideFromDebugger so your thread doesn't hide itself (lesson 15.4). It also covers `NtQueryObject`, `NtClose` (the CloseHandle trap), `OutputDebugString`, and timing via `NtQuerySystemTime`/`GetTickCount`.

How to use it in x64dbg: install the plugin in the `plugins` folder, open the ScyllaHide menu, pick a profile (usually start with the default "x64dbg" profile, which already has most options on), apply, then run again. Most ordinary crackmes and malware will stop yelling "debugger detected" right here.

A practical tip: don't blindly turn on every option. A few options rarely change the program's behavior. If you turn everything on and the app crashes, turn off the groups you're unsure about, then turn them back on one group at a time until it both gets past the check and runs fine.

## TitanHide: when the check looks down into the kernel

ScyllaHide lives in user-mode, so it can only fix what goes through that process's ntdll. Some checks look deeper, for example calling straight down into the kernel or checking debug state at the OS object level, which user-mode hooks don't reach. That's when you need TitanHide.

TitanHide is a kernel-mode driver. It intercepts system services (like NtQueryInformationProcess) inside the kernel, before the result gets back up to user-mode, so it gets past even the checks ScyllaHide can't. Because it's a driver, it needs admin rights and needs Driver Signature Enforcement turned off or handled (usually run in a test VM with test-signing on). In practice the two tools complement each other: many people turn on ScyllaHide first and only pull out TitanHide when they meet a stubborn check.

## HyperHide: the deepest layer

When even the driver gets detected (some protectors check for the presence of TitanHide), HyperHide pushes the lying down to the hypervisor level, using hardware virtualization to interfere so that neither the process nor the kernel sees the usual hook traces. This is a level you rarely need, only when you hit a hard commercial protector. Just know it exists to pull out when ScyllaHide and TitanHide both lose.

There's also SharpOD, another anti-anti-debug plugin that used to be very popular for OllyDbg and x64dbg, with the same principle as ScyllaHide. Keep it in the toolbox as a plan B.

## Four levels, pick the right one

Don't jump straight down to the hypervisor for a crackme. A reasonable ladder:

| Level | Tool | Use when |
|---|---|---|
| User-mode | ScyllaHide, SharpOD | Default, try first, gets past most |
| Kernel-mode | TitanHide | The check calls straight into the kernel or ScyllaHide doesn't get past it |
| Hypervisor | HyperHide | The protector detects even the driver |
| Manual | x64dbg script, hardware BP | A weird check no tool covers, or you want to understand it properly |

## Manual techniques, when plugins aren't enough

Plugins cover the common checks. For a strange home-made check you handle it yourself, and these three tips are enough for most situations.

The first is a conditional breakpoint that fixes the value itself. Instead of stopping and fixing by hand each time, set a conditional breakpoint with a command in x64dbg. For example, to make `IsDebuggerPresent` always return 0, set a breakpoint right after the call and have it set `rax = 0` and continue by itself, with no stop. In the Command box or the Breakpoints tab, x64dbg lets you attach an expression that runs on every hit, like:

```
bp IsDebuggerPresent
SetBreakpointCommand IsDebuggerPresent, "ret; mov rax,0"
```

(the exact syntax depends on the version, the idea is: on a hit, fix the return value yourself and continue). This turns an annoying check invisible without patching the file.

The second is using hardware breakpoints instead of software breakpoints. A debugger's software breakpoint works by overwriting the first byte of the instruction with `0xCC` (INT 3). Anti-debug code can scan the code section for stray `0xCC` bytes to detect that you set a breakpoint (lesson 15.3). A hardware breakpoint is different: it uses the CPU's debug registers DR0 to DR3, modifies no code bytes at all, so a `0xCC` scan sees nothing. Downside: only 4 slots, and there's a separate check that reads DR through GetThreadContext (ScyllaHide can fake this part too). When you suspect the binary scans for `0xCC`, switch to hardware breakpoints.

The third is targeted patching. Once you've located the exact branch of the check (the `cmp`/`je` pair leading to the "detected" branch), sometimes the tidiest thing is to NOP the jump or flip the condition right there, as lesson 17.1 will cover in detail. Use it when you want a permanent patch instead of having to turn on a plugin every time.

Rule of thumb: turn on ScyllaHide first to clean 90%, look at which checks still fire for the rest, then handle each with a conditional breakpoint or a patch. You rarely have to climb to the kernel for learning purposes.

## Key takeaways
Bypassing anti-debug means making every source of information answer "no debugger", not deleting the check. ScyllaHide (user-mode) is the first line, and its default profile gets past most checks from lessons 15.1 to 15.4. TitanHide (kernel driver) handles checks that look down into the kernel, and HyperHide (hypervisor) is for protectors that detect even the driver.

Hardware breakpoints (DR0-DR3) don't write `0xCC` into the code, so they dodge breakpoint-scanning checks. A conditional breakpoint that fixes the return value neutralizes a weird check without patching the file. Climb the layers from low to high, user-mode first, kernel next, hypervisor last, and don't use a cleaver to kill a chicken.
