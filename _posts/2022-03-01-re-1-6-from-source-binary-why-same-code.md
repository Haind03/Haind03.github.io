---
title: "Lesson 1.6: From source to binary, and why the same code comes out in two different shapes"
date: 2022-03-01 14:05:00 +0700
categories: ["Technique Reverse", "Part 01 · Computer Fundamentals for RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Beginners often ask: I wrote a clean, clear C function, so why does it turn into a pile of assembly in IDA that looks nothing like the original? The answer is in the road from source to binary, and especially in a guy called the optimizer. Once you understand this road, you'll get less annoyed when the decompiler spits out weird code, and more importantly, you'll know ahead of time what kind of binary you're facing.

## The compilation pipeline

When you type `gcc hello.c -o hello`, it looks like one step, but there are actually four stages in a row. "Compiler" is just the umbrella name.

```
hello.c
   |  1. Preprocessor
   v
hello.i   (C with macros and #include expanded)
   |  2. Compiler (the real compiler)
   v
hello.s   (assembly)
   |  3. Assembler
   v
hello.o   (object file, machine code but not complete yet)
   |  4. Linker
   v
hello     (executable)
```

Each stage leaves traces you'll run into when reversing. The preprocessor handles every line starting with `#`: it pastes in the `#include` content, replaces `#define` macros, and strips comments. After this step all macros are gone. That's why a constant `#define MAX 100` in the source is just a bare `100` in the binary, with no trace of the name MAX.

The compiler then translates the expanded C into assembly. This is the smartest stage, and where optimization happens, so your code gets transformed the most here. The assembler translates assembly (text) into machine code (binary) in an object file. The translation is almost one to one, nothing creative. Finally the linker puts the object files together, connects function calls between files, and attaches library code. This stage decides the static versus dynamic linking question right below.

## Static vs dynamic linking, what you see as soon as you open the file

Your program calls `printf`. But you didn't write `printf`, it lives in the C library. There are two ways to attach it.

With dynamic linking (the common default), the executable only contains a note saying it needs `printf` from an external library (libc.so on Linux, DLLs on Windows). At runtime the loader finds and loads that library. The file is small, and what matters to you is that looking at the import table shows right away which functions it uses. `CreateFileW`, `socket`, `RegOpenKey` are all exposed. This is the number one source of clues during triage.

With static linking, all the library code is stuffed straight into the executable at link time. The file bloats, and `printf` now sits mixed in with your code, with no import to look at. Reversing is harder because you have to tell apart the code you need to read from thousands of library functions. This is where FLIRT signatures (Lesson 3.4) save you, since they recognize and label known library functions so you can skip them.

Go and Rust lean toward static linking by default, so their binaries are big and full of runtime code, which is part of why they have a reputation for being hard to reverse.

## Loader, the last stage at runtime

When you run the file, the OS calls the loader. It reads the header (PE or ELF, Lessons 1.7 and 1.8), maps the sections into memory with the right permissions (code is R-X, data is RW-), loads the needed dynamic libraries, fills in the import address table (IAT), handles relocations if ASLR changed the base, and only then jumps to the entry point. This whole process is why "what's on disk" and "what's in memory at runtime" aren't exactly the same, a point we touched on in Lesson 1.2.

## The optimizer, the main culprit that makes code hard to read

Now the most important part of this lesson. The same C source built with different optimization levels gives assembly that's worlds apart.

The optimization level is set with the `-O` flag. With `-O0` there's no optimization: the compiler translates almost every C line faithfully, so the code is verbose with a lot of redundant instructions, but it sticks close to the source. This is a gift for reversers. `-O1` and `-O2` are moderate and heavy optimization, and `-O2` is the default for most release software. `-O3` is aggressive and sometimes even changes the loop structure, and `-Os` optimizes for size.

Here is what the optimizer does, and why it gives you a headache. Inlining stuffs a small function straight into where it's called, instead of a `call`. That's good for speed and bad for you: the tidy `is_valid()` in the source disappears and its logic is spread into the middle of the parent function. You search forever and never find `call is_valid` because it no longer exists as its own function.

Loop unrolling flattens a loop that runs 4 times into 4 blocks of instructions in a row and drops the counter variable too, so you no longer see a "loop". Strength reduction replaces an expensive operation with a cheap one: `x * 8` becomes `shl x, 3`, and `x / 2` becomes a shift. Division by a constant even gets turned into a strange multiplication by a reciprocal plus a shift, and doesn't look like a division at all. When you see an `imul` with a weirdly big constant followed by `shr`, it's likely just a harmless division.

Temp variables in the source are kept entirely in registers and never touch memory, so the decompiler has nothing to name and makes up `v1`, `v2`, `v3`. The instruction order can also differ from the source, if branches are merged, and code that never runs is simply deleted.

The takeaway: when the decompiler gives you odd-looking code full of `v1 = v2 >> 3`, don't assume the author wrote it that way. The original source is very likely clean, and `-O2` just reshaped it. Conversely, if you build a binary yourself to learn (like in the lab), build with `-O0` to make it easier first, then try `-O2` to see the difference.

## Symbols, stripped, and debug info

Object files and executables can contain **symbols**: function names and global variable names, tied to addresses. When symbols are there, opening in IDA shows `check_password` instead of `sub_401500`, which is great.

A non-stripped file keeps the symbol table. A lot of debug builds, and quite a few Linux binaries, fall into this category. A stripped file has had its symbol table removed (with the `strip` command), leaving only the minimal symbols needed for dynamic linking, so every internal function name becomes `sub_xxx`. Release software is usually stripped. Debug info (DWARF on Linux/ELF, PDB on Windows) is a layer thicker than symbols, with data types, source line numbers, and local variable names. It's usually kept separate (a `.pdb`, `.dSYM` file). Getting hold of a matching PDB is like hitting the jackpot, the decompiled output nearly has the variable names too.

During triage, knowing whether the file is stripped sets the right expectation for difficulty. Detect It Easy and the tools in Lesson 2.1 tell you this right away.

## Lab

The lab is at [labs/1.6/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/1.6). You build the same C file four ways (-O0 and -O2, with and without strip), then open them in Ghidra to see inlining, strength reduction, and the difference between stripped and non-stripped with your own eyes. The solution with comparisons is at [labs/1.6/solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/1.6/solution.md), but try it before opening.

## Key takeaways
Compilation has four stages: preprocessor, compiler, assembler, linker, and macros disappear right at stage one. Dynamic linking exposes imports, which are golden clues during triage, while static linking stuffs library code inside and makes things harder. At runtime the loader maps sections, loads DLLs, fills the IAT and handles relocations, so "on disk" differs from "in memory".

The optimizer is the main culprit behind hard-to-read code through inlining, loop unrolling, strength reduction, and lost intermediate variables. Weird decompiled code is usually from `-O2`, not the author, and when building your own binaries to learn you should use `-O0`. A stripped file has lost all internal function names, and a PDB/DWARF alongside is like hitting the jackpot.
