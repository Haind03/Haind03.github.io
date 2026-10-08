---
title: "Lesson 14.4: Code-level obfuscation"
image:
  path: /assets/img/covers/re-14-4-code-level-obfuscation-when-program-flow.webp
  alt: "Lesson 14.4: Code-level obfuscation"
date: 2023-04-30 10:27:00 +0700
categories: ["Reverse Engineering", "Part 14 · Packers and Obfuscation"]
tags: [reverse-engineering, packer, obfuscation]
render_with_liquid: false
---
Packers hide code until runtime (lessons 14.1, 14.2). Obfuscation is different. The code is still there and you can disassemble it, but it's been rewritten on purpose to be hard to read. A ten-line function grows to five hundred lines, an addition becomes many bit operations, and a clean if/else flow becomes an infinite loop with a giant switch. The logic stays the same, only the shape changes.

This lesson covers the most common techniques, how to recognize each one, and a general strategy for dealing with them. Most come from OLLVM (Obfuscator-LLVM), an open-source set of LLVM passes that a lot of commercial protectors and malware reuse.

## Control flow flattening

This is the one you'll meet most, and it's the most annoying. The idea is to take the function's natural flow (block A finishes and goes to B, B branches to C or D) and flatten it. Every basic block becomes a `case` in one big `switch`, and a state variable decides which case runs next. All of it sits inside a `while(1)` loop.

In IDA's graph view a normal function looks like a tree flowing downward. A flattened function has one dispatcher in the middle, and every block returns to the dispatcher and branches out again. The original if/for/while structure is gone, because the order of execution is now driven by the state variable and not by instruction position.

Here's a concrete case. The original function checks a serial:

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

Both versions give identical results (the lab checked this by building both and comparing on many inputs). But the second one has lost its original shape. To understand it, you have to do by hand what the state variable does and follow where state jumps. case 0 sets state=1, case 1 sets state=2 if it passes, case 2 jumps into the loop of case 3 and 4, then on to case 5. Rebuild the chain of states and you've rebuilt the original flow.

You recognize it from the spider graph and from a variable that gets assigned constants over and over and is compared at the top of the loop. That's the state variable. For small functions, tracing state by hand like above is enough. For big functions, use the automated tools in lesson 14.6 (D-810, Miasm, emulation) to rebuild the original CFG. Or skip static analysis and go dynamic by setting breakpoints and see in which order the cases actually run with your input.

## Opaque predicates

An opaque predicate is a condition whose result the obfuscator knows for sure (always true or always false), but the compiler and decompiler don't. The classic example is `if ((x*x + x) % 2 == 0)`. The product of two consecutive numbers is always even, so this is always true, and the else branch is dead code that only adds noise.

You end up with a graph full of fake branches, and time wasted on code that never runs. You spot it by weird arithmetic conditions on a variable whose value is actually fixed. Symbolic execution tools (angr, Triton in Part 18) or an SMT solver can prove the predicate is constant, and then you cut the dead branch.

## Mixed Boolean-Arithmetic

MBA turns a simple operation into an equivalent but ugly expression that mixes arithmetic with bit operations. For example `x + y` can become `(x ^ y) + 2*(x & y)`, or worse, a chain of `|`, `&`, `^`, `~` and shifts a dozen lines long. Mathematically they're equal, but looking at it you can't tell it's an addition.

You recognize MBA by a block made only of bit operations with no clear purpose, over the same few variables. To deal with it, use an expression simplifier (Miasm, Triton has a simplifier, or dedicated MBA solvers), or emulate that piece with a few values to see what it computes.

## String encryption

Strings are the reverser's most useful clue (lesson 0.4), so obfuscators encrypt all of them. Instead of "Invalid license" sitting in `.rdata`, you see a meaningless byte array and a decryption function called right before the string is used. The decryption is usually simple, such as XOR with a key, or adding or subtracting a constant.

The most effective approach is dynamic, which means setting a breakpoint after the decryption call and read the clear string in memory. If the algorithm is simple, you can also rewrite it in Python to decrypt in bulk (that's Part 16). Mandiant's FLOSS automates most of this.

## Junk code, dead code, instruction substitution

Three smaller techniques often come along. Junk or dead code inserts meaningless instructions (disguised nops, computing something and throwing the result away) to dilute the code, and you can ignore it once you see it doesn't affect the output. Instruction substitution replaces one instruction with an equivalent sequence (e.g. `a = b - c` becomes `a = b + (-c)` over several steps), and a good decompiler usually merges these back for you. Anti-disassembly junk bytes are in lesson 15.6. They're a bit different because they attack the disassembler and not the reader.

## General strategy

Don't try to read an obfuscated function linearly, you'll get lost. First identify which technique you're facing, since flattening has the spider shape, MBA has bit-operation blocks, and string encryption has a decryption function before every string.

Then I prefer dynamic over static. Obfuscation makes static reading hard, but at runtime the program still has to do the right thing. A breakpoint in the right place shows you real values, decrypted strings and the branch that actually runs. Focus on the input and output of the code and not on individual instructions. For a long MBA block, knowing it adds these two numbers is enough. At scale, automate with emulation and symbolic execution (Part 18), or dedicated deobfuscation tools (lesson 14.6).

Obfuscation costs you time, it doesn't make things impossible. The logic still has to run correctly, so there's always a dynamic route to see what it does.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 14.4</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/14.4.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/14.4/src/flattened.c" download><i class="fa-solid fa-download"></i>src/flattened.c</a>
<a class="lab-file" href="/assets/labs/14.4/src/original.c" download><i class="fa-solid fa-download"></i>src/original.c</a>
</div>
</div>

The goal is to see a control-flow-flattened function yourself and practice rebuilding the original flow. There are two files, `original.c`, a `check` function written normally with a clear flow, and `flattened.c`, the same logic manually flattened into `while(1)` plus `switch(state)`. Build both:

```
gcc -O0 -o original original.c
gcc -O0 -o flattened flattened.c
```

Run both with a few different serials and confirm they always give the same result (`Correct!` or `Nope.`), which shows that flattening doesn't change the logic. Then look only at `flattened.c`, pretending you haven't seen the original. Find the dispatcher variable (state) and build a table of what each case does and what it sets the next state to. From that table, redraw the original flow and work out the three conditions the serial must satisfy, then find a valid serial that meets all three. Open `flattened` in Ghidra or IDA, look at the graph view of the `check` function and compare its shape with `original`, noticing the spider shape. As an advanced step, build optimized versions with `gcc -O2` for both and see how much the decompiler merges back.

Two questions to think about. Why does control flow flattening confuse the decompiler but not break the program? And if the function had 200 cases instead of 7, how would your strategy change (the hint is lesson 14.6, and emulation and symbolic execution in Part 18)? Try it yourself before opening the solution.

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

Putting the table together rebuilds the original flow, which is to compute `len = strlen(s)`, return 0 if `len != 8`, return 0 if `s[0] != 'R'`, loop `for (i = 0; i < len; i++) sum += s[i]` (case 3 is the condition and case 4 is the body), return 0 if `sum % 7 != 0`, and otherwise return 1. That's identical to `original.c`. Case 3 and case 4 together form the `for` loop, which is where beginners often slip, since a loop after flattening splits into two cases, one checking the condition and one running the body, pointing at each other.

So a valid serial must satisfy three conditions. Its length is exactly 8, its first character is 'R', and the sum of the ASCII codes of its 8 characters is divisible by 7.

A valid serial, built with `gcc -O0`:

```
./original Reversa1   -> Correct!
./flattened Reversa1  -> Correct!
```

Some other valid serials of the same family are `Reversa8`, `Reversb7`, `Reversc6` and `Reversd5`. All have length 8, start with 'R', and have an ASCII sum divisible by 7. In the real runs, both binaries gave identical results on every input I tried, and Reverse1, R1234567, Raaaaaaa, hello and Rabcdefg were Nope in both, and Reversa1 was Correct in both.

One caveat is that the flattened version here was written by hand to match the shape that OLLVM `-fla` produces, so it isn't real OLLVM output. The logic and the dispatcher structure are the same as what you'll meet when you unpack OLLVM.

</details>

## Key takeaways
Control flow flattening is while(1) + switch(state) with a spider-shaped graph, and you rebuild the flow by tracing the state variable. An opaque predicate is an always-true or always-false condition that creates dead branches, and you cut it with symbolic execution. MBA is a simple operation written with bit operations, undone with a simplifier or by emulating. For string encryption, set a breakpoint after the decryption function to read the real string. OLLVM is the common source of flattening, substitution and bogus control flow.

In general, prefer dynamic over static, focus on input and output, and automate when it's big (lesson 14.6).
