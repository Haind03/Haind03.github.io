---
title: "Lesson 5.2: ILSpy and dnSpy, when decompiling gives back almost the original source"
date: 2026-10-06 08:38:00 +0700
categories: ["Technique Reverse", "Part 05 · C# and .NET"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
After struggling with native assembly for two whole parts, opening a .NET file in dnSpy is a pleasant shock. You click a method, and instead of a sea of `mov`/`call`, the window shows C# almost exactly as the author wrote it: class names, method names, local variable names, even a `foreach` loop intact. The reason is in lesson [5.1](/posts/tr-5-1-net-ben-trong-clr-il-metadata/): .NET compiles to IL with full metadata, so the decompiler can rebuild a lot. This lesson is how to use the two main tools to take advantage of that.

Both are already in the repo: `dnSpy-net-win64/dnSpy.exe` and `ILSpy_binaries_9.0.0.7660-preview2-x64/ILSpy.exe`.

## ILSpy or dnSpy, which one

Short answer: use both, each for its own job.

- **ILSpy** is for *reading*. Light, fast, cross-platform (there's an Avalonia build running on Linux/macOS), and it has a command-line version `ilspycmd` to export a whole C# project to disk so you can grep to your heart's content. When you just need to understand the code, ILSpy is enough.
- **dnSpy** (the maintained fork is **dnSpyEx**) does more: besides reading, it can *debug* an assembly with no source, and *edit* and save it back. Lessons [5.3](https://github.com/Haind03/Technique-Reverse/blob/main/phan-05-csharp-dotnet/5.3-debug-net-dnspy.md) and [5.4](https://github.com/Haind03/Technique-Reverse/blob/main/phan-05-csharp-dotnet/5.4-sua-il-csharp-patch.md) will use those two abilities. In this lesson we use dnSpy mainly for reading and investigating.

The two tools' interfaces are nearly the same, so learning one lets you use the other.

## Open an assembly and look around

Drag and drop a .NET `.exe` or `.dll` into the window, or File > Open. On the left a hierarchical tree appears:

```
MyApp.exe
  references        (dependent assemblies)
  MyApp             (root namespace)
    Program         (class)
      Main(string[]) : void       (method)
      CheckLicense(string) : bool
    Resources
```

The tree follows the .NET structure exactly: an assembly contains namespaces, a namespace contains types (class/struct/enum/interface), a type contains methods and fields. Click a method and the decompiler translates it to C# right in the right-hand panel.

One thing to know: a .NET Core apphost `.exe` (for example `dnSpy.exe`) is often just a launcher shell, and the real code sits in the `.dll` with the same name. If you open the `.exe` and it looks empty, open the matching `.dll`. DIE also points this out in lesson [2.1](/posts/tr-2-1-triage-die-strings-pebear/).

## View the C#, then flip to IL

By default the decompiler shows C#. But sometimes the decompiler translates wrong or hides details (especially with obfuscated code), and then you need to look at the raw IL, which doesn't lie.

- In **ILSpy**: the language dropdown on the toolbar, switch from `C#` to `IL`. You can choose `IL with C#` to see them side by side.
- In **dnSpy**: the context menu or the language button, switch between `C#` and `IL`.

IL is much easier to read than native assembly: it's a stack machine with clearly named opcodes (`ldarg`, `call`, `brtrue`, `ldstr`). When the decompiled C# looks weird, flipping to IL usually clears things up right away.

## Search: jump straight to what you need

Instead of fumbling through the tree, use search (ILSpy: the Search box, or `Ctrl+Shift+K` in dnSpy). You can search by type name, method name, and most importantly by **string**. It's like the go-from-strings technique in lesson [0.4](/posts/tr-0-4-quy-trinh-reverse/): if you see the message "License invalid" in the program, search for that string and it leads straight to the license-check method.

## Analyze: the strongest weapon, xrefs for .NET

This is the feature that makes .NET RE much faster than native. Right-click a method, field or type and choose **Analyze** (in dnSpy) or open the Analyze panel (ILSpy). It gives you:

- **Used By**: which methods call this method. This is the reverse cross-reference, equivalent to the `X` key in IDA.
- **Uses**: what this method calls.
- **Instantiated By**: where objects of this class are created.
- **Assigned By / Read By** for fields.

A typical flow: you suspect a method `CheckLicense` is the center. Analyze it, look at Used By to see where it's called from (usually `Main` or a button click), then trace upward to understand the flow. Or the other way, from the error message string, Analyze the field holding the string to find where it's used. Following the Used By/Uses graph is how you rebuild the program's logic without reading everything.

## Export the whole project to grep

When the assembly is big, opening each method in the GUI is slow. ILSpy lets you export the whole project:

- GUI: right-click the assembly > Save Code, and it writes a `.csproj` folder with all the `.cs` files.
- CLI: `ilspycmd MyApp.dll -p -o outdir` (ilspycmd is a dotnet tool installed separately via `dotnet tool install -g ilspycmd`).

With the source on disk you can use grep, ripgrep, or open it in your favorite editor for full-text search, much faster than clicking around in the GUI.

## Lab

In [labs/5.2/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/5.2) there are instructions to open the .NET DLLs already in the repo (for example ILSpy's `ICSharpCode.Decompiler.dll`) with both ILSpy and dnSpy, decompile, use Search and Analyze to follow a method, and try exporting the project to C# with ilspycmd. The solution is in `solution.md`.

## Common pitfalls
- Opening the empty apphost `.exe` instead of the `.dll` that holds the code. Open the `.dll` with the same name.
- Trusting the decompiled C# absolutely. When something looks off, flip to IL to check.
- Skipping Analyze and trying to read sequentially. Used By/Uses saves a huge amount of time.
- Obfuscated code (names like `a.b.c`, encrypted strings) still decompiles but is hard to read. That's the topic of lesson [5.5](https://github.com/Haind03/Technique-Reverse/blob/main/phan-05-csharp-dotnet/5.5-obfuscator-de4dot.md).

## Key takeaways
- ILSpy for reading (light, cross-platform, ilspycmd exports projects), dnSpy for reading + debugging + editing.
- The tree: assembly > namespace > type > method. Click a method to get C#.
- Flip C# to IL when the decompile looks suspicious.
- Search by string to jump straight to the logic.
- Analyze (Used By / Uses) is .NET's cross-reference, use it to rebuild the flow.
