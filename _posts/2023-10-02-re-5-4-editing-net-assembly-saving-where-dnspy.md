---
title: "Lesson 5.4: Editing a .NET assembly and saving it, where dnSpy shines"
date: 2023-10-02 14:57:00 +0700
categories: ["Technique Reverse", "Part 05 · C# and .NET"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
With native, patching a program means fumbling around changing opcode bytes one by one, watching that you don't shift addresses, then rebuilding. With .NET it's a world of difference: dnSpy lets you edit the C# code directly, hit recompile, save the file, done. It sounds like cheating, but it's a natural consequence of .NET assemblies carrying full metadata (see [Lesson 5.1](/posts/re-5-1-net-internals-why-decompiling-gives-back/)). This lesson is the harvest.

We'll patch at two levels: the C# level (easiest, but not always possible) and the IL level (always works, and the real skill of a .NET reverser).

## Why patching .NET is cleaner than native

When you edit a native function, you have to fit the new code into exactly the old number of bytes (or find a code cave), because shifting everything behind it breaks every absolute address and offset. That's why people often have to `nop` instead of rewriting.

IL doesn't have that constraint. Methods in .NET are located through metadata tokens and not fixed addresses, and dnSpy rewrites the whole module when saving, so it recomputes every offset and every table. You add or remove IL instructions freely, and dnSpy does the bookkeeping. In practice you can even change method signatures, add fields, change the flow, and the file still runs.

## Level 1: Edit Method, editing C# directly

This is the fastest route when the decompiler gives C# clean enough to recompile.

In dnSpy, open the assembly and find the method to change (use search or Analyze as in [Lesson 5.2](/posts/re-5-2-ilspy-dnspy-when-decompiling-gives-back/)). Right-click the method and choose **Edit Method (C#)**, and dnSpy opens a C# editing box right at that method. Edit the logic, for example a check function that returns `false` when wrong gets changed to always `return true`. Click **Compile** and dnSpy uses Roslyn to recompile the method into the assembly, then use **File > Save Module** to write it to disk.

The nice part is you work at the familiar C# level. The downside is that if the decompiler translated it wrong (common with obfuscated code, newer language features, or places dnSpy can't rebuild correctly), that C# won't compile and you're stuck. Then you have to go down to the IL level.

## Level 2: Edit IL Instructions, the most reliable

IL is the real bytecode of the method. Editing here doesn't depend on whether the decompiler translated correctly, so it always works. Serious .NET reversers are all comfortable with a handful of IL instructions, you don't need to memorize them all.

Right-click the method and choose **Edit IL Instructions**. dnSpy shows the IL instruction list and lets you edit line by line.

A few IL instructions to know, enough to patch most crackmes:

| IL | Meaning |
|---|---|
| `ldc.i4.0` / `ldc.i4.1` | Push the constant 0 / 1 (i.e. false / true) onto the stack |
| `ldc.i4 <n>` | Push the integer n |
| `ret` | Return (the return value is whatever's on top of the stack) |
| `brtrue` / `brtrue.s` | Jump if the value on the stack is nonzero (true) |
| `brfalse` / `brfalse.s` | Jump if it's zero (false) |
| `beq` / `bne.un` | Jump if equal / not equal |
| `call` / `callvirt` | Call a method |
| `nop` | Do nothing (used to delete an instruction) |
| `ceq` | Compare for equality, push the 0/1 result onto the stack |

A few classic patching tricks. You can flip a branch by changing `brtrue` to `brfalse` (and vice versa) so the "wrong" and "right" branches swap places, and one instruction flips the whole logic. You can force the return value: if the check function returns a bool, insert `ldc.i4.1` then `ret` right at the start of the method, and the function always returns `true` and never runs the logic. You can disable a call by replacing the annoying `call` (for example one that calls an anti-tamper function) with an equivalent number of `nop`s, remembering to balance the stack (if the call returns a value that's used afterwards, you have to push a fake value in its place). And you can change a comparison constant: if it compares a length against 8, change the `ldc.i4.8` constant to the value you want.

A practical tip: usually you don't need to understand the whole method. Find the exact spot where it decides right/wrong (either a `brtrue`/`brfalse` or the `ret` of a bool function), then step in right there. Least touching, least risk.

## Pitfall: strong name signature

Many assemblies are signed with a strong name. After you edit and save, the signature no longer matches the content, and if something checks it (strong name verification, or the assembly is loaded through the GAC/a host that checks), the file will be refused.

How you handle it depends on the case. If the assembly loads other assemblies itself and verifies signatures, you may have to patch that check too. For a normal assembly run directly, strong name verification has been off by default since .NET Framework 3.5 SP1 for full-trust, so it often still runs. dnSpy's Save Module has writer-related options, so if you hit a token/signature error, try unchecking keep signature, or remove the strong name and re-sign with your own key. Command-line tools like `sn.exe -Vr` (skip verification) can also be used in your own test environment.

This is where beginners often get confused: the patch is right but it still reports an error, and the culprit is usually the signature and not the logic.

## Automation: dnlib and Mono.Cecil

When you need to patch in bulk, or write an unpack/deobfuscate tool, you don't sit there clicking through dnSpy method by method. Two libraries read and write .NET assemblies from code. dnlib is the foundation dnSpy itself uses underneath, powerful and able to handle even broken/obfuscated assemblies, and most modern .NET RE tools (including de4dot) are built on it. Mono.Cecil is older, with a compact API, enough for most IL reading/editing tasks.

An example idea with dnlib: load the module, walk to the check method, insert `ldc.i4.1; ret` at the start of the body, write it to a new file. About ten lines of C#. API details are saved for a lesson on automation, here you just need to know this route exists when manual dnSpy isn't enough.

## Lab

The exercise is at [labs/5.4/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/5.4): patch a .NET crackme so it always reports success, do it both ways (Edit Method C# and Edit IL), then save the module and run it again. The full solution with the specific IL is at [labs/5.4/solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/5.4/solution.md), do it yourself before opening it.

## Key takeaways
Patching .NET is cleaner than native because methods are located through metadata tokens, and dnSpy recomputes offsets when you Save Module. Edit Method (C#) is fastest, but you get stuck when the decompiler translated it wrong. Edit IL always works, so remember a few instructions: `ldc.i4.0/1`, `ret`, `brtrue/brfalse`, `nop`.

Common tricks are flipping `brtrue`/`brfalse`, inserting `ldc.i4.1; ret` to force a bool function to return true, and nopping a call. If it still errors after patching, suspect the strong name signature before suspecting the logic. For bulk patching, use dnlib or Mono.Cecil.
