---
title: "Lesson 17.7: Dynamic Binary Instrumentation, letting the binary tell you where it ran"
date: 2026-10-06 09:46:00 +0700
categories: ["Technique Reverse", "Part 17 · Patching, Hooking, Injection"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
A debugger lets you stop and inspect point by point. Frida lets you hook a few functions. But when you want to ask something like "in this run, exactly which instructions did the program execute", or "where does the flow differ between a wrong input and a right one", both fall short. That's when you need Dynamic Binary Instrumentation (DBI).

## What DBI is

DBI is a technique of inserting analysis code (instrumentation) into a binary's execution flow while it runs, with no source code and without modifying the file on disk. A DBI tool reads each basic block about to run, re-translates it together with your observation snippets, and only then lets the CPU run the instrumented version.

In other words, you write something like "every time an instruction runs, add one to a counter", or "every time memory is written, record the address", and the DBI tool attaches that snippet to every instruction/every write of the target program. The program has no idea it's being observed at this level.

How it differs from the tools you've learned:

| Tool | Level of intervention | Good for |
|---|---|---|
| Debugger (x64dbg) | stops at breakpoints, manual | a deep look at one point |
| Frida ([Lesson 17.2](/posts/tr-17-2-frida-toan-tap/)) | function-level hooks | reading/changing parameters, observing APIs |
| DBI (Pin, DynamoRIO...) | per instruction/block, whole program | coverage, wide traces, taint |

DBI is heavier than Frida (it runs much slower because it re-translates every block) but far more detailed: it sees every instruction, not just function boundaries.

## Four tools people use

- **Intel Pin.** Long established, powerful, free (not open source). You write a pintool in C++, registering callbacks for each instruction (INS), each block (BBL), each loaded image (IMG). Used a lot for instruction counting, memory traces, and taint analysis.
- **DynamoRIO.** Open source, client architecture, compact API. It comes with sample tools like drcov (collects coverage) and drltrace (traces library calls). Many people like it because it's open and faster than Pin for some tasks.
- **QBDI** (QuarksLab). A DBI you can embed in other programs, with nice Python and C++ APIs, good for writing quick analysis scripts instead of building a whole pintool.
- **TinyInst.** Lightweight, leaning toward coverage for fuzzing, it doesn't re-translate everything like Pin/DynamoRIO but only instruments where needed, so it's fast and stable on large binaries on Windows/macOS.

Beginners should start with a ready-made tool (DynamoRIO's drcov) before writing their own pintool.

## The most valuable use: coverage diffing

This is the trick that makes DBI worth learning. The idea is very simple but powerful:

1. Run the program with a **wrong** input, collect the set of basic blocks executed (coverage A).
2. Run again with a **nearly right** or **right** input, collect coverage B.
3. Compare. The blocks that appear only in B and not in A are the code that runs when you go deeper into the check logic.

For a crackme, this marks out the serial check function without having to understand anything beforehand: you let the program itself show you where it branches when the input gets better. Combining coverage with fuzzing is the foundation of modern fuzzing (AFL uses this very coverage idea to guide itself).

Other uses:

- **Instruction count / execution trace.** Understand what an obfuscated function does by looking at the sequence of instructions that actually run, ignoring junk code that never executes (useful against anti-disassembly in [Lesson 15.6](/posts/tr-15-6-anti-disassembly/)).
- **Memory trace.** Record every memory read/write to follow where a value goes.
- **Taint analysis.** Mark the input as "tainted" then track it spreading through registers and memory cells, to see which decisions the input affects.

## DBI and anti-debug

An interesting point: many anti-debug techniques in Part 15 target debuggers (checking the PEB, debug port, 0xCC breakpoints). DBI doesn't use a debugger and doesn't place 0xCC breakpoints, so some of those checks can't catch it. Still, DBI leaves its own traces (abnormally slow run time, re-translated code regions, some Pin/DynamoRIO artifacts), so sophisticated malware has anti-DBI too. It's not a silver bullet, but it's a different angle of approach when the debugger is blocked.

## When to use DBI

Use it when your question is "global and quantitative": coverage, counting, wide traces, taint. Don't use it when you only need to look at one function (a debugger is faster) or hook a few APIs (Frida is lighter). DBI trades speed for visibility: the program runs many times slower, but in return you see everything.

## Lab

See [labs/17.7/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/17.7): use a DBI tool to collect the coverage of a program with a right input and a wrong input, then compare them to mark out the check function yourself.

## Key takeaways
- DBI inserts observation code into each instruction/block at runtime, no source needed, no disk file modified.
- Pin (C++, powerful), DynamoRIO (open source, drcov built in), QBDI (embeddable, nice API), TinyInst (light, for coverage/fuzzing).
- The strongest trick: coverage diffing between wrong and right input to find the check function.
- Heavier than Frida but detailed down to each instruction; use it for global questions, not for looking at a single point.
- Sidesteps part of anti-debug (no debugger, no 0xCC) but has its own anti-DBI.
