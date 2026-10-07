---
title: "Lesson 5.2: ILSpy and dnSpy, when decompiling gives back almost the original source"
image:
  path: /assets/img/covers/re-5-2-ilspy-dnspy-when-decompiling-gives-back.webp
  alt: "Lesson 5.2: ILSpy and dnSpy, when decompiling gives back almost the original source"
date: 2022-08-06 14:52:00 +0700
categories: ["Technique Reverse", "Part 05 · C# and .NET"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
After struggling with native assembly for two whole parts, opening a .NET file in dnSpy is a pleasant shock. You click a method, and instead of a sea of `mov`/`call`, the window shows C# almost exactly as the author wrote it: class names, method names, local variable names, even a `foreach` loop intact. The reason is in lesson [5.1](/posts/re-5-1-net-internals-why-decompiling-gives-back/): .NET compiles to IL with full metadata, so the decompiler can rebuild a lot. This lesson is how to use the two main tools to take advantage of that.

Both are free portable downloads: `dnSpy.exe` and `ILSpy.exe`, so there's nothing to install.

## ILSpy or dnSpy, which one

Short answer: use both, each for its own job.

ILSpy is for reading. It's light, fast, cross-platform (there's an Avalonia build running on Linux/macOS), and it has a command-line version `ilspycmd` to export a whole C# project to disk so you can grep to your heart's content. When you just need to understand the code, ILSpy is enough. dnSpy (the maintained fork is dnSpyEx) does more: besides reading, it can debug an assembly with no source, and edit and save it back. Lessons [5.3](/posts/re-5-3-debugging-net-without-source-using-dnspy/) and [5.4](/posts/re-5-4-editing-net-assembly-saving-where-dnspy/) will use those two abilities. In this lesson we use dnSpy mainly for reading and investigating.

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

One thing to know: a .NET Core apphost `.exe` (for example `dnSpy.exe`) is often just a launcher shell, and the real code sits in the `.dll` with the same name. If you open the `.exe` and it looks empty, open the matching `.dll`. DIE also points this out in lesson [2.1](/posts/re-2-1-five-minute-triage-die-strings-pe/).

## View the C#, then flip to IL

By default the decompiler shows C#. But sometimes the decompiler translates wrong or hides details (especially with obfuscated code), and then you need to look at the raw IL, which doesn't lie.

In ILSpy, use the language dropdown on the toolbar and switch from `C#` to `IL`, or choose `IL with C#` to see them side by side. In dnSpy, use the context menu or the language button to switch between `C#` and `IL`.

IL is much easier to read than native assembly: it's a stack machine with clearly named opcodes (`ldarg`, `call`, `brtrue`, `ldstr`). When the decompiled C# looks weird, flipping to IL usually clears things up right away.

## Search: jump straight to what you need

Instead of fumbling through the tree, use search (ILSpy: the Search box, or `Ctrl+Shift+K` in dnSpy). You can search by type name, method name, and most importantly by string. It's like the go-from-strings technique in lesson [0.4](/posts/re-0-4-reverse-engineering-workflow-not-get-lost/): if you see the message "License invalid" in the program, search for that string and it leads straight to the license-check method.

## Analyze: the strongest weapon, xrefs for .NET

This is the feature that makes .NET RE much faster than native. Right-click a method, field or type and choose Analyze (in dnSpy) or open the Analyze panel (ILSpy). Used By shows which methods call this method, which is the reverse cross-reference, equivalent to the `X` key in IDA. Uses shows what this method calls. Instantiated By shows where objects of this class are created, and Assigned By / Read By covers fields.

A typical flow: you suspect a method `CheckLicense` is the center. Analyze it, look at Used By to see where it's called from (usually `Main` or a button click), then trace upward to understand the flow. Or the other way, from the error message string, Analyze the field holding the string to find where it's used. Following the Used By/Uses graph is how you rebuild the program's logic without reading everything.

## Export the whole project to grep

When the assembly is big, opening each method in the GUI is slow. ILSpy lets you export the whole project. In the GUI, right-click the assembly > Save Code, and it writes a `.csproj` folder with all the `.cs` files. On the command line, run `ilspycmd MyApp.dll -p -o outdir` (ilspycmd is a dotnet tool installed separately via `dotnet tool install -g ilspycmd`).

With the source on disk you can use grep, ripgrep, or open it in your favorite editor for full-text search, much faster than clicking around in the GUI.

## Lab

The task is to investigate a .NET assembly with ILSpy and dnSpy, and get comfortable with reading, switching to IL, searching and Analyze. You don't need to download anything special, because the .NET DLLs that ship with ILSpy make good samples. You need `ILSpy.exe` and `dnSpy.exe`, and the sample to dissect is `ICSharpCode.Decompiler.dll` from ILSpy's folder, a real and fairly large .NET assembly that is well suited for practice.

Start by opening the tree. Drag `ICSharpCode.Decompiler.dll` into ILSpy, expand the tree, find the namespace `ICSharpCode.Decompiler`, and list any 3 classes along with one method in each. Next decompile and read: pick a short method and read the C#, then switch the display language to IL (the language box on the toolbar) and compare the two, finding the opcodes `ldstr` (load a string), `call` (call a method) and `ret`. Then search by string. Use the Search box in string/constant mode and type a common English keyword (for example `Error`, `Invalid` or `version`), jump to a result and look at the method that contains it.

For cross-references, right-click any public method, choose Analyze, and open the **Used By** branch. Note at least two methods that call it, then open **Uses** to see what it calls out to. After that, open the same file in dnSpy and repeat the search and Analyze steps (`Ctrl+Shift+K` to search, right-click then Analyze), comparing the experience with ILSpy. Optionally, if you have `ilspycmd` installed (`dotnet tool install -g ilspycmd`), export the whole project:

```
ilspycmd ICSharpCode.Decompiler.dll -p -o out_decompiler
```

and then run `grep -r "Invalid" out_decompiler` to see the power of full-text search over exported source.

Two questions to think about. Why does decompiling .NET give readable C# right away, while decompiling a native C file does not (hint: metadata, see Lesson 5.1)? And if the class and method names were renamed to `a`, `b`, `c`, would the steps above still be effective, and which of them would still work? Try it before opening the solution.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Do it yourself first. What follows is a direction and sample answers. The specific class and method names may differ depending on the ILSpy version you have, but the approach is the same.

### Opening the tree

Drag `ICSharpCode.Decompiler.dll` into ILSpy. The namespace `ICSharpCode.Decompiler` holds a lot of classes. For example you may see `CSharpDecompiler` (the central class) with its method `DecompileWholeModuleAsString()`, `DecompilerSettings` (the configuration) with many bool properties, and, under `ICSharpCode.Decompiler.Metadata`, the classes that read PE and metadata. The tree follows assembly > namespace > type > method exactly, and every name is intact because this assembly is not obfuscated.

### Decompile, read, then flip to IL

Pick a short method. The right panel shows C#. Switch the language box to IL and you see the same method as opcodes. A string assignment in C# (`x = "abc"`) becomes `ldstr "abc"` followed by `stloc` in IL, a method call becomes `call` or `callvirt`, and the method ends with `ret`. IL is a stack machine, easier to read than native assembly, and it is the place to check when the decompiled C# looks strange.

### Search by string

Search for the string `Invalid` (or `Error`, `version`). ILSpy lists the methods and fields containing that string, and clicking a result jumps to the method that uses it. This is exactly the go-from-the-string technique, where a string is an anchor leading to logic.

### Analyze and xrefs

Right-click a public method (for example one in `CSharpDecompiler`), choose Analyze, and open **Used By**. You get a list of the methods that call it, and each line is clickable. **Uses** gives the opposite direction, the APIs and methods it calls out to. Use Used By to trace back from a core function up to an entry point, or Uses to go deeper down. It is the equivalent of IDA's `X` (xref) but for .NET, and more accurate because the metadata is complete.

### dnSpy

In dnSpy, `Ctrl+Shift+K` opens search and right-click then Analyze gives a similar window. The main difference is that dnSpy also has an Edit button (edit C# or IL) and can debug, which ILSpy cannot. For reading alone the two are equivalent.

### Exporting the project

```
ilspycmd ICSharpCode.Decompiler.dll -p -o out_decompiler
grep -rn "Invalid" out_decompiler
```

You get the whole `.cs` tree on disk, and a full-text grep finds every mention of a keyword immediately, which is faster than clicking through the GUI when the assembly is large.

### Answers to the questions

.NET decompiles nicely because a .NET file contains IL together with full metadata (type, method, field and parameter names, and types). The decompiler only has to translate IL up to C# and reattach the names that are already there. With a native C file the compiler has thrown away all the names and high-level structure and left only machine code, so everything has to be inferred from scratch. If the names were changed to a/b/c (obfuscation), searching and analyzing by name mostly lose their value. Searching by string still works, because strings are usually not renamed, or if they are encrypted they give themselves away at the decryption site, and the Used By and Uses graphs stay correct as call relationships even when the names are ugly. Removing obfuscation is Lesson 5.5.

</details>

## Common pitfalls
One is opening the empty apphost `.exe` instead of the `.dll` that holds the code, so open the `.dll` with the same name. Another is trusting the decompiled C# absolutely, when you should flip to IL to check anything that looks off. Skipping Analyze and trying to read sequentially also costs you, since Used By/Uses saves a huge amount of time. Finally, obfuscated code (names like `a.b.c`, encrypted strings) still decompiles but is hard to read. That's the topic of lesson [5.5](/posts/re-5-5-net-obfuscators-strip-them/).

## Key takeaways
ILSpy is for reading (light, cross-platform, ilspycmd exports projects) and dnSpy is for reading, debugging and editing. The tree goes assembly > namespace > type > method, and clicking a method gives you C#. Flip C# to IL when the decompile looks suspicious, and search by string to jump straight to the logic. Analyze (Used By / Uses) is .NET's cross-reference, so use it to rebuild the flow.
