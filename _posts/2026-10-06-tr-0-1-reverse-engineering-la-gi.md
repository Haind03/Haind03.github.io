---
title: "Lesson 0.1: What is reverse engineering, and why it's not as scary as you think"
date: 2026-10-06 08:00:00 +0700
categories: ["Technique Reverse", "Part 00 · Getting Started"]
tags: [reverse-engineering, basics]
render_with_liquid: false
---
The first time you open an `.exe` in IDA, a sea of green assembly hits you in the face: thousands of `mov`, `push`, `call` lines with no beginning and no end. The urge is to shut the laptop and go to sleep. I felt the same. But reverse engineering (RE) isn't about reading all of that. It's about knowing which parts are worth reading and skipping the other 95%.

Short version: RE is taking a finished product and working backwards to how it works, when you don't have the source code. People take an engine apart to see how it runs, and here we "take apart" a program.

## Why people reverse

Not everyone learns RE to crack software. This field feeds a lot of different areas. Malware analysis is one: a ransomware sample lands on a company's network and you have to know what it does, how it spreads, which server it talks to, and nobody hands you the attacker's source code. Vulnerability research is another. The software is closed and has no source, but you still need to know what bugs it has so you can report them to the vendor for a patch, or protect your own systems.

Then there's compatibility and recovery, like an old file format nobody supports anymore or a piece of hardware that lost its driver, where you reverse it to write a new one. You can also use RE to test the security of your own product before a hacker does it to you. And finally there's CTF and academic work, which is the healthiest playground for practicing the craft and also what this series uses the most.

## Two paths: static and dynamic

Every RE technique, however fancy, falls into one of two groups, or a mix of both.

Static analysis means you pick the file apart without running it. Open it in a disassembler/decompiler, read the code, look at strings, check the imports. It's completely safe because the program never executes. The weakness is that the code can be encrypted or packed, and what you see on disk isn't necessarily what actually runs.

Dynamic analysis means you run it in a controlled environment and watch. You use a debugger to set breakpoints, look at variable values at runtime, and track which files it touches and which APIs it calls. You see "the truth", but it's more dangerous (especially with malware) and the program may detect that you're watching (anti-debug).

Good RE people don't pick a side. Use static to narrow down "where is the interesting part", then use dynamic to see with your own eyes how that part runs.

## Layers of abstraction: the key to the whole field

![Layers of abstraction of a program](/assets/img/technique-reverse/assets/common/tang-truu-tuong.svg)

This is the most important thing in this lesson. Remember it and you'll understand how the whole series is laid out.

A program exists at several layers, and the lower you go, the further from humans:

```
Source code (C, C#, Java, Python...)   <- the programmer writes here
        |  compiler
        v
Bytecode / IL  (only for .NET, Java, Python...)
        |  JIT or interpreter
        v
Machine code / Assembly  (native: C, C++, Go, Rust...)
        |  CPU
        v
Electricity
```

The key point is that how hard a reverse is depends entirely on which layer the program stops at.

Managed languages (C#/.NET, Java, Python) compile to bytecode that keeps almost all the information: function names, variable names, class structure. Decompiling a `.NET` file with dnSpy often gives code nearly identical to the original. That's why this series starts "celebrating" early with the .NET and Java parts. Native languages (C, C++, Go, Rust) compile straight to machine code. Variable names are gone, and the structure gets chopped up and optimized by the compiler. This is the "real" reversing, and it's why we have to learn assembly.

That's also why the course orders languages from easiest to hardest to recover, not from most common to least common.

## The minimum toolkit

Don't install anything yet, lesson [0.3](/posts/tr-0-3-dung-lab-an-toan/) sets up a proper lab. But so you get the picture, here's the "5 things" almost everyone doing RE has: something to identify files (Detect It Easy), a disassembler/decompiler (IDA Free or Ghidra), a debugger (x64dbg on Windows, GDB on Linux), a hex editor (HxD, ImHex), and language-specific tools (dnSpy for .NET, JADX for Android, pycdc for Python, all three are already in this repo).

The fuller list of 200+ tools is in the [tool repository](/posts/tr-tai-nguyen-cong-cu/), but don't install them all at once. Install when a lesson needs one.

## The reality of learning

There will be evenings when you sit for hours just to understand what one function does, and it turns out it only checks the string length. That's normal. RE is a skill that builds up slowly: 80% of the early time goes to getting used to the tools and learning to read assembly, and the "aha" comes later. Anyone who says they got good at RE in two weeks is either lying or just hit the "decompile" button and copied the output.

The goal of this series isn't to cram theory but to have you actually do one concrete thing in every lesson. The next lesson covers the legal and ethical boundaries, the boring part that will cost you one day if you skip it.

## Key takeaways
RE means understanding how a program works when you don't have the source code. There are two branches, static (don't run it) and dynamic (run it and observe), and they're usually used together.

Difficulty depends on which layer the program stops at: managed is easy and native is hard. Don't try to read all the assembly, learn to find the parts worth reading.
