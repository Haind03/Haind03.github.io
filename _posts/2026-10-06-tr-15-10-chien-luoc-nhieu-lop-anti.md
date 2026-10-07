---
title: "Lesson 15.10: When several anti layers are stacked, how to fight"
date: 2026-10-06 09:35:00 +0700
categories: ["Technique Reverse", "Part 15 · Anti-Reversing and Bypasses"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
In the previous nine lessons, each one dissected a single anti technique. Reality is harsher: a malware sample or a commercial protector never uses just one trick. It stacks layers. A typical sample might have UPX or a custom packer on the outside, anti-debug placed in a TLS callback that runs even before main, anti-VM calling CPUID right at the start, an integrity check that hashes its own code section, and a core that's virtualized. You finish removing one layer and run into the next. This lesson doesn't teach any new trick, it teaches the order and the mindset so you don't drown.

## Rule number one: peel from the outside in

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

The classic beginner mistake is to rush into the logic core while the packer hasn't been removed, so you read nothing but junk. Just peel in order: unpack first (Lessons 14.2, 14.3), then deal with anti-debug, and only then get to the logic.

## Set up the environment properly, once

Before touching a multi-layer sample, put in the effort to set up the environment so you don't have to fight each individual check. Use a VM that looks like a real machine: enough CPU cores and RAM, some user files, a changed machine name, and the easily exposed VM artifacts removed (Lesson 15.5). Plug ScyllaHide (user mode) into x64dbg to swallow most of the anti-debug APIs and PEB checks at once, so you don't patch each by hand (Lesson 15.9). Use TitanHide or HyperHide when ScyllaHide isn't enough, since they hide at a deeper layer. And turn on the options to break at the TLS callback and the system breakpoint in x64dbg, so you attach early enough before the anti-debug in TLS gets to run (Lesson 15.4).

Set it up once, snapshot it, and use it for every later sample.

## When static is blocked, switch to dynamic

Anti-disassembly (Lesson 15.6) and virtualization (Lesson 14.5) make static disassemblers useless or wrong. When that happens, don't try to read statically at all costs. Run it dynamically and observe: real values show up in registers, decoded strings appear in memory, the real flow is clear when you single-step. Many anti layers are designed to beat the static reader, and they collapse as soon as you let it run and look.

## Divide and conquer: isolate each check

Don't try to get past every layer at the same time. For each check, do three things: find it, understand what it decides, and neutralize exactly that decision point. Usually the decision point is a branch instruction (`cmp` then `je/jne`) after the check has run. Patch that exact branch, or change the register value at runtime, and you're through, without needing to fully understand the check mechanism.

For integrity checks (Lesson 15.8), remember the counterintuitive lesson: don't modify the code being checked, neutralize the checking function itself. Modifying the code is lighting your own fuse.

## The heavy weapon: emulation skips a whole pile of anti

This is the most important idea of the lesson. A lot of anti-debug relies on there being a real debugger and a real operating system: PEB.BeingDebugged, NtQueryInformationProcess, RDTSC timing, hardware breakpoints. If you don't use a real debugger but **emulate** the code with Unicorn or Qiling (Lesson 18.2), that whole anti-debug group becomes meaningless, because there's no debugger to detect, and you control every return value of every API.

Emulation fits when you need to run an isolated function (for example the string decryption routine, or the serial generation function) without dragging along the program's whole anti-debug machinery. Isolate the function, load it into the emulator, feed input, get the output.

## When to stop unpicking and go black-box

You don't always need to understand every layer. If your goal is just "what input makes it print Correct", often there's no need to devirtualize what the VProtect core is doing and wear yourself out. Take the black-box approach: treat the protected part as a box, only observe the relation between input and output, or use symbolic execution (Lesson 18.3) to let a solver find an input that satisfies the condition at the output. Virtualization protects how things are computed, but usually can't hide the final condition that has to hold.

Always go back to the original question (Lesson 0.4): what do I actually need to know? Once you can answer that, you know which layers are worth removing and which to skip.

## Take notes, or you'll unpick it all over again

A multi-layer sample can eat many days. Write down each layer you've recognized, the address of each check, what you've neutralized and how. A simple table of "layer, address, how to bypass" saves you hours when you have to rerun, or when the sample resets after one mistake.

## A sample order to follow

```
1. Triage (DIE, strings, entropy): recognize what the outermost layer is
2. Set up the environment: realistic VM + ScyllaHide + early attach
3. Unpack: get to the OEP, dump, rebuild the IAT
4. Neutralize anti-debug/anti-VM: ScyllaHide handles most, patch the rest
5. Neutralize the integrity check (neutralize the check function, don't modify the checked code)
6. For a virtualized core: consider black-box / symbolic / emulation instead of fully devirtualizing
7. Take notes on every step
```

No two samples are exactly alike, but this frame keeps you heading in the right direction instead of flailing.

## Key takeaways
Peel layers in runtime order: packer, TLS, anti-VM, anti-debug, integrity, core. Set up the environment properly once (realistic VM + ScyllaHide + early attach) and then snapshot. When static is blocked, go dynamic, and don't try to read statically what anti-disasm has hit.

Isolate each check and neutralize exactly the decision point, without trying to do everything at once. Emulation (Unicorn/Qiling) disables the whole anti-debug group because there's no real debugger. Know when to switch to black-box or symbolic instead of fully unpicking, and take notes on each layer, otherwise you'll have to redo it from scratch.
