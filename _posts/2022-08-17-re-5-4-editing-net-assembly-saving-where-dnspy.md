---
title: "Lesson 5.4: Editing a .NET assembly and saving it"
image:
  path: /assets/img/covers/re-5-4-editing-net-assembly-saving-where-dnspy.webp
  alt: "Lesson 5.4: Editing a .NET assembly and saving it"
date: 2022-08-17 15:56:00 +0700
categories: ["Technique Reverse", "Part 05 · C# and .NET"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
With native code, patching means changing opcode bytes one by one, watching that you don't shift addresses, then rebuilding. With .NET it's very different, because dnSpy lets you edit the C# code directly, hit recompile, and save the file. It sounds like cheating, but it follows from .NET assemblies carrying full metadata (see [Lesson 5.1](/posts/re-5-1-net-internals-why-decompiling-gives-back/)).

We'll patch at two levels, the C# level (easiest, but not always possible) and the IL level (always works, and the main skill of a .NET reverser).

## Why patching .NET is cleaner than native

When you edit a native function, the new code has to fit in exactly the old number of bytes (or you need a code cave), because shifting everything behind it breaks every absolute address and offset. That's why people often `nop` instead of rewriting.

IL doesn't have that constraint. Methods in .NET are located through metadata tokens and not fixed addresses, and dnSpy rewrites the whole module when saving, so it recomputes every offset and every table. You can add or remove IL instructions freely and dnSpy does the bookkeeping. You can even change method signatures, add fields, change the flow, and the file still runs.

## Level 1: Edit Method, editing C# directly

This is the fastest route when the decompiler gives C# clean enough to recompile.

In dnSpy, open the assembly and find the method to change (use search or Analyze as in [Lesson 5.2](/posts/re-5-2-ilspy-dnspy-when-decompiling-gives-back/)). Right-click the method and choose **Edit Method (C#)**, and dnSpy opens a C# editing box at that method. Edit the logic, for example change a check function that returns `false` when wrong so it always does `return true`. Click **Compile** and dnSpy uses Roslyn to recompile the method into the assembly, then use **File > Save Module** to write it to disk.

You work in familiar C#. The downside is that if the decompiler translated it wrong (common with obfuscated code, newer language features, or places dnSpy can't rebuild correctly), that C# won't compile and you're stuck. Then you go down to the IL level.

## Level 2: Edit IL Instructions

IL is the real bytecode of the method. Editing here doesn't depend on whether the decompiler translated correctly, so it always works. Serious .NET reversers are comfortable with a handful of IL instructions. You don't need to memorize them all.

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

Some classic patching tricks. You can flip a branch by changing `brtrue` to `brfalse` (and vice versa) so the "wrong" and "right" branches swap, and one instruction flips the whole logic. You can force the return value. If the check function returns a bool, insert `ldc.i4.1` then `ret` at the start of the method, and the function always returns `true` and never runs the logic. You can disable a call by replacing the annoying `call` (for example one that calls an anti-tamper function) with the same number of `nop`s. Balance the stack too. If the call returns a value that's used afterwards, push a fake value in its place. And you can change a comparison constant. If it compares a length against 8, change the `ldc.i4.8` constant to the value you want.

You usually don't need to understand the whole method. Find the exact spot where it decides right/wrong (either a `brtrue`/`brfalse` or the `ret` of a bool function) and step in there. Least touching, least risk.

## Pitfall: strong name signature

Many assemblies are signed with a strong name. After you edit and save, the signature no longer matches the content, and if something checks it (strong name verification, or the assembly is loaded through the GAC or a host that checks), the file will be refused.

How you handle it depends on the case. If the assembly loads other assemblies itself and verifies signatures, you may have to patch that check too. For a normal assembly run directly, strong name verification has been off by default since .NET Framework 3.5 SP1 for full-trust, so it often still runs. dnSpy's Save Module has writer-related options, so if you hit a token/signature error, try unchecking keep signature, or remove the strong name and re-sign with your own key. Command-line tools like `sn.exe -Vr` (skip verification) also work in your own test environment.

Beginners often get confused here, because the patch is right but it still reports an error, and the cause is usually the signature and not the logic.

## Automation: dnlib and Mono.Cecil

When you need to patch in bulk, or write an unpack/deobfuscate tool, you don't click through dnSpy method by method. Two libraries read and write .NET assemblies from code. dnlib is what dnSpy itself uses underneath. It can handle even broken/obfuscated assemblies, and most modern .NET RE tools (including de4dot) are built on it. Mono.Cecil is older, with a compact API, enough for most IL reading/editing tasks.

An example with dnlib is to load the module, walk to the check method, insert `ldc.i4.1; ret` at the start of the body, write it to a new file. About ten lines of C#. API details are for a lesson on automation, here you just need to know this route exists when manual dnSpy isn't enough.

## Lab

The goal is to make the crackme always print `Correct!` whatever you type, by editing the .NET assembly rather than by finding the password. You need dnSpy and a build of `Program.cs`. With the .NET SDK, run `dotnet new console -o crackme54`, copy `Program.cs` into that folder, then build and run it:

```
dotnet build -c Release
dotnet crackme54.dll
```

With the .NET Framework instead, `csc Program.cs` produces `Program.exe`.

Open the assembly in dnSpy and find the method `CheckPassword`. Work out where the right/wrong decision is made, which is the bool return value, and the `brtrue`/`brfalse` branch in `Main`. For the first approach, right-click `CheckPassword`, choose Edit Method (C#), change the body to `return true;`, Compile, Save Module and run again. For the second approach, undo that (or start from the original), right-click `CheckPassword`, choose Edit IL Instructions, insert `ldc.i4.1` followed by `ret` at the start of the method, save the module and run again. Then try a third way, which is to patch `Main` itself and flip the `brfalse`/`brtrue` at the branch so the "Correct!" path always runs. Compare the three, and decide which one touches the least and which one is the safest.

Two questions to think about afterwards. If the assembly has a strong name, what error do you get after Save Module and how do you handle it? And why doesn't patching IL break the other methods even though you added instructions?

<div class="lab-box">
<div class="lab-head"><b>LAB 5.4</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/5.4/src/Program.cs" download><i class="fa-solid fa-file-code"></i>src/Program.cs</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The real password is `dotnet_42` (the string `"dotnet_" + (2*21)`), but this exercise doesn't ask you to find it, it asks you to patch the check away.

The target function. In dnSpy, `CheckPassword` decompiles to roughly this:

```csharp
static bool CheckPassword(string input)
{
    string expected = "dotnet_" + (2 * 21).ToString();
    return input == expected;
}
```

Its IL (abridged) ends with a comparison and a `ret`:

```
ldarg.0
ldstr      "dotnet_"
...                     // builds the expected string
call       string System.String::Concat(...)
call       bool System.String::op_Equality(string, string)
ret
```

Approach A, Edit Method (C#). Right-click `CheckPassword` and choose Edit Method (C#). Change the body to:

```csharp
static bool CheckPassword(string input)
{
    return true;
}
```

Compile, then File > Save Module. Run it again and whatever you type gives `Correct!`. It's the fastest way, but it only works when the C# recompiles successfully.

Approach B, Edit IL Instructions. Use this when you want certainty and independence from the decompiler. Right-click `CheckPassword`, choose Edit IL Instructions, and insert two instructions at the top of the list:

```
ldc.i4.1
ret
```

The old instructions after them are never reached, so the method always returns `true`. Save Module and run again. `ldc.i4.1` pushes the constant 1 (true) onto the evaluation stack and `ret` immediately returns the value on top of the stack. Since the method is declared to return `bool`, 1 is exactly `true`.

Approach C, patching the branch in Main. In `Main`, the IL around the branch looks roughly like this:

```
call   bool Program::CheckPassword(string)
brfalse.s  IL_wrong      // if false, jump to the branch printing "Wrong"
ldstr  "Correct!"
call   void Console::WriteLine(string)
...
```

Change `brfalse.s` to `brtrue.s` (or remove the jump) so the "Correct!" path always runs regardless of the result. This is the classic inverted-branch patch and it edits a single instruction.

In comparison, A (Edit C#) touches the whole method, is quick, and suits cases where the C# recompiles. B (insert `ldc.i4.1; ret`) touches the first two instructions of the method and always works when the target is a bool function. C (flip the branch in the caller) touches one instruction and is the one to use when you don't want to, or can't, modify the check function itself.

On the strong name question, if the assembly is signed, running it after Save Module may report a signature verification error rather than a logic error. To handle it, remove the strong name when saving (an option in dnSpy's writer), or re-sign with your own key, or in a test environment use `sn -Vr`. Your logic patch was right, the signature is the cause.

Other methods don't break because .NET methods are referenced through metadata tokens, not fixed offsets. When you Save Module, dnSpy rewrites the whole metadata and the method bodies and recomputes every offset, so adding instructions to one method doesn't shift any other method.

</details>

## Key takeaways
Patching .NET is cleaner than native because methods are located through metadata tokens, and dnSpy recomputes offsets when you Save Module. Edit Method (C#) is fastest, but you get stuck when the decompiler translated it wrong. Edit IL always works, so remember a few instructions such as `ldc.i4.0/1`, `ret`, `brtrue/brfalse`, `nop`.

Common tricks are flipping `brtrue`/`brfalse`, inserting `ldc.i4.1; ret` to force a bool function to return true, and nopping a call. If it still errors after patching, suspect the strong name signature before the logic. For bulk patching, use dnlib or Mono.Cecil.
