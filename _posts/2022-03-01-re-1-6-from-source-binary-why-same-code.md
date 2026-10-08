---
title: "Lesson 1.6: From source code to binary"
image:
  path: /assets/img/covers/re-1-6-from-source-binary-why-same-code.webp
  alt: "Lesson 1.6: From source code to binary"
date: 2022-03-01 14:05:00 +0700
categories: ["Reverse Engineering", "Part 01 · Computer Fundamentals for RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Beginners often ask why a clean C function they wrote becomes so much assembly in IDA that looks nothing like the original. The reason is the process from source to binary, and mostly the optimizer. Once you understand this process, weird decompiler output annoys you less, and you know ahead of time what kind of binary you're facing.

## The compilation pipeline

When you type `gcc hello.c -o hello` it looks like one step, but there are four stages in a row. "Compiler" is just the umbrella name.

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

Each stage leaves traces you'll run into when reversing. The preprocessor handles every line starting with `#`. It pastes in the `#include` content, replaces `#define` macros, and strips comments. After this step all macros are gone. That's why a constant `#define MAX 100` in the source is just a bare `100` in the binary, with no trace of the name MAX.

The compiler then translates the expanded C into assembly. This is where optimization happens, so your code gets changed the most here. The assembler translates assembly text into machine code in an object file. That translation is almost one to one. Finally the linker puts the object files together, connects function calls between files, and attaches library code. It also decides the static versus dynamic linking question below.

## Static vs dynamic linking

Your program calls `printf`, but you didn't write `printf`. It lives in the C library, and there are two ways to attach it.

With dynamic linking (the usual default), the executable only contains a note saying it needs `printf` from an external library (libc.so on Linux, DLLs on Windows). At runtime the loader finds and loads that library. The file is small, and the import table shows right away which functions it uses. `CreateFileW`, `socket`, `RegOpenKey` are all visible. This is the biggest source of clues during triage.

With static linking, all the library code is copied into the executable at link time. The file gets bigger, and `printf` sits mixed in with your code, with no import to look at. Reversing is harder because you have to separate the code you need to read from thousands of library functions. FLIRT signatures (Lesson 3.4) help here, since they recognize and label known library functions so you can skip them.

Go and Rust lean toward static linking by default, so their binaries are big and full of runtime code. That's part of why they have a reputation for being hard to reverse.

## The loader

When you run the file, the OS calls the loader. It reads the header (PE or ELF, Lessons 1.7 and 1.8), maps the sections into memory with the right permissions (code is R-X, data is RW-), loads the needed dynamic libraries, fills in the import address table (IAT), handles relocations if ASLR changed the base, and then jumps to the entry point. So what's on disk and what's in memory at runtime aren't exactly the same, which we touched on in Lesson 1.2.

## The optimizer

This is the most important part of the lesson. The same C source built with different optimization levels gives very different assembly.

The level is set with the `-O` flag. With `-O0` there's no optimization. The compiler translates almost every C line faithfully, so the code is verbose with a lot of redundant instructions, but it stays close to the source. That's the easiest case for a reverser. `-O1` and `-O2` are moderate and heavy optimization, and `-O2` is the default for most release software. `-O3` is aggressive and sometimes even changes the loop structure, and `-Os` optimizes for size.

Here's what the optimizer does that makes your life harder. Inlining puts a small function's body right where it's called, instead of a `call`. It's good for speed and bad for you. The tidy `is_valid()` in the source disappears and its logic is spread into the middle of the parent function. You search for `call is_valid` and never find it because it no longer exists as its own function.

Loop unrolling flattens a loop that runs 4 times into 4 blocks of instructions in a row and drops the counter variable too, so you no longer see a loop. Strength reduction replaces an expensive operation with a cheap one. For example, `x * 8` becomes `shl x, 3`, and `x / 2` becomes a shift. Division by a constant even becomes a strange multiplication by a reciprocal plus a shift, and doesn't look like a division at all. If you see an `imul` with a weirdly big constant followed by `shr`, it's probably just a division.

Temp variables from the source are kept entirely in registers and never touch memory, so the decompiler has nothing to name and makes up `v1`, `v2`, `v3`. The instruction order can also differ from the source, branches can be merged, and code that never runs is deleted.

So when the decompiler gives you odd code full of `v1 = v2 >> 3`, don't assume the author wrote it that way. The original source is probably clean and `-O2` reshaped it. If you build a binary yourself to learn (like in the lab), build with `-O0` first, then try `-O2` to see the difference.

## Symbols, stripped, and debug info

Object files and executables can contain symbols, which are function names and global variable names tied to addresses. When symbols are there, IDA shows `check_password` instead of `sub_401500`, which is great.

A non-stripped file keeps the symbol table. A lot of debug builds, and quite a few Linux binaries, are like this. A stripped file has had its symbol table removed (with the `strip` command), leaving only the minimal symbols needed for dynamic linking, so every internal function name becomes `sub_xxx`. Release software is usually stripped. Debug info (DWARF on Linux/ELF, PDB on Windows) goes further than symbols, with data types, source line numbers, and local variable names. It's usually kept in a separate file (`.pdb`, `.dSYM`). If you can get a matching PDB, that's a big win, since the decompiled output nearly has the variable names too.

During triage, knowing whether the file is stripped tells you how hard it will be. Detect It Easy and the tools in Lesson 2.1 show this right away.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 1.6</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/1.6.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/1.6/src/optdemo.c" download><i class="fa-solid fa-download"></i>src/optdemo.c</a>
</div>
</div>

In this lab you take one small C program and build it several ways, then open each build in Ghidra (or IDA) to watch the optimizer work. The goal is to see inlining, loop unrolling and strength reduction yourself, and to feel the difference between a binary that still has symbols and one that has been stripped. The program is `optdemo.c`. It has a few deliberate baits for the optimizer, such as a tiny function that is easy to inline, a loop with a fixed trip count, and a multiplication and a division by constants.

On Linux, gcc or clang both work. Build four variants to compare, namely an unoptimized build with symbols (the easiest to read), an `-O2` build with symbols (inlining and strength reduction show up), an `-O2` build that is then stripped (internal function names are gone), and optionally an `-O3` build to see even more aggressive optimization.

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

Two hints. `sum_fixed()` always returns 0+1+2+3 = 6, and the optimizer knows that at compile time, so ask yourself whether it still computes anything. And at `-O2` a division by 3 usually becomes an `imul` with a strange 32-bit constant (a reciprocal) followed by `shr` or `sar`, so don't mistake it for a real multiplication.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Try it yourself first. The exact output depends on your gcc or clang version, but the patterns below hold for every recent release.

At `-O0` the binary keeps the source structure. All four functions are intact and separate, and `compute` contains three `call` instructions, to `square`, `sum_fixed` and `scale`, so the control flow matches the source exactly. Every function has a full prologue and epilogue, local variables are spilled to the stack (`[rbp-x]`), and there are many seemingly pointless `mov` instructions shuffling values through memory. That's the price of not optimizing, and in exchange the code stays close to what the author wrote. It's the reason to build with `-O0` first when you're learning.

At `-O2` the optimizer gets to work. You won't find `call square` any more. The body of `square`, a single multiplication, has been pasted straight into `compute`, and with a constant `n` the whole squaring can even be folded at compile time. In optimized code a "missing" function doesn't mean the author never wrote it, only that it was inlined.

`sum_fixed` turns into a constant. It always yields 6 and the optimizer works that out at compile time, so the loop disappears completely, with no counter and no backward jump. Most likely `compute` just adds `6` to the result, or folds it into a larger constant. This is loop unrolling pushed to the limit, where the whole loop is unrolled and then collapsed into one number.

`scale` shows strength reduction. `x * 8` almost certainly becomes `lea` or `shl reg, 3`, with no `imul` at all, because a shift is cheaper. `x / 3` is the interesting part. You will see something like this:

```asm
mov   eax, x
movsxd rax, eax          ; or similar
imul  rax, rax, 0x55555556   ; multiply by a "magic number" (the reciprocal of 3)
shr   rax, 32            ; or sar, take the high part
... a few sign-fixing instructions
```

This isn't a real multiplication by a big number. It's how the compiler divides by a constant without the very slow `div` instruction. The constant `0x55555556` is the multiplicative inverse of 3 in fixed-point form. Once you've seen an `imul` with a magic number followed by `shr`, you'll recognize it as a division by a constant.

Stripping removes names. In `optdemo_O2`, Ghidra shows `compute` and `scale` (the functions that were not fully inlined) with their real names. In `optdemo_O2_stripped` they all become `FUN_00401xxx` in Ghidra or `sub_401xxx` in IDA. `main` can often still be recognized from the way the runtime calls it, but the internal functions lose their names entirely. You lose the internal function names, and keep the logic, the constants and the instruction structure. Stripping slows you down because you have to rename things yourself, but it doesn't hide the behavior.

Putting it together, `-O2` inlines, unrolls, strength-reduces and interleaves instructions, so it's much harder to read than `-O0`. Small functions get inlined and vanish as separate functions, fixed-count loops can be computed ahead of time into a constant, and multiplication or division by a constant turns into shifts or an `imul` with a magic number that you shouldn't misread. Stripping loses internal names but not logic. Real release software is almost always `-O2` and stripped, so expect both layers of difficulty. Renaming functions early (Lesson 0.4) and recognizing optimizer patterns is how you get through.

</details>

## Key takeaways
Compilation has four stages, which are preprocessor, compiler, assembler, linker, and macros disappear at stage one. Dynamic linking exposes imports, which are very useful clues during triage, while static linking copies library code inside and makes things harder. At runtime the loader maps sections, loads DLLs, fills the IAT and handles relocations, so "on disk" differs from "in memory".

The optimizer is the main reason code gets hard to read, through inlining, loop unrolling, strength reduction, and lost intermediate variables. Weird decompiled code usually comes from `-O2`, not the author, and when building your own binaries to learn you should use `-O0`. A stripped file has lost all internal function names, and having a PDB/DWARF alongside is a big help.
