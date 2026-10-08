---
title: "Lesson 17.7: Dynamic Binary Instrumentation"
image:
  path: /assets/img/covers/re-17-7-dynamic-binary-instrumentation-letting-binary-tell.webp
  alt: "Lesson 17.7: Dynamic Binary Instrumentation"
date: 2022-08-28 11:03:00 +0700
categories: ["Reverse Engineering", "Part 17 · Patching, Hooking, Injection"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
A debugger lets you stop and inspect point by point. Frida lets you hook a few functions. Neither helps much when you want to ask "in this run, which instructions did the program actually execute", or "where does the flow differ between a wrong input and a right one". For that you need Dynamic Binary Instrumentation (DBI).

![Coverage diffing with DBI](/assets/img/re/re-17-7-dynamic-binary-instrumentation-letting-binary-tell.svg)
_Run a wrong and a correct input under a DBI tool and diff the executed blocks_

## What DBI is

DBI inserts analysis code (instrumentation) into a binary's execution flow while it runs, with no source code and without modifying the file on disk. A DBI tool reads each basic block about to run, re-translates it together with your observation snippets, and only then lets the CPU run the instrumented version.

You write something like "every time an instruction runs, add one to a counter", or "every time memory is written, record the address", and the DBI tool attaches that snippet to every instruction/every write of the target program. The program can't tell it's being observed at this level.

How it differs from the tools you've learned:

| Tool | Level of intervention | Good for |
|---|---|---|
| Debugger (x64dbg) | stops at breakpoints, manual | a deep look at one point |
| Frida ([Lesson 17.2](/posts/re-17-2-frida-full-inspecting-modifying-program-while/)) | function-level hooks | reading/changing parameters, observing APIs |
| DBI (Pin, DynamoRIO...) | per instruction/block, whole program | coverage, wide traces, taint |

DBI is heavier than Frida (it runs much slower because it re-translates every block) but far more detailed, since it sees every instruction, not just function boundaries.

## Four tools people use

Intel Pin has been around a long time and is free (not open source). You write a pintool in C++, registering callbacks for each instruction (INS), each block (BBL), each loaded image (IMG). It's used a lot for instruction counting, memory traces, and taint analysis.

DynamoRIO is open source with a client architecture and a compact API. It comes with sample tools like drcov (collects coverage) and drltrace (traces library calls). Many people like it because it's open and faster than Pin for some tasks.

QBDI (QuarksLab) is a DBI you can embed in other programs, with nice Python and C++ APIs, good for writing quick analysis scripts instead of building a whole pintool.

TinyInst is lightweight and leans toward coverage for fuzzing. It doesn't re-translate everything like Pin/DynamoRIO but only instruments where needed, so it's fast and stable on large binaries on Windows/macOS.

Beginners should start with a ready-made tool (DynamoRIO's drcov) before writing their own pintool.

## Coverage diffing

This is the main reason to learn DBI. Run the program with a wrong input and collect the set of basic blocks executed (coverage A). Run again with a nearly right or right input and collect coverage B. Then compare. The blocks that appear only in B and not in A are the code that runs when you go deeper into the check logic.

For a crackme, this marks out the serial check function without you having to understand anything beforehand. The program itself shows you where it branches when the input gets better. Combining coverage with fuzzing is the foundation of modern fuzzing (AFL uses this coverage idea to guide itself).

There are other uses too. With instruction count and execution traces, you can understand what an obfuscated function does by looking at the sequence of instructions that actually run, ignoring junk code that never executes (useful against anti-disassembly in [Lesson 15.6](/posts/re-15-6-anti-disassembly-when-disassembler-itself-gets/)). A memory trace records every memory read/write to follow where a value goes. Taint analysis marks the input as "tainted" then tracks it spreading through registers and memory cells, to see which decisions the input affects.

## DBI and anti-debug

Many anti-debug techniques in Part 15 target debuggers (checking the PEB, debug port, 0xCC breakpoints). DBI doesn't use a debugger and doesn't place 0xCC breakpoints, so some of those checks can't catch it. DBI leaves its own traces though (abnormally slow run time, re-translated code regions, some Pin/DynamoRIO artifacts), so sophisticated malware has anti-DBI too. It doesn't solve everything, but it gives you a different angle when the debugger is blocked.

## When to use DBI

Use it when your question is global and quantitative, such as coverage, counting, wide traces, taint. Don't use it when you only need to look at one function (a debugger is faster) or hook a few APIs (Frida is lighter). DBI trades speed for visibility. The program runs many times slower, but you see everything.

## Lab

The task is to use a DBI tool to collect the code coverage of a program with two different inputs, then compare them to narrow down the code that runs when you get deeper into the check logic. You don't have to understand the program beforehand, because the coverage points the way. You need one DBI tool, such as DynamoRIO (which ships `drcov`), Intel Pin, or QBDI. This lab is described with DynamoRIO because `drcov` already collects coverage. You also need a practice target, a crackme that takes an input and prints right or wrong (for example the crackme from Lesson 3.5 or Lesson 2.5), and a tool to view and compare coverage, either Lighthouse (an IDA/Binary Ninja plugin) or your own diff script.

First run the target with an input that is certainly WRONG and collect the coverage:

```
drrun -t drcov -- ./target wrongwrong
```

The result is a `drcov.*.log` file recording the basic blocks that ran. Run it again with a "better" input (the right length, the right prefix, or an input you guess gets further into the check function) and collect a second coverage. Compare the two sets of blocks. The blocks that appear ONLY in the second run are code newly triggered by going deeper. Load both coverage files into Lighthouse in IDA or Binary Ninja, color them, and see which function the new blocks fall in. That is very likely the check function (or branch). Finally open that function and read it statically to confirm it is the serial or password check logic.

Some questions to think about. Why does coverage diffing find the check function faster than reading statically from the start? If the right and wrong inputs give identical coverage all the way to the end, what does that suggest about how the check works (for example a comparison that does not branch early)? And DBI runs many times slower than a normal run, so when is that cost worth paying and when should you go back to a debugger?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Try it yourself before reading.

### The coverage diffing procedure with DynamoRIO

First collect the coverage for a wrong input:

```
drrun -t drcov -- ./target AAAAAAAA
```

This produces `drcov.target.<pid>.0000.proc.log`, which you rename to `cov_wrong.log`. Then collect the coverage with a better input. Suppose triage shows the correct serial is 10 characters long and starts with "RE", so try:

```
drrun -t drcov -- ./target RE00000000
```

and rename it to `cov_better.log`. To compare, the quickest way is to load both into Lighthouse (in IDA, File > Load file > Code coverage file). Lighthouse colors the blocks that ran. Open the two coverages and use the diff (composition) feature to get `cov_better - cov_wrong`. The extra blocks lit up in the "better" run concentrate in one function, usually the per-character comparison or the serial transform function, and that is the target. Open that function statically (F5 in IDA) to read the logic and recover the correct serial.

### Why this is fast

Instead of reading from `main` down through the CRT and dozens of helper functions, you let the program filter for you, so only the code that reacts to the better input shows up in the diff. For a large or obfuscated binary, this is the cheapest way to narrow things down.

### Answers to the questions

Coverage diffing is faster because it removes all code unrelated to the difference between right and wrong, leaving only the logic branch you care about, while static reading has you filter by eye. If coverage is identical to the end, the check function most likely compares without branching early (for example accumulating a `diff |= a[i]^b[i]` variable and checking once at the end, or a constant-time memcmp). Then coverage is useless and you have to switch to a memory trace or static reading. The slowness cost of DBI is worth it when the question is global (coverage, wide tracing, taint). When you only need to inspect one function whose address you already know, a debugger is much faster and more direct.

The `drrun -t drcov` procedure and the way of loading into Lighthouse follow the DynamoRIO and Lighthouse documentation. You need DynamoRIO or Pin installed, and Lighthouse needs the IDA or Binary Ninja GUI, so run it on your own machine to get real numbers.

</details>

## Key takeaways
DBI inserts observation code into each instruction/block at runtime, with no source needed and no disk file modified. The tools are Pin (C++), DynamoRIO (open source, drcov built in), QBDI (embeddable, nice API), and TinyInst (light, for coverage/fuzzing). The most useful trick is coverage diffing between wrong and right input to find the check function.

It's heavier than Frida but detailed down to each instruction, so use it for global questions, not for looking at a single point. It sidesteps part of anti-debug (no debugger, no 0xCC) but has its own anti-DBI.
