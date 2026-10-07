---
title: "Lesson 1.6: From source to binary, and why the same code comes out in two different shapes"
image:
  path: /assets/img/covers/re-1-6-from-source-binary-why-same-code.webp
  alt: "Lesson 1.6: From source to binary, and why the same code comes out in two different shapes"
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

In this lab you take one small C program and build it several ways, then open each build in Ghidra (or IDA) to watch the optimizer work. The goal is to see inlining, loop unrolling and strength reduction with your own eyes, and to feel the difference between a binary that still has symbols and one that has been stripped. The program is `optdemo.c`. It contains a few deliberate baits for the optimizer: a tiny function that is easy to inline, a loop with a fixed trip count, and a multiplication and a division by constants.

On Linux, gcc or clang both work. Build four variants to compare: an unoptimized build with symbols (the easiest to read), an `-O2` build with symbols (inlining and strength reduction show up), an `-O2` build that is then stripped (internal function names are gone), and optionally an `-O3` build to see even more aggressive optimization.

```sh
gcc -O0 -g optdemo.c -o optdemo_O0
gcc -O2 -g optdemo.c -o optdemo_O2
gcc -O2 optdemo.c -o optdemo_O2_stripped
strip optdemo_O2_stripped
gcc -O3 optdemo.c -o optdemo_O3
```

On Windows you can use MSVC, where `/Od` is the equivalent of `-O0`:

```
cl /Od optdemo.c /Fe:optdemo_Od.exe
cl /O2 optdemo.c /Fe:optdemo_O2.exe
```

Start by opening `optdemo_O0` and finding the four functions `square`, `sum_fixed`, `scale` and `compute`. They should all be there and call each other in a clear way. Then open `optdemo_O2` and answer a few questions. Do you still see `call square`, and where did `square` go? Is the loop in `sum_fixed` still a loop, or has it turned into a constant? What does `x * 8` become inside `scale`, and what does `x / 3` look like? Next open `optdemo_O2_stripped` and check what the functions are called now and what information you lost compared with the build that kept its symbols. Finally, work out how the optimization level and stripping change the difficulty of reversing the same logic.

Two hints. `sum_fixed()` always returns 0+1+2+3 = 6, and the optimizer knows that at compile time, so ask yourself whether it still computes anything. And at `-O2` a division by 3 usually becomes an `imul` with a strange 32-bit constant (a reciprocal) followed by `shr` or `sar`, so do not mistake it for a real multiplication.

<div class="lab-box">
<div class="lab-head"><b>LAB 1.6</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/1.6/src/optdemo.c" download><i class="fa-solid fa-file-code"></i>src/optdemo.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Try it yourself first. The exact output depends on your gcc or clang version, but the patterns below hold for every recent release.

At `-O0` the binary is honest. All four functions are intact and separate, and `compute` contains three `call` instructions, to `square`, `sum_fixed` and `scale`, so the control flow matches the source exactly. Every function has a full prologue and epilogue, local variables are spilled to the stack (`[rbp-x]`), and there are many seemingly pointless `mov` instructions shuffling values through memory. That is the price of not optimizing, and in exchange the code stays close to what the author wrote. It is the reason to build with `-O0` first when you are learning.

At `-O2` the optimizer gets to work. You will not find `call square` any more. The body of `square`, a single multiplication, has been pasted straight into `compute`, and with a constant `n` the whole squaring can even be folded at compile time. The lesson is that in optimized code a "missing" function does not mean the author never wrote it, only that it was inlined.

`sum_fixed` turns into a constant. It always yields 6 and the optimizer works that out at compile time, so the loop disappears completely, with no counter and no backward jump. Most likely `compute` just adds `6` to the result, or folds it into a larger constant. This is loop unrolling pushed to the limit: the whole loop is unrolled and then collapsed into one number.

`scale` shows strength reduction. `x * 8` almost certainly becomes `lea` or `shl reg, 3`, with no `imul` at all, because a shift is cheaper. `x / 3` is the interesting part. You will see something like this:

```asm
mov   eax, x
movsxd rax, eax          ; or similar
imul  rax, rax, 0x55555556   ; multiply by a "magic number" (the reciprocal of 3)
shr   rax, 32            ; or sar, take the high part
... a few sign-fixing instructions
```

This is not a real multiplication by a big number. It is how the compiler divides by a constant without using the very slow `div` instruction. The constant `0x55555556` is the multiplicative inverse of 3 in fixed-point form. Once you see the pattern of an `imul` with a magic number followed by `shr`, you can recognize it immediately as a division by a constant.

Stripping removes names. In `optdemo_O2`, Ghidra shows `compute` and `scale` (the functions that were not fully inlined) with their real names. In `optdemo_O2_stripped` they all become `FUN_00401xxx` in Ghidra or `sub_401xxx` in IDA. `main` can often still be recognized from the way the runtime calls it, but the internal functions lose their names entirely. What you lose is the internal function names. What you keep is the logic, the constants and the instruction structure. In other words, stripping slows you down because you have to rename things yourself, but it does not hide the behavior.

Putting it together: `-O2` inlines, unrolls, strength-reduces and interleaves instructions, so it is much harder to read than `-O0`. Small functions get inlined and vanish as separate functions, fixed-count loops can be computed ahead of time into a constant, and multiplication or division by a constant turns into shifts or an `imul` with a magic number that you should not misread. Stripping loses internal names but not logic. Real release software is almost always `-O2` and stripped, so you accept both layers of difficulty by default, and the habit of renaming functions early (Lesson 0.4) together with recognizing optimizer patterns is what gets you through.

</details>

## Key takeaways
Compilation has four stages: preprocessor, compiler, assembler, linker, and macros disappear right at stage one. Dynamic linking exposes imports, which are golden clues during triage, while static linking stuffs library code inside and makes things harder. At runtime the loader maps sections, loads DLLs, fills the IAT and handles relocations, so "on disk" differs from "in memory".

The optimizer is the main culprit behind hard-to-read code through inlining, loop unrolling, strength reduction, and lost intermediate variables. Weird decompiled code is usually from `-O2`, not the author, and when building your own binaries to learn you should use `-O0`. A stripped file has lost all internal function names, and a PDB/DWARF alongside is like hitting the jackpot.
