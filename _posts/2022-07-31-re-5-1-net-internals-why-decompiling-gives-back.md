---
title: "Lesson 5.1: .NET internals, why decompiling gives back nearly the original source"
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

ILSpy and dnSpy are both included in this repo (the parent folder `ILSpy_binaries_9.0.0...` and `dnSpy-net-win64`). ILSpy specializes in decompiling and viewing IL, while dnSpy is strong in that it can also debug and edit assemblies. Lessons [5.2](/posts/re-5-2-ilspy-dnspy-when-decompiling-gives-back/) and [5.3](/posts/re-5-3-debugging-net-without-source-using-dnspy/) go deeper. ildasm (comes with the Windows SDK) outputs IL as text and ilasm assembles it back, ilspycmd is the command-line version of ILSpy and is handy for automation, and JetBrains' dotPeek is another free decompiler.

They all read the same thing: the IL and metadata in the assembly. They differ in interface and in the ability to edit.

## Lab

See `labs/5.1/`. You'll use DIE to recognize a file as .NET, then open it in ILSpy or dnSpy to see the IL and metadata with your own eyes. If your machine doesn't have the dotnet SDK, just use `ILSpy.dll` itself or the .NET DLLs in the repo as samples to look at.

## Key takeaways
A .NET file on disk contains IL bytecode plus metadata, not machine code, and machine code is only produced at runtime by the JIT. A .NET assembly is still a PE, but the code sits behind the CLI header and not in the usual .text section. Metadata keeps type/method/field names intact, so decompiling gives nearly the original source.

IL is stack-based bytecode, at a much higher level than assembly, so it's easy to translate back. The real obstacle when reversing .NET is usually obfuscation, not the format itself.
