---
title: "Lesson 14.6: Automatic deobfuscation, let the machine unpick it instead of grinding by hand"
date: 2026-10-06 09:25:00 +0700
categories: ["Technique Reverse", "Part 14 · Packers and Obfuscation"]
tags: [reverse-engineering, packer, obfuscation]
render_with_liquid: false
---
Lesson [14.4](/posts/tr-14-4-obfuscation-ky-thuat/) showed you what obfuscation looks like: control flow flattening turns a tidy function into a giant dispatcher, MBA turns `x + y` into a long bit expression, opaque predicates scatter dead branches everywhere. Undoing each one by hand is doable, but with a binary of a few thousand obfuscated functions you'll give up before finishing the third. This lesson is about getting tools to do the heavy lifting.

The common idea behind every automatic deobfuscation tool fits in one sentence: **lift the code to a cleaner intermediate form (IR), simplify on it with algebraic rules or a solver, then lower it back down.** They only differ in which layer they work at and how powerful they are.

## Why work on IR and not on assembly

x86 assembly is very messy to transform automatically: the same operation has a dozen ways of being written, status flags change implicitly, instruction lengths vary. If you try to write simplification rules directly on assembly, you drown in special cases.

So tools lift the assembly to an Intermediate Representation: a small, regular language where each instruction does exactly one thing, with no hidden side effects. On IR, `x + y` is always `x + y`, and an MBA expression equivalent to `x + y` can be simplified back to exactly `x + y` with algebraic laws. When done, lower it back to a readable form, or feed it straight into the decompiler.

Hex-Rays calls its IR microcode. Ghidra calls it P-Code. Binary Ninja has the multi-level BNIL. Each deobfuscation tool hooks into one of those IRs.

## D-810, unpicking right inside Hex-Rays

If you use IDA Pro with Hex-Rays, D-810 is the first thing to know. It's a plugin that hooks into the microcode layer: while the decompiler is building pseudocode, D-810 steps in, recognizes familiar obfuscation patterns and rewrites the microcode before you see the result.

It's strongest at three things:
- **MBA**: recognizes and reduces Mixed Boolean-Arithmetic expressions back to the original operation.
- **Opaque predicates**: detects conditions that are always true or always false and cuts the dead branch.
- **Control flow flattening**: rebuilds the original flow from the dispatcher, returning normal if/else/loops.

The nice part is you don't have to run a separate step and import the result. Install the right rules, press F5, and the pseudocode shows up already clean. The weakness: it follows rules, so when it meets an obfuscation variant the rules don't know, it's stuck, and you have to write more rules yourself (D-810 allows that) or change approach.

## HexRaysDeob and the microcode plugin line

Before D-810 there was Rolf Rolles' HexRaysDeob, also working at the microcode layer and one of the first demonstrations that Hex-Rays microcode is open enough to automatically undo obfuscation. It targeted some specific protectors (famous for samples from a malware family of that time). D-810 is more popular now, but rereading Rolles' microcode series is still the best way to understand the mechanism underneath, instead of just pressing buttons.

What they have in common: they treat the symptom right where it's produced, during decompilation, so the result goes straight into the pseudocode.

## Miasm, when you need a full toolkit

Miasm isn't a plugin for a decompiler, it's a whole Python framework: it lifts many architectures to its own IR, can emulate, has a symbolic execution engine, and an expression simplifier. Since it's a library, you program the unpicking workflow yourself.

A typical usage: lift an obfuscated function to Miasm's IR, run symbolic execution over it, get the symbolic expression of the output in terms of the input, then let the simplifier reduce it. Flattening melts away because symbolic execution follows the real flow regardless of the dispatcher; MBA melts away because the simplifier knows the laws. The price is that you have to write code, but in return you get full control and don't depend on ready-made rules.

Of the same family of thinking there are a few other directions worth knowing by name: **gtirb** (GrammaTech's rewriting-style IR) for rewriting binaries, and **Souper** (a solver-based superoptimizer) for finding shorter equivalent expressions. You rarely need them when you're starting out, but knowing they exist keeps you from thinking D-810 is the only option.

## Symbolic execution, the common weapon for MBA and flattening

This is the most general approach, and also the bridge to [Part 18](https://github.com/Haind03/Technique-Reverse/tree/main/phan-18-nang-cao). Tools like Triton or angr treat the input as symbolic variables, run through the code, and instead of computing a number they compute a formula. Two direct uses for deobfuscation:

- **Simplifying MBA**: have Triton build the symbolic expression of an MBA chunk, then use the simplifier or Z3 to prove it's equivalent to a short expression. In practice an MBA expression of thirty bit operations often reduces to `a ^ b` or `a + b`.
- **Undoing flattening**: symbolic/concolic execution follows the real execution flow, joining the original blocks in the order they actually run, skipping the dispatcher. From that trace you rebuild a clean CFG.

Triton is compact and can be embedded in other tools; angr is heavier but comes with CFG recovery and lots of utilities. The details of symbolic execution are saved for [Lesson 18.3](https://github.com/Haind03/Technique-Reverse/tree/main/phan-18-nang-cao).

## Automatic or by hand: choose by scale

Don't assume obfuscation means building a whole symbolic pipeline. Weigh the effort you put in against what you get back:

| Situation | What to do |
|---|---|
| One function, one small MBA spot | Reduce it by hand, faster than building a tool |
| Many functions with the same kind of obfuscation | D-810 with the right rules, or write one rule and apply it in bulk |
| Heavy flattening, many functions | D-810 or a Miasm/symbolic script |
| Unfamiliar obfuscation, no rules yet | Miasm or Triton, write your own unpicking logic |
| You only need to know what a function returns for a given input | Emulate (Unicorn/Qiling), no need to unpick |

A tip that's often forgotten: a lot of the time you don't need to undo any obfuscation at all. If the question is just "for which serial does this check function return true", simply emulate or let symbolic execution solve it backwards, never mind how tangled the inside flow is. Deobfuscating to read is one goal; finding the answer is another, and the second is often much cheaper.

## Lab

See [labs/14.6/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/14.6). You'll take a function with MBA or opaque predicates, use D-810 or Miasm to simplify it, and compare the pseudocode before and after. If you can't install the tools yet, the lab has a sample MBA expression for you to reduce by hand, enough to see with your own eyes a monstrous expression collapse into a single XOR.

## Key takeaways
- All automatic deobfuscation follows one formula: lift to IR, simplify, lower back down.
- D-810 unpicks right inside Hex-Rays microcode, strong on MBA, opaque predicates, flattening; rule-based.
- HexRaysDeob is the predecessor, read Rolf Rolles' series to understand microcode.
- Miasm is a full Python framework (IR, emulation, symbolic, simplify), you program the workflow yourself.
- Symbolic execution (Triton, angr) is the general weapon for both MBA and flattening, details in Part 18.
- Weigh the scale: a small spot by hand, only build a tool for bulk work. And sometimes you just emulate to get the answer, with no unpicking needed.
