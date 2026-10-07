---
title: "Lesson 15.10: Handling stacked anti-analysis layers"
image:
  path: /assets/img/covers/re-15-10-when-several-anti-layers-are-stacked.webp
  alt: "Lesson 15.10: Handling stacked anti-analysis layers"
date: 2023-07-01 23:10:00 +0700
categories: ["Technique Reverse", "Part 15 · Anti-Reversing and Bypasses"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
In the previous nine lessons each one covered a single anti technique. In practice a malware sample or a commercial protector never uses just one trick, it stacks layers. A typical sample might have UPX or a custom packer on the outside, anti-debug in a TLS callback that runs even before main, anti-VM calling CPUID right at the start, an integrity check that hashes its own code section, and a virtualized core. You finish removing one layer and hit the next. This lesson doesn't teach a new trick. It covers the order to work in so you don't get lost.

## Work from the outside in

The anti layers are ordered by when they run, and you have to respect that order. Whatever runs earliest has to be handled first, because otherwise you won't even reach the place where the next layer is.

A typical runtime order:

```
1. Packer stub          (runs first, unpacks the real code)
2. TLS callback         (runs before the entry point, often hides anti-debug here)
3. Entry point / CRT
4. Anti-VM, anti-sandbox (right when main starts)
5. Anti-debug API + PEB  (scattered everywhere)
6. Integrity check       (periodic or before sensitive parts)
7. Virtualized core      (the most heavily protected logic core)
```

The classic beginner mistake is to go into the logic core while the packer is still there, so you read nothing but junk. Go in order: unpack first (Lessons 14.2, 14.3), then deal with anti-debug, and only then get to the logic.

## Set up the environment properly, once

Before touching a multi-layer sample, spend the time to set up the environment so you don't have to fight each check separately. Use a VM that looks like a real machine: enough CPU cores and RAM, some user files, a changed machine name, and the easily exposed VM artifacts removed (Lesson 15.5). Plug ScyllaHide (user mode) into x64dbg to swallow most of the anti-debug APIs and PEB checks at once, so you don't patch each by hand (Lesson 15.9). Use TitanHide or HyperHide when ScyllaHide isn't enough, since they hide at a deeper layer. And turn on the options to break at the TLS callback and the system breakpoint in x64dbg, so you attach early enough, before the anti-debug in TLS runs (Lesson 15.4).

Set it up once, snapshot it, and use it for every later sample.

## When static is blocked, switch to dynamic

Anti-disassembly (Lesson 15.6) and virtualization (Lesson 14.5) make static disassemblers useless or wrong. When that happens, don't insist on reading statically. Run it and observe. Real values show up in registers, decoded strings appear in memory, and the real flow is clear when you single-step. Many anti layers are designed to beat the static reader, and they stop working once you let the program run and look.

## Isolate each check

Don't try to get past every layer at the same time. For each check, do three things: find it, understand what it decides, and neutralize that decision point. Usually the decision point is a branch (`cmp` then `je/jne`) after the check has run. Patch that exact branch, or change the register value at runtime, and you're through, without needing to fully understand how the check works.

For integrity checks (Lesson 15.8), remember not to modify the code being checked. Neutralize the checking function itself. If you modify the code, the check will catch it.

## Emulation skips a lot of anti-debug

This is the most useful idea in the lesson. A lot of anti-debug relies on a real debugger and a real operating system: PEB.BeingDebugged, NtQueryInformationProcess, RDTSC timing, hardware breakpoints. If you don't use a real debugger but emulate the code with Unicorn or Qiling (Lesson 18.2), that whole group of anti-debug does nothing. There's no debugger to detect, and you control every return value of every API.

Emulation fits when you need to run an isolated function (for example the string decryption routine, or the serial generation function) without dragging along the program's whole anti-debug code. Isolate the function, load it into the emulator, feed input, get the output.

## When to stop unpicking and go black-box

You don't always need to understand every layer. If your goal is just "what input makes it print Correct", often there's no need to devirtualize the core. Take the black-box approach: treat the protected part as a box and only observe the relation between input and output, or use symbolic execution (Lesson 18.3) to let a solver find an input that satisfies the condition at the output. Virtualization protects how things are computed, but usually can't hide the final condition that has to hold.

Always go back to the original question (Lesson 0.4): what do I actually need to know? Once you can answer that, you know which layers are worth removing and which to skip.

## Take notes

A multi-layer sample can take days. Write down each layer you've recognized, the address of each check, and what you've neutralized and how. A simple table of layer, address and bypass saves hours when you have to rerun, or when the sample resets after one mistake.

## A sample order

```
1. Triage (DIE, strings, entropy): recognize what the outermost layer is
2. Set up the environment: realistic VM + ScyllaHide + early attach
3. Unpack: get to the OEP, dump, rebuild the IAT
4. Neutralize anti-debug/anti-VM: ScyllaHide handles most, patch the rest
5. Neutralize the integrity check (neutralize the check function, don't modify the checked code)
6. For a virtualized core: consider black-box / symbolic / emulation instead of fully devirtualizing
7. Take notes on every step
```

No two samples are exactly alike, but this order keeps you going in the right direction.

## Lab

This lab has no binary to run. It practices something more important: knowing what to do, and in what order, before you touch anything. Newcomers often feel overwhelmed when they open a sample with every kind of anti-technique and don't know where to start, so this exercise makes you write the plan down.

Imagine you receive a file `target.exe` and the first triage shows the following. Detect It Easy reports a custom packer, an entropy of 7.9 in the main section, and imports that are only `LoadLibraryA`, `GetProcAddress` and `VirtualAlloc`. There's a TLS directory with one callback. When you try it in x64dbg, the program exits immediately with the message "Debugger detected". After you get past that for now, a function calls `CPUID` and then exits when running in a VM. The license check lives in a function that looks like a huge dispatcher loop with a state variable, a sign of virtualization. And before entering the license function, a piece of code reads the program's own code section and compares it.

Your job is to write a plan. List the anti layers present in the sample and tie each to the matching lesson in Parts 14 and 15. Put them in the order you would handle them and explain why. For each layer, give one concrete way past it (a tool or an action). Say which layer you would not try to fully remove, with the reason and an alternative approach. And describe the environment you would set up before starting.

A few questions to think about. Why shouldn't you touch the integrity check function by modifying the code section? In what cases does emulation (Unicorn/Qiling) let you skip most of the anti-debug without patching anything? And if all you need is a valid license key, do you have to devirtualize the core? Write your own plan first, then open the solution to compare.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

This is a reference plan. Yours doesn't have to match exactly, as long as the order is sensible and the reasons are solid.

First, the anti layers and the matching lessons:

| Triage sign | Anti layer | Lesson |
|---|---|---|
| Entropy 7.9, poor imports, VirtualAlloc | Packer | [14.1](/posts/re-14-1-packers-work-spot-one/), [14.2](/posts/re-14-2-unpacking-upx-automatic-manual/) |
| TLS callback | Early-running anti-debug | [15.4](/posts/re-15-4-advanced-anti-debug-self-debug-tls/) |
| "Debugger detected" | API/PEB anti-debug | [15.1](/posts/re-15-1-anti-debug-via-windows-apis-group/), [15.2](/posts/re-15-2-anti-debug-reading-peb-directly-when/) |
| CPUID then exit in a VM | Anti-VM | [15.5](/posts/re-15-5-anti-vm-anti-sandbox-when-sample/) |
| Reads and compares its own code section | Integrity check | [15.8](/posts/re-15-8-integrity-checks-anti-tamper-when-program/) |
| Dispatcher plus state variable | Virtualization | [14.5](/posts/re-14-5-code-virtualization-highest-wall/) |

For the order of attack, the packer comes first. Until you unpack it, everything behind it is still compressed and meaningless to read. Get to the OEP, dump, and rebuild the IAT with Scylla. Next is the anti-debug in the TLS callback. It runs before the entry point, so it has to be neutralized before you reach the real code. Turn on stopping at TLS callbacks in x64dbg. Then the API and PEB anti-debug, neutralized with ScyllaHide from the very start. After that comes the anti-VM, handled by making the VM look real and patching the branch after `CPUID`. The integrity check is next, and it must be disabled before you patch anything else in the code, otherwise it will detect your earlier patches. The virtualized core goes last, because it's the most expensive.

For ways past each layer: unpack the packer by hand with the ESP trick, then dump and use Scylla ([14.2](/posts/re-14-2-unpacking-upx-automatic-manual/), [14.3](/posts/re-14-3-dumping-process-rebuilding-iat-scylla/)). For the TLS anti-debug, break at the TLS callback, step past it, then patch it or let ScyllaHide handle it. For API/PEB anti-debug, use ScyllaHide ([15.9](/posts/re-15-9-bypassing-anti-debug-from-mouse-click/)). For anti-VM, build a realistic VM and patch the `je/jne` after `CPUID`. For the integrity check, patch the checksum comparison branch so it always counts as a match, and don't modify the code being checked.

The layer I wouldn't fully remove is the virtualized core. Fully devirtualizing a custom VM takes weeks. If the goal is only to find a valid license key, a black-box approach is much more efficient: set a condition on the output (where validity is decided) and then use symbolic execution ([18.3](/posts/re-18-3-symbolic-execution-making-computer-solve-crackme/)) or constraint-based brute force to find a satisfying input. A VM protects how the value is computed, and it rarely hides the final condition.

For the environment, I'd set up a VM with 4 cores and 8 GB of RAM, with user files, a renamed machine, and the easily exposed VM artifacts removed. I'd run x64dbg with ScyllaHide, with stopping at TLS callbacks and the system breakpoint turned on. I'd take a snapshot of the clean state so I can rerun quickly after a mistake. And I'd keep Unicorn/Qiling ready to isolate and emulate the decryption routine while skipping the anti-debug.

On the reflection questions: you don't modify the code section because the integrity check will catch it. Changing the code throws the checksum off and the program detects tampering, so the right move is to neutralize the check function itself. Emulation skips anti-debug when you isolate one function and run it in Unicorn/Qiling, since there's no real debugger for PEB.BeingDebugged, NtQueryInformationProcess or RDTSC to detect, and you control every return value. And you don't need to devirtualize if you only need a valid key, because a black-box or symbolic approach on the output condition is usually enough.

</details>

## Key takeaways
Work through the layers in runtime order: packer, TLS, anti-VM, anti-debug, integrity, core. Set up the environment properly once (realistic VM + ScyllaHide + early attach) and then snapshot. When static is blocked, go dynamic, and don't try to read statically what anti-disassembly has hit.

Isolate each check and neutralize the decision point, without trying to do everything at once. Emulation (Unicorn/Qiling) disables the whole anti-debug group because there's no real debugger. Know when to switch to black-box or symbolic instead of fully unpicking, and take notes on each layer, otherwise you'll have to redo it from scratch.
