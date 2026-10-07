---
title: "Lesson 14.4: Code-level obfuscation, when the program flow gets bent"
image:
  path: /assets/img/covers/re-14-4-code-level-obfuscation-when-program-flow.webp
  alt: "Lesson 14.4: Code-level obfuscation, when the program flow gets bent"
date: 2023-04-30 10:27:00 +0700
categories: ["Technique Reverse", "Part 14 · Packers and Obfuscation"]
tags: [reverse-engineering, packer, obfuscation]
render_with_liquid: false
---
Packers hide code until runtime (lessons 14.1, 14.2). Obfuscation does something different: the code is still there, you can still disassemble it, but it has been deliberately rewritten to be hard to read. A ten-line function balloons to five hundred lines, an addition turns into a pile of bit operations, a clean if/else flow turns into an infinite loop with a giant switch. The logic doesn't change, only the shape.

This lesson goes over the most common techniques, how to recognize each one, and more importantly the general strategy for not being scared off by them. Most of these come from OLLVM (Obfuscator-LLVM), an open-source set of LLVM passes that a lot of commercial protectors and malware reuse.

## Control flow flattening, the number one troublemaker

This is the technique you'll meet most and the most frustrating one. The idea: take the function's natural flow (block A finishes and goes to B, B branches to C or D) and flatten it all. Every basic block becomes a `case` in one big `switch`, and a state variable decides which case runs next. All of it sits inside a `while(1)` loop.

On IDA's graph view, a normal function looks like a tree flowing downward. A flattened function looks like a spider: one dispatcher in the middle, every block returns to the dispatcher and fans out again. The original if/for/while structure disappears completely, because the order of execution is now driven by the state variable and not by instruction position.

Let's look at a concrete case. The original function checks a serial:

```c
int check(const char *s) {
    int len = strlen(s);
    if (len != 8) return 0;
    if (s[0] != 'R') return 0;
    int sum = 0;
    for (int i = 0; i < len; i++) sum += s[i];
    if (sum % 7 != 0) return 0;
    return 1;
}
```

After flattening (this is the `flattened.c` file in the lab, written by hand so the shape is easy to see):

```c
int check(const char *s) {
    int state = 0, len = 0, sum = 0, i = 0, ret = 0;
    while (1) {
        switch (state) {
            case 0:  len = strlen(s); state = 1; break;
            case 1:  if (len != 8) { ret = 0; state = 99; } else state = 2; break;
            case 2:  if (s[0] != 'R') { ret = 0; state = 99; } else { sum = 0; i = 0; state = 3; } break;
            case 3:  if (i < len) state = 4; else state = 5; break;   // loop condition
            case 4:  sum += s[i]; i++; state = 3; break;              // loop body
            case 5:  if (sum % 7 != 0) { ret = 0; state = 99; } else { ret = 1; state = 99; } break;
            case 99: return ret;
        }
    }
}
```

The two versions give identical results (the lab checked this by building both and comparing on many inputs). But the second one has lost all its original shape. To understand it, you have to do by hand what the state variable is doing: follow where state jumps. case 0 sets state=1, case 1 sets state=2 if it passes, case 2 jumps into the loop of case 3 and 4, then on to case 5. Rebuild the chain of states and you've rebuilt the original flow.

You recognize it right away from the "spider" graph and a variable that gets assigned constants over and over and is compared at the top of the loop. That's the state variable. For small functions, tracing state by hand as above is enough. For big functions, use the automated tools in lesson 14.6 (D-810, Miasm, emulation) to rebuild the original CFG. Or skip static and go dynamic: set breakpoints and see which order the cases actually run in with your input.

## Opaque predicate, branches that never run

An opaque predicate is a condition whose result the obfuscator knows for sure (always true or always false), but the compiler and decompiler don't. The classic example: `if ((x*x + x) % 2 == 0)`. The product of two consecutive numbers is always even, so this condition is always true, and the else branch is dead code that's only there to add noise.

The result is a graph full of fake branches, and you waste effort reading code that never runs. You spot it by noticing weird arithmetic conditions on a variable whose value is actually fixed. Symbolic execution tools (angr, Triton in Part 18) or an SMT solver can prove the predicate is constant, and then you cut the dead branch.

## Mixed Boolean-Arithmetic, addition in armor

MBA turns a simple operation into an equivalent but eye-straining expression, mixing arithmetic with bit operations. For example `x + y` can become `(x ^ y) + 2*(x & y)`, or worse a whole chain of `|`, `&`, `^`, `~`, shifts a dozen lines long. Mathematically they're equal, but looking at it you can't guess it's adding.

You recognize MBA when you see a block made entirely of bit operations with no clear purpose, over the same few variables. To deal with it, use an expression simplifier (Miasm, Triton has a simplifier, or dedicated MBA solvers), or emulate that piece with a few values to work out what it actually computes.

## String encryption

Strings are the reverser's most valuable clue (lesson 0.4), so obfuscators encrypt all of them. Instead of "Invalid license" sitting in `.rdata`, you see a meaningless byte array and a decryption function called right before the string is used. The decryption is usually very light: XOR with a key, or adding/subtracting a constant.

The most effective approach is dynamic: set a breakpoint after the decryption function call and read the clear string in memory. Or if the algorithm is simple, rewrite it in Python to decrypt in bulk (that's exactly Part 16). Mandiant's FLOSS automates most of this.

## Junk code, dead code, instruction substitution

Three small techniques often come along. Junk or dead code inserts meaningless instructions (disguised nops, computing something and throwing the result away) to dilute things, and you can ignore it once you see it doesn't affect the output. Instruction substitution replaces one instruction with an equivalent sequence (e.g. `a = b - c` becomes `a = b + (-c)` over several steps), and a good decompiler usually merges these back for you. Anti-disassembly junk bytes are a topic for lesson 15.6, a bit different because they attack the disassembler and not the reader.

## General strategy when you meet obfuscation

Don't try to read an obfuscated function linearly, you'll drown. Instead, first identify which technique you're facing: flattening has the spider shape, MBA has bit-operation blocks, and string encryption has a decryption function before every string.

Then prefer dynamic over static. Obfuscation makes static reading hard, but at runtime the program still has to do the right thing. A breakpoint in the right place shows you real values, decrypted strings, and the branch that actually runs. Focus on the input and output of the code and don't get lost in individual instructions. For a long MBA block, knowing "it adds these two numbers" is enough. At scale, automate with emulation and symbolic execution (Part 18), or dedicated deobfuscation tools (lesson 14.6).

The key point is that obfuscation costs you time, it doesn't make things impossible. The logic still has to run correctly, so there's always a dynamic route to see the truth.

## Lab

The goal is to see a control-flow-flattened function with your own eyes and practice rebuilding the original flow. There are two files: `original.c`, a `check` function written normally with a clear flow, and `flattened.c`, the same logic manually flattened into `while(1)` plus `switch(state)`. Build both:

```
gcc -O0 -o original original.c
gcc -O0 -o flattened flattened.c
```

Run both with a few different serials and confirm they always give the same result (`Correct!` or `Nope.`), which is the proof that flattening doesn't change the logic. Then look only at `flattened.c`, pretending you haven't seen the original, find the dispatcher variable (state) and build a table of what each case does and what it sets the next state to. From that table, redraw the original flow and work out the three conditions the serial must satisfy, then find a valid serial that meets all three. Open `flattened` in Ghidra or IDA, look at the graph view of the `check` function and compare its shape with `original`, noticing the spider shape. As an advanced step, build optimized versions with `gcc -O2` for both and see how much the decompiler merges back.

Two questions to reflect on. Why does control flow flattening confuse the decompiler but not break the program? And if the function had 200 cases instead of 7, how would your strategy change (hint: lesson 14.6, and emulation and symbolic execution in Part 18)? Try it yourself before opening the solution.

<div class="lab-box">
<div class="lab-head"><b>LAB 14.4</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/14.4/src/flattened.c" download><i class="fa-solid fa-file-code"></i>src/flattened.c</a>
<a class="lab-file" href="/assets/labs/14.4/src/original.c" download><i class="fa-solid fa-file-code"></i>src/original.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Tracing each case of `flattened.c` and its next state gives the dispatcher table:

| state | what it does | next state |
|---|---|---|
| 0 | len = strlen(s) | 1 |
| 1 | if len != 8: ret=0, go to 99; otherwise go to 2 | 2 or 99 |
| 2 | if s[0] != 'R': ret=0, go to 99; otherwise sum=0, i=0, go to 3 | 3 or 99 |
| 3 | if i < len: go to 4; otherwise go to 5 (this is the loop condition) | 4 or 5 |
| 4 | sum += s[i]; i++; back to 3 (the loop body) | 3 |
| 5 | if sum % 7 != 0: ret=0; otherwise ret=1; go to 99 | 99 |
| 99 | return ret | (exit) |

Putting the table together rebuilds the original flow: compute `len = strlen(s)`, return 0 if `len != 8`, return 0 if `s[0] != 'R'`, loop `for (i = 0; i < len; i++) sum += s[i]` (case 3 is the condition and case 4 is the body), return 0 if `sum % 7 != 0`, and otherwise return 1. That is identical to `original.c`. Case 3 and case 4 together form the `for` loop, which is where beginners often slip: a loop after flattening splits into two cases, one checking the condition and one running the body, pointing at each other.

So a valid serial must satisfy three conditions. Its length is exactly 8, its first character is 'R', and the sum of the ASCII codes of its 8 characters is divisible by 7.

A valid serial, built with `gcc -O0`:

```
./original Reversa1   -> Correct!
./flattened Reversa1  -> Correct!
```

Some other valid serials of the same family are `Reversa8`, `Reversb7`, `Reversc6` and `Reversd5`. All have length 8, start with 'R', and have an ASCII sum divisible by 7. In the real runs, both binaries gave identical results on every input I tried: Reverse1, R1234567, Raaaaaaa, hello and Rabcdefg were Nope in both, and Reversa1 was Correct in both.

One caveat: the flattened version here was written by hand to match the shape that OLLVM `-fla` produces, so it is not real OLLVM output. The logic and the dispatcher structure are the same as what you will meet when you unpack OLLVM.

</details>

## Key takeaways
Control flow flattening is while(1) + switch(state) with a spider-shaped graph, and you rebuild the flow by tracing the state variable. An opaque predicate is an always-true/false condition that creates dead branches, and you cut it with symbolic execution. MBA is a simple operation wearing bit operations, undone with a simplifier or by emulating. For string encryption, set a breakpoint after the decryption function to read the real string. OLLVM is the common source of flattening, substitution and bogus control flow.

The golden rule is to prefer dynamic over static, focus on input/output, and automate when it's big (lesson 14.6).
