---
title: "Lesson 15.9: Bypassing anti-debug, from a mouse click to a kernel driver"
image:
  path: /assets/img/covers/re-15-9-bypassing-anti-debug-from-mouse-click.webp
  alt: "Lesson 15.9: Bypassing anti-debug, from a mouse click to a kernel driver"
date: 2023-06-22 20:40:00 +0700
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

## Lab

This lab has no source code of its own. It reuses the anti-debug programs you built in the earlier labs of this part: the one from Lesson 15.1 (anti-debug through APIs such as IsDebuggerPresent and NtQueryInformationProcess), the one from Lesson 15.2 (reading PEB.BeingDebugged and NtGlobalFlag directly) and the one from Lesson 15.3 (RDTSC timing and the trap). The goal is to use ScyllaHide to get past many checks at once instead of patching each one by hand, and then to deal with one leftover check yourself using a conditional breakpoint.

You need Windows, x64dbg, and the ScyllaHide plugin (copied into the x64dbg `plugins` folder), plus the anti-debug programs from those three labs.

Start by opening the Lesson 15.1 program in x64dbg and running it normally, without ScyllaHide. Confirm that it prints "debugger detected" (or exits early) and note which check fired. Then turn on ScyllaHide through Plugins > ScyllaHide, choose the default profile for x64dbg, tick the groups (IsDebuggerPresent, PEB, NtQueryInformationProcess, NtSetInformationThread) and apply. Run again and see that the program now behaves as if there were no debugger. Match each check from Lessons 15.1 and 15.2 to the corresponding ScyllaHide option.

Repeat with the Lesson 15.2 program (direct PEB access) and the Lesson 15.3 program (timing). Write down which ones ScyllaHide gets past immediately and which need extra options. Timing usually needs the time group turned on.

Next pick one check and deliberately turn off its ScyllaHide option, pretending the plugin does not cover it. Get past it yourself with a conditional breakpoint: put a breakpoint at the check function, attach a command that fixes the return value (for example forcing `rax = 0` after `IsDebuggerPresent`), and let it continue by itself. Confirm that the program passes the check. Finally set a hardware breakpoint (right-click > Breakpoint > Hardware) instead of a software breakpoint at a function, and explain why this avoids a check that scans for the byte `0xCC`.

Two questions to think about. Why is ScyllaHide (user-mode) not enough for every binary, and when should you think of TitanHide? And how does a self-fixing conditional breakpoint differ from patching the file directly, and which situation suits each?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The procedure below describes the standard steps on x64dbg with ScyllaHide. The exact options differ a little between ScyllaHide versions.

To confirm detection, run the Lesson 15.1 program under x64dbg with nothing turned on. The program calls `IsDebuggerPresent` (and other checks), sees the debugger and prints the detection message. This is the "before" state to compare against.

After you apply the default profile, ScyllaHide hooks ntdll inside the process and forces values. `IsDebuggerPresent` reads `PEB.BeingDebugged`, and ScyllaHide keeps that byte at 0, so it returns 0. `NtQueryInformationProcess(ProcessDebugPort)` returns 0 instead of a non-zero value. `NtQueryInformationProcess(ProcessDebugFlags)` returns 1 (meaning "no debug"). `NtSetInformationThread(ThreadHideFromDebugger)` is swallowed, so the thread does not hide itself. Run again and the program takes the "no debugger" branch. Every check from Lessons 15.1 and 15.2 has a corresponding option box in ScyllaHide.

For direct PEB access and timing, the Lesson 15.2 program reads `gs:[0x60]` straight to get the PEB and then checks BeingDebugged and NtGlobalFlag. ScyllaHide keeps these fields clean in the PEB memory itself, so a direct read still sees clean values and it gets through. The Lesson 15.3 program measures time with RDTSC, which is the place that often needs extra tuning: turn on the option group related to time (ScyllaHide intervenes in the system's time functions). Note that RDTSC is a direct CPU instruction, and ScyllaHide cannot intercept a pure CPU instruction as easily as an API. So for timing based on bare RDTSC, the sure way is to patch the branch that compares the delta, or to run through the measured section without single-stepping (use run-to after the measured section rather than stepping instruction by instruction).

For the self-fixing conditional breakpoint, suppose you turn off ScyllaHide's IsDebuggerPresent option to handle it yourself. In x64dbg, first run `bp IsDebuggerPresent` (or put the breakpoint right after the call, at the instruction that uses the result in `rax` or `eax`). Then attach a command that runs when the breakpoint hits, to force the result to 0 and continue. For example, put the breakpoint at the `test eax, eax` right after the call and give it the command `eax=0` with the "do not pause" option. As a result, every time the program asks whether there is a debugger, it always receives 0 and takes the clean branch, and you never have to click anything by hand.

A hardware breakpoint avoids the `0xCC` scan because a software breakpoint overwrites the first byte of an instruction with `0xCC` (INT 3). If the binary scans its own code section for stray `0xCC` bytes, it can detect your breakpoint. A hardware breakpoint uses the CPU's debug registers DR0 to DR3 and the hardware's address matching, and does not modify a single byte of code, so the `0xCC` scan sees nothing unusual. The limits are that there are only 4 slots, and that some checks read the DR registers through GetThreadContext (ScyllaHide can fake that part).

As for when ScyllaHide is not enough and TitanHide is needed, ScyllaHide hooks in user mode, inside the ntdll of the process. A check that calls straight down into the kernel, or that checks the debug state at the level of an operating system object, is not touched by a user-mode hook, and then you need TitanHide, a kernel-mode driver that intercepts it inside the kernel.

As for conditional breakpoint versus patching the file, a conditional breakpoint lives only in the debug session and does not touch the file on disk, which is flexible while probing and trying things quickly. A file patch creates a permanent fix that runs independently outside the debugger, which suits the moment when you understand things well and want a reusable artifact. While analyzing, use the breakpoint, and when you are done and need a runnable copy, patch.

</details>

## Key takeaways
Bypassing anti-debug means making every source of information answer "no debugger", not deleting the check. ScyllaHide (user-mode) is the first line, and its default profile gets past most checks from lessons 15.1 to 15.4. TitanHide (kernel driver) handles checks that look down into the kernel, and HyperHide (hypervisor) is for protectors that detect even the driver.

Hardware breakpoints (DR0-DR3) don't write `0xCC` into the code, so they dodge breakpoint-scanning checks. A conditional breakpoint that fixes the return value neutralizes a weird check without patching the file. Climb the layers from low to high, user-mode first, kernel next, hypervisor last, and don't use a cleaver to kill a chicken.
