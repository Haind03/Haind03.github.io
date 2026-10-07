---
title: "Lesson 5.1: .NET internals, why decompiling gives back nearly the original source"
image:
  path: /assets/img/covers/re-5-1-net-internals-why-decompiling-gives-back.webp
  alt: "Lesson 5.1: .NET internals, why decompiling gives back nearly the original source"
date: 2022-07-31 15:25:00 +0700
categories: ["Technique Reverse", "Part 05 · C# and .NET"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
After several parts of wrestling with native assembly, this part is a vacation. Open a .NET file in dnSpy or ILSpy and you usually get back C# that reads almost exactly like what the author wrote: the right class names, the right method names, the right variable names, not the comments but the structure is intact. The interesting question is: why is native such a mess while .NET is so nice? Answer that and you understand the approach for this whole part.

## A .NET program doesn't contain machine code

This is the crux. When you build a C# project, the compiler (Roslyn) doesn't produce x86 instructions. It produces **IL** (Common Intermediate Language, also called MSIL or CIL), an intermediate, CPU-independent kind of bytecode. Real machine code is only created **at runtime**, by the CLR's JIT compiler, right before a method is called for the first time.

The full flow:

```
C# source  --Roslyn-->  IL + metadata  (sits in the .exe/.dll file)
                              |
                         CLR loads, JIT
                              v
                        x86/x64 machine code  (exists only in RAM at runtime)
```

Because what's on disk is IL and not machine code, and IL is at a much higher level than assembly, translating IL back to C# is much easier than translating machine code back to C++.

## CLR, IL, metadata: three pieces

![.NET architecture: source to IL plus metadata, JIT to native, dnSpy decompiles back](/assets/img/re/part-05/dotnet-arch.svg)

The CLR (Common Language Runtime) is the virtual machine that runs .NET programs, a role like the JVM for Java. It loads assemblies, JITs, manages memory (the garbage collector), and does type safety checks. Code running on the CLR is called **managed code**.

An assembly is the unit of deployment: an `.exe` or `.dll` file. The interesting part is that it's still a valid PE file (see [Lesson 1.7](/posts/re-1-7-pe-format-anatomy-windows-exe/) again), but the code isn't in a `.text` section holding x86, it's a CLI header pointing to the IL and metadata streams. That's why DIE opening a .NET file still reports PE, but adds ".NET".

IL is stack-based bytecode: instead of operating on registers like x86, it pushes operands onto an evaluation stack and pops them off. For example `a + b` becomes "push a, push b, add". It's precisely this abstract, information-rich form that lets the decompiler rebuild the original expressions.

Metadata is the real star. Alongside the IL is a set of tables fully describing every type, method, field, parameter, with their **real names**. The CLR needs metadata for reflection, binding, and type checking, so the names can't be stripped like symbols in native code. The decompiler reads the metadata directly and immediately has class and method names. This is the biggest difference from native, where variable names are gone after compiling.

## Looking at IL to picture it

A small C# method:

```csharp
public static int Add(int a, int b)
{
    return a + b;
}
```

The matching IL (as shown by ildasm/ILSpy):

```
.method public hidebysig static int32 Add(int32 a, int32 b) cil managed
{
    ldarg.0      // push argument 0 (a) onto the stack
    ldarg.1      // push argument 1 (b) onto the stack
    add          // take the top two, add, push the result
    ret          // return the value on top of the stack
}
```

Notice: the method name `Add`, the type `int32`, the parameter names `a` and `b` are all intact. Compared to native, where this function becomes `sub_401000` taking two numbers in `rcx`/`rdx`, this is almost source. The decompiler just has to put it back together as `return a + b;`.

## Why managed is easier than native

Collected into a table to be clear:

| | Native (C/C++) | Managed (.NET) |
|---|---|---|
| What's on disk | x86/x64 machine code | IL bytecode |
| Function/variable names | gone (unless there are symbols) | intact in the metadata |
| Abstraction level | low, close to the CPU | high, close to the language |
| Decompile result | approximate pseudocode | C# nearly like the original |
| Main obstacle | compiler optimization | obfuscation (see Lesson 5.5) |

The last point is very important: the only thing standing between you and .NET source usually isn't the format itself, but an **obfuscator** deliberately renaming and distorting things. Most of this part is therefore about removing obfuscation, not wrestling with IL.

## Tools

ILSpy and dnSpy are both free portable downloads. ILSpy specializes in decompiling and viewing IL, while dnSpy is strong in that it can also debug and edit assemblies. Lessons [5.2](/posts/re-5-2-ilspy-dnspy-when-decompiling-gives-back/) and [5.3](/posts/re-5-3-debugging-net-without-source-using-dnspy/) go deeper. ildasm (comes with the Windows SDK) outputs IL as text and ilasm assembles it back, ilspycmd is the command-line version of ILSpy and is handy for automation, and JetBrains' dotPeek is another free decompiler.

They all read the same thing: the IL and metadata in the assembly. They differ in interface and in the ability to edit.

## Lab

The goal is to confirm by hand what this lesson says: a .NET file contains IL and metadata that keeps names, so it decompiles to something very close to the source. You don't strictly need the dotnet SDK. If you don't have it, use any .NET files you already have as samples. The tools are DIE (Detect It Easy), ILSpy and dnSpy.

First recognize .NET with DIE. Drag `ILSpy.dll` (or `dnSpy.exe`) into DIE and confirm it reports a PE with an extra .NET / CLR label, and note which runtime it names (.NET Framework or modern .NET). Why is it still a PE, yet the code isn't in the `.text` section the way it would be in a plain C exe?

Then open a .NET DLL in ILSpy. Open `ILSpy.exe`, choose File > Open and point it at any .NET DLL in the ILSpy folder (for example `ICSharpCode.Decompiler.dll`). Browse the tree of namespaces, classes and methods on the left and notice the names are fully intact. Pick any method and look at the decompiled C# on the right. Next switch the language box in the top corner from `C#` to `IL` and compare the IL with the C# of the same method. Look for `ldarg`, `ldloc`, `call` and `ret`, and pick a small method (a getter or an addition function) to see the IL to C# mapping most clearly.

If you have the dotnet SDK, build a program of your own. Create a project with this command:

```
mkdir hello5x && cd hello5x && dotnet new console
```

Replace `Program.cs` with the file `Program.cs` that comes with this lab, then build:

```
dotnet build -c Debug
```

Open the resulting DLL (in `bin/Debug/netX/Hello5x.dll`) in ILSpy, find the method `Calculator.Add`, look at its IL and compare. Switch `SumTo` to IL and see for yourself how the `for` loop turns into a conditional jump.

Two questions to think about. If an assembly is obfuscated so that every name becomes `a`, `b`, `c`, which part of the file is touched, the IL or the metadata (hint: both kinds of names live in the metadata)? And why can dnSpy edit code while ILSpy can't (see Lessons 5.2 and 5.4)?

<div class="lab-box">
<div class="lab-head"><b>LAB 5.1</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/5.1/src/Program.cs" download><i class="fa-solid fa-file-code"></i>src/Program.cs</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

DIE reports the file is a PE, and it also recognizes the CLI header and attaches a label like `.NET` with the runtime version (for example `.NET Framework(v4.0...)` or `.NET(v8...)`). It can do that because the Optional header of a PE has a Data Directory called COM Descriptor (`IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR`, the 14th entry) that points to the CLI header, and native files normally leave this entry empty.

As for why it is a PE and yet the code isn't in the normal `.text`: the Windows loader still loads the file as an ordinary PE, but the entry point is only a small stub that jumps into the CLR. The real code is IL, living in the streams (`#~`, `#Strings`, `#US`, `#Blob`) that the CLI header points to, and only the CLR understands it. The section holding them is usually named `.text`, but its content is IL plus metadata, not x86.

When you open `ICSharpCode.Decompiler.dll` (or any .NET DLL), the tree on the left shows namespaces, classes and methods with their original names. That is direct evidence that metadata keeps names. Switch to IL mode and a simple property getter looks like this:

```
.method public hidebysig specialname instance int32 get_Count() cil managed
{
    ldarg.0
    ldfld int32 SomeClass::_count
    ret
}
```

The mapping is easy to see. `ldarg.0` loads `this` (hidden argument number 0), `ldfld` reads a field (the field name is in the metadata too) and `ret` returns.

For your own build, the method in this lab's `Program.cs`:

```csharp
public static int Add(int a, int b)
{
    return a + b;
}
```

gives IL roughly like this in a Debug build:

```
.method public hidebysig static int32 Add(int32 a, int32 b) cil managed
{
    .maxstack 2
    ldarg.0    // a
    ldarg.1    // b
    add
    ret
}
```

In a Debug build Roslyn may insert extra `nop`s and use a temporary local for the return value, so you may see `stloc.0` and `ldloc.0` mixed in. A Release build is as compact as above. Then `SumTo` with its `for` loop:

```csharp
public int SumTo(int n)
{
    int total = 0;
    for (int i = 1; i <= n; i++)
        total += i;
    return total;
}
```

Its IL has two locals (`total`, `i`), a label at the top of the loop, a body that accumulates, and a `blt` or `ble` (branch if less than or less or equal) that goes back to the top of the loop. A `for` loop in IL is also just compare plus jump, like assembly, but it keeps the variable names, so a decompiler can rebuild a clean `for` loop.

On the reflection questions, a renaming obfuscator acts on the metadata (the `#Strings` table holds the names). IL refers to names through tokens that point into the metadata, so when the original names are replaced with `a`, `b`, `c` or unreadable characters, the decompiler still produces code with the right logic but meaningless names. The logic (IL) isn't lost, only the names. dnSpy can edit because it can recompile a method from C# or edit the IL directly and write the assembly back (using dnlib), while ILSpy leans toward reading and decompiling and doesn't focus on writing back. The details are in Lessons 5.2 and 5.4.

</details>

## Key takeaways
A .NET file on disk contains IL bytecode plus metadata, not machine code, and machine code is only produced at runtime by the JIT. A .NET assembly is still a PE, but the code sits behind the CLI header and not in the usual .text section. Metadata keeps type/method/field names intact, so decompiling gives nearly the original source.

IL is stack-based bytecode, at a much higher level than assembly, so it's easy to translate back. The real obstacle when reversing .NET is usually obfuscation, not the format itself.
