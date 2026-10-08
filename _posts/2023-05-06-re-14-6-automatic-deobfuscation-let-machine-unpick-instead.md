---
title: "Lesson 14.6: Automatic deobfuscation"
image:
  path: /assets/img/covers/re-14-6-automatic-deobfuscation-let-machine-unpick-instead.webp
  alt: "Lesson 14.6: Automatic deobfuscation"
date: 2022-07-12 07:01:00 +0700
categories: ["Reverse Engineering", "Part 14 · Packers and Obfuscation"]
tags: [reverse-engineering, packer, obfuscation]
render_with_liquid: false
---
Lesson [14.4](/posts/re-14-4-code-level-obfuscation-when-program-flow/) showed what obfuscation looks like. Control flow flattening turns a tidy function into a giant dispatcher, MBA turns `x + y` into a long bit expression, opaque predicates scatter dead branches everywhere. Undoing each one by hand is doable, but with a binary of a few thousand obfuscated functions you'll give up before finishing the third. This lesson is about getting tools to do the heavy lifting.

![Lift, simplify and lower in automatic deobfuscation](/assets/img/re/re-14-6-automatic-deobfuscation-let-machine-unpick-instead.svg)
_Tools lift code to an IR, simplify it, and lower it back, each working at a different layer._

Every automatic deobfuscation tool follows the same idea, which is to lift the code to a cleaner intermediate form (IR), simplify it there with algebraic rules or a solver, then lower it back down. They differ in which layer they work at and how much they can handle.

## Why work on IR and not on assembly

x86 assembly is messy to transform automatically, since the same operation can be written a dozen ways, status flags change implicitly, instruction lengths vary. If you write simplification rules directly on assembly, you drown in special cases.

So tools lift the assembly to an Intermediate Representation, which is a small, regular language where each instruction does exactly one thing, with no hidden side effects. On IR, `x + y` is always `x + y`, and an MBA expression equivalent to `x + y` can be simplified back to `x + y` with algebraic laws. When done, lower it back to a readable form, or feed it straight into the decompiler.

Hex-Rays calls its IR microcode. Ghidra calls it P-Code. Binary Ninja has the multi-level BNIL. Each deobfuscation tool hooks into one of those IRs.

## D-810, inside Hex-Rays

If you use IDA Pro with Hex-Rays, D-810 is the first thing to know. It's a plugin that hooks into the microcode layer. While the decompiler is building pseudocode, D-810 steps in, recognizes familiar obfuscation patterns and rewrites the microcode before you see the result.

It's good at three things. It recognizes MBA (Mixed Boolean-Arithmetic) expressions and reduces them back to the original operation. It detects opaque predicates, meaning conditions that are always true or always false, and cuts the dead branch. And it undoes control flow flattening by rebuilding the original flow from the dispatcher, giving normal if/else/loops back.

You don't have to run a separate step and import the result. Install the right rules, press F5, and the pseudocode shows up already clean. The weakness is that it follows rules, so when it meets an obfuscation variant the rules don't know, it's stuck, and you have to write more rules yourself (D-810 allows that) or change approach.

## HexRaysDeob and the microcode plugin line

Before D-810 there was Rolf Rolles' HexRaysDeob, also working at the microcode layer and one of the first demonstrations that Hex-Rays microcode is open enough to automatically undo obfuscation. It targeted some specific protectors (famous for samples from a malware family of that time). D-810 is more popular now, but Rolles' microcode series is still the best way to understand the mechanism underneath instead of just pressing buttons.

What they have in common is that they fix the problem during decompilation, so the result goes straight into the pseudocode.

## Miasm

Miasm isn't a plugin for a decompiler, it's a whole Python framework that lifts many architectures to its own IR, can emulate, has a symbolic execution engine, and an expression simplifier. Since it's a library, you program the unpicking workflow yourself.

A typical usage is to lift an obfuscated function to Miasm's IR, run symbolic execution over it, get the symbolic expression of the output in terms of the input, then let the simplifier reduce it. Flattening goes away because symbolic execution follows the real flow regardless of the dispatcher, and MBA goes away because the simplifier knows the laws. You have to write code, but you get full control and don't depend on ready-made rules.

A few other directions are worth knowing by name, namely gtirb (GrammaTech's rewriting-style IR) for rewriting binaries, and Souper (a solver-based superoptimizer) for finding shorter equivalent expressions. You rarely need them when starting out, but it's good to know D-810 isn't the only option.

## Symbolic execution

This is the most general approach, and also the bridge to [Part 18](/reverse-engineering/). Tools like Triton or angr treat the input as symbolic variables, run through the code, and instead of computing a number they compute a formula. There are two direct uses for deobfuscation.

One is simplifying MBA, where you have Triton build the symbolic expression of an MBA chunk, then use the simplifier or Z3 to prove it's equivalent to a short expression. In practice an MBA expression of thirty bit operations often reduces to `a ^ b` or `a + b`. The other is undoing flattening, where symbolic/concolic execution follows the real execution flow, joining the original blocks in the order they actually run, skipping the dispatcher, and from that trace you rebuild a clean CFG.

Triton is compact and can be embedded in other tools. angr is heavier but comes with CFG recovery and lots of utilities. Symbolic execution itself is covered in [Lesson 18.3](/reverse-engineering/).

## Automatic or by hand

Obfuscation doesn't mean you have to build a whole symbolic pipeline. Weigh the effort against what you get back:

| Situation | What to do |
|---|---|
| One function, one small MBA spot | Reduce it by hand, faster than building a tool |
| Many functions with the same kind of obfuscation | D-810 with the right rules, or write one rule and apply it in bulk |
| Heavy flattening, many functions | D-810 or a Miasm/symbolic script |
| Unfamiliar obfuscation, no rules yet | Miasm or Triton, write your own unpicking logic |
| You only need to know what a function returns for a given input | Emulate (Unicorn/Qiling), no need to unpick |

People often forget that a lot of the time you don't need to undo any obfuscation. If the question is just "for which serial does this check function return true", you can emulate it or let symbolic execution solve it backwards, however tangled the inside flow is. Deobfuscating to read is one goal and finding the answer is another, and the second is often much cheaper.

## Lab

The goal is to see a tool (or yourself) turn an obfuscated expression back into a readable original form. Ideally you have IDA Pro with Hex-Rays and the [D-810](https://gitlab.com/eshard/d810) plugin, or [Miasm](https://github.com/cea-sec/miasm). Without them you can still do the MBA reduction by hand with pen and paper or Python.

Start with a hand reduction, no tool needed. Here is an MBA expression built to be equivalent to a simple operation:

```
f(a, b) = (a ^ b) + 2 * (a & b)
```

Prove it equals a familiar operation. As a hint, think about how `a + b` splits into an "add without carry" part and a "carry" part. Check it in Python:

```python
import random
for _ in range(10000):
    a = random.randint(0, 2**32-1)
    b = random.randint(0, 2**32-1)
    assert ((a ^ b) + 2*(a & b)) & 0xFFFFFFFF == (a + b) & 0xFFFFFFFF
print("f(a,b) == a + b")
```

Then try a harder one, `g(a, b) = (a | b) - (a & b)`. Reduce it and check it in Python the same way. The hint is that the result is a single bitwise operator.

If you have the tools, use them. With D-810, open a binary that contains MBA (build one with tigress or OLLVM, or take an MBA crackme), turn on the MBA rules, press F5, and compare the pseudocode before and after enabling the plugin. With Miasm, lift a small function, run symbolic execution, print the output expression and call the simplifier, comparing the raw expression with the reduced one.

Finally, think about when you don't need to unpick anything. Consider a heavily flattened function `check(serial)`. Instead of undoing the flow, you could emulate it or use symbolic execution to find a valid serial without understanding the dispatcher. Write a paragraph describing how you would do it (tool details are in Part 18).

Two questions to think about. Why is simplifying MBA on an IR easier than on raw assembly? And D-810 works by rules, so what happens when it meets an MBA variant that no rule knows, and how does symbolic execution differ?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Try it yourself before reading.

For the first expression, `f(a, b) = (a ^ b) + 2 * (a & b)` equals `a + b`. Binary addition splits into two parts. `a ^ b` is the per-bit sum that ignores carries (add without carry). `a & b` marks the positions that generate a carry, and the carry is added into the next column, meaning a left shift by 1 bit, so `2 * (a & b)` is exactly `(a & b) << 1`. Adding the two parts gives the full addition `a + b`. This is the classic MBA identity that obfuscators use to hide a plain `+`. I checked 100000 random 32-bit pairs, and `((a^b)+2*(a&b)) & 0xFFFFFFFF == (a+b) & 0xFFFFFFFF` held for all of them.

For the second, `g(a, b) = (a | b) - (a & b)` equals `a ^ b`. `a | b` contains every bit set in at least one operand. It splits into two disjoint groups, bits set on only one side (`a ^ b`) and bits set on both (`a & b`). Because the two groups don't overlap, `a | b = (a ^ b) + (a & b)`. Subtracting `a & b` leaves `a ^ b`. Again I checked 100000 random 32-bit pairs, and `((a|b)-(a&b)) & 0xFFFFFFFF == (a^b) & 0xFFFFFFFF` held for all of them. This is what MBA looks like, which is an expression that looks complicated but is always equal to a single simple operation. Tools like D-810 or Miasm's simplifier know a library of such identities and apply them automatically.

For the tools, the typical workflow (described here, the concrete result depends on the sample you use) goes like this. With D-810, before enabling the plugin, the Hex-Rays pseudocode of the MBA function shows a long chain of `^`, `&`, `|`, `+` and `<<` operations. After turning on the MBA rules and pressing F5 again, the same function reduces to `return a + b;` or similar, because the plugin rewrites at the microcode level so the decompiler prints the cleaned version. With Miasm, after lifting and running symbolic execution the raw output expression looks like `((a ^ b) + ((a & b) << 1))`, and calling `expr.simplify()` (or Miasm's simplifier) reduces it to `a + b`.

For when you don't need to unpick anything, take a heavily flattened `check(serial)`. Instead of recovering the flow, you can emulate it with Unicorn or Qiling. Load the function, try many serials and see which make it return true. That works well when the serial space is small or structured. Or you can use symbolic execution with angr or Triton. Make the serial a symbolic variable and ask the solver for a value that makes the function return true, without reading a single line of the dispatcher. Both answer "which serial is valid" while ignoring the tangled flow. Details are in Lessons 18.2 (emulation) and 18.3 (symbolic execution).

On the questions, simplifying on an IR is easier because an IR is regular, with one effect per instruction, no implicitly changing status flags and no multiple ways of writing the same operation. That lets you apply algebraic rules without handling many x86 special cases. D-810 matches patterns by rule, so when it meets an MBA with no rule it can't reduce it and you have to add a rule yourself. Symbolic execution doesn't rely on patterns. It computes the symbolic expression and lets a solver prove equivalence, so it can handle variants it has never seen, at the cost of running slower and heavier.

</details>

## Key takeaways
All automatic deobfuscation follows one formula, which is to lift to IR, simplify, lower back down. D-810 works inside Hex-Rays microcode and is good on MBA, opaque predicates and flattening, though it is rule-based. HexRaysDeob is the predecessor, and Rolf Rolles' series is the one to read to understand microcode. Miasm is a full Python framework (IR, emulation, symbolic, simplify) where you program the workflow yourself, and symbolic execution (Triton, angr) works for both MBA and flattening, with details in Part 18. Pick by scale. Do a small spot by hand and only build a tool for bulk work, and sometimes you can just emulate to get the answer with no unpicking.
