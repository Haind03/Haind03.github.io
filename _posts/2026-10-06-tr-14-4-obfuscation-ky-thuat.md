---
title: "Lesson 14.4: Code-level obfuscation, when the program flow gets bent"
date: 2026-10-06 09:23:00 +0700
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

In `labs/14.4/` there are `original.c` and `flattened.c`, the same `check` function, one original and one manually control-flow-flattened. Build both, confirm they give the same results, then practice rebuilding the original flow from the flattened version alone by tracing the state variable. Details in `labs/14.4/README.md`, the solution and a valid serial in `labs/14.4/solution.md`.

## Key takeaways
Control flow flattening is while(1) + switch(state) with a spider-shaped graph, and you rebuild the flow by tracing the state variable. An opaque predicate is an always-true/false condition that creates dead branches, and you cut it with symbolic execution. MBA is a simple operation wearing bit operations, undone with a simplifier or by emulating. For string encryption, set a breakpoint after the decryption function to read the real string. OLLVM is the common source of flattening, substitution and bogus control flow.

The golden rule is to prefer dynamic over static, focus on input/output, and automate when it's big (lesson 14.6).
