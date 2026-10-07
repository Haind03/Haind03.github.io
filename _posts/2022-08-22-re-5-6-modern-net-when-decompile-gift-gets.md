---
title: "Lesson 5.6: Modern .NET, when the decompile gift gets taken back"
image:
  path: /assets/img/covers/re-5-6-modern-net-when-decompile-gift-gets.webp
  alt: "Lesson 5.6: Modern .NET, when the decompile gift gets taken back"
date: 2022-08-22 15:21:00 +0700
categories: ["Technique Reverse", "Part 05 · C# and .NET"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
The earlier lessons in Part 5 gave you a comfortable feeling: open dnSpy, click a button, get nearly the original source. That's the world of the old .NET Framework. But .NET Core and .NET 5, 6, 7, 8 onwards add many publish modes, and one of them takes back that whole gift, turning the problem into native reversing like C++. This lesson helps you recognize which kind you're holding, so you don't waste a whole session looking for IL in a file that has no IL left.

Three modes worth caring about: single-file, ReadyToRun, and NativeAOT. The difficulty goes up in that order, and NativeAOT is the turning point.

## First: how .NET Core differs from .NET Framework

The old .NET Framework runs on the CLR preinstalled in Windows, a small `.exe` file calling into the system runtime. .NET Core (and .NET 5+) carries its own runtime, so packaging is much more flexible. A modern .NET app can be published in several ways. Framework-dependent needs the runtime installed on the machine, gives a small file, and is still pure IL, as easy as .NET Framework. Self-contained ships the runtime too, so it's heavier but still IL. Single-file merges everything into one exe, ReadyToRun (R2R) puts precompiled native code next to the IL, and NativeAOT compiles straight to native, throwing away the IL.

The last three are where you need to understand things well.

## Single-file: everything in one exe

![Comparing single-file, ReadyToRun, NativeAOT in terms of decompilability](/assets/img/re/part-05/dotnet-packaging.svg)

When you publish with `PublishSingleFile=true`, the toolchain stuffs all the dependent DLLs (and sometimes the runtime too) into a single `.exe` file for tidiness. It sounds like hiding, but it's really just a bundle: the `.NET` DLLs are still intact inside, just repacked.

Newer dnSpy and ILSpy can often open single-file directly and list the assemblies inside on their own. If not, use a bundle extraction tool like ExtractAllTheThings or `dotnet-bundle extract` scripts, which split the file back into individual DLLs, and then open each DLL as usual. The signs are that the `.exe` is fairly large (tens of MB if self-contained), and DIE or a look at the hex shows traces of several `.NET` assemblies glued together.

In other words, single-file is only a packaging layer. The decompile gift is still fully there, you just have to open it the right way.

## ReadyToRun (R2R): native is there, but the IL is still there too

R2R compiles part of the IL ahead of time into native code so the app starts faster, without having to JIT from scratch. The key point for a reverser: **R2R keeps both**, there's precompiled native code, but the IL and metadata are still in the file.

That means you can still decompile to C#. dnSpy/ILSpy read the IL part as usual. The native part is just a compiled copy of that same IL, with no new information. Unless you suspect the runtime executes native differently from the IL (rare), reading the IL is enough.

In short, R2R looks scarier than it is. It's still managed, still decompiles fine.

## NativeAOT: this is the turning point

NativeAOT (Native Ahead-Of-Time) compiles the whole program straight to native machine code, like C++. There's no CLR loading IL at runtime, no JIT, and most importantly: **no IL, no managed metadata left to decompile.**

The consequences are very real. Opening a NativeAOT binary in dnSpy or ILSpy will fail, or only show a native PE with an empty managed part, so don't waste time. You have to reverse it like a C++ binary: IDA, Ghidra, x64dbg, read the assembly, recover the logic by hand, and everything learned in Part 1 through Part 4 comes back into use here. There's a small consolation: the .NET runtime leaves a few traces. There may be some metadata left for reflection, type names in runtime tables, or characteristic strings of the CoreCLR/NativeAOT runtime. A few community scripts try to recover method names from these tables, but don't expect nice C# like before.

NativeAOT is still new and not as common as the traditional IL kind, but it's being used more and more for CLI tools and apps that need fast startup. If you meet a ".NET app" that dnSpy gives up on, NativeAOT is the prime suspect.

## Quick identification with Detect It Easy

The triage step (recall [Lesson 2.1](/posts/re-2-1-five-minute-triage-die-strings-pe/)) decides which direction you go. If DIE reports ".NET" with assembly info, and dnSpy shows a namespace tree, this is pure IL (framework-dependent, self-contained, or R2R) and you can decompile freely. If the file is very large and DIE still recognizes the .NET signs but it opens a bit strangely, it's likely a single-file bundle, so extract it and then open. If DIE reports a plain native PE (for example "C++" or just "PE") but you know for sure the origin is a .NET app, or you see strings related to the CoreCLR/NativeAOT runtime, mutexes, .NET type names in a file with no managed header, it's very likely NativeAOT, so switch to IDA/Ghidra.

A manual check tip: a PE with managed code has a CLI header (the COM Descriptor Data Directory is nonzero). Pure native has this entry empty. PE-bear or DIE shows you this.

## Lab

The goal is to tell the three modern .NET publish styles apart and to know which ones can still be decompiled and which ones must be reversed as native code. You need Detect It Easy (with its command-line `diec`), dnSpy and optionally PE-bear. If you have the dotnet SDK, do part A, otherwise do part B.

For part A, create a minimal app:

```bash
dotnet new console -o aotdemo
cd aotdemo
```

Edit `Program.cs` so it has a bit of logic (read an argument, print a string), then publish it three ways into three different folders:

```bash
# 1. single-file (self-contained, still IL)
dotnet publish -c Release -r win-x64 --self-contained true \
  -p:PublishSingleFile=true -o out-singlefile

# 2. ReadyToRun (native + IL)
dotnet publish -c Release -r win-x64 --self-contained true \
  -p:PublishReadyToRun=true -o out-r2r

# 3. NativeAOT (native only, needs the aot workload)
dotnet publish -c Release -r win-x64 \
  -p:PublishAot=true -o out-aot
```

Run `diec` on the exe in each of the three folders and note what DIE says for each. Try opening each exe in dnSpy and see which ones show the namespace tree and decompile to C#, and which one dnSpy gives up on. Compare the three file sizes and explain them. For the NativeAOT build, open it in Ghidra or IDA and check whether any managed-style method names remain, and look for strings related to the runtime.

For part B, without the SDK, use .NET files you already have as samples. Run `diec dnSpy.exe` and `diec ILSpy.exe` (or the accompanying `.dll` files) and see whether DIE recognizes them as a .NET apphost or a real assembly, and why the main code lives in the `.dll` and not in the apphost `.exe` (discussed in Lesson 2.1). Open a .NET DLL such as ILSpy's `ICSharpCode.Decompiler.dll` in dnSpy and confirm it decompiles to C#, which stands for plain IL. Then use PE-bear or DIE to check a file's Data Directory: a COM Descriptor (CLI header) entry that is non-zero means managed code, and zero means pure native. Confirm this yourself on a .NET DLL and on any native DLL, for instance a `Qt5Core.dll` from the DIE folder. Finally write down your own identification rules: which signs tell you to open dnSpy and which tell you to switch to IDA or Ghidra.


<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Comparing the three publish styles:

| Style | What DIE says | Opens in dnSpy? | IL still present? | Approach |
|---|---|---|---|---|
| single-file (self-contained) | .NET, very large file, bundle marker | Yes (it lists the inner assemblies itself), or extract first | Yes | Decompile normally after extracting |
| ReadyToRun | .NET, with native code too | Yes | Yes (with native) | Read the IL, ignore the native part |
| NativeAOT | Native PE (no managed marker) | No | No | Reverse like C++ with IDA/Ghidra |

Single-file is essentially a bundle: the original .NET DLLs are glued onto the end of the exe in a dedicated bundle format. Recent dnSpy builds recognize it and let you browse each assembly as if it were a separate file. If dnSpy can't open it, use ExtractAllTheThings or a bundle extraction script to split it into individual `.dll` files and open those normally. The size is large (tens of MB) because the runtime is packed in.

ReadyToRun holds two versions of the same logic in the file: the original IL and a precompiled native version for fast startup. dnSpy reads the IL part and decompiles to C# as usual, and the native part is just a compiled copy that adds no information. The practical conclusion is that when you meet R2R, just read the IL and don't bother with the native part unless you have a special reason.

NativeAOT is the big difference. The program is compiled straight to machine code, with no IL or managed metadata left. dnSpy and ILSpy are helpless because there is nothing for them to read. You have to open it in IDA or Ghidra and reverse it like a C++ binary: read assembly, rebuild the logic, recover structs. The .NET runtime does leave a few traces (type tables for reflection, runtime strings), and some community scripts try to restore method names from them, but the result is never as nice as decompiling IL.

Identifying by the CLI header (part B). Every PE with managed code declares a CLI header, which is the **COM Descriptor** entry in the Data Directory table of the Optional Header (index 14). A non-zero COM Descriptor (pointing to an RVA) means the file has managed code and opens in dnSpy or ILSpy, which holds for every .NET DLL and for R2R and single-file builds. A COM Descriptor of zero means a pure native PE, which holds for NativeAOT and for native DLLs like `Qt5Core.dll`. In PE-bear, open the Optional Header tab, scroll to Data Directories and look at the .NET MetaData (COM Descriptor) row. DIE also shows directly whether a file is .NET, based on this same header.

A condensed set of rules. Triage with DIE before anything else. If DIE says .NET and dnSpy shows a namespace tree, it is plain IL and you can decompile freely (framework-dependent, self-contained, R2R). If a .NET file is very large and opens strangely, it is single-file, so extract the bundle and open the pieces. If you know it's a .NET app but DIE says pure native and dnSpy gives up, it is NativeAOT, so switch to IDA or Ghidra and reverse it like C++.

This matters because misreading the publish style is the biggest time sink when you start with .NET RE. People can sit for an hour trying to force dnSpy to open a NativeAOT binary when one DIE triage would have told them to open IDA. One minute of triage saves an hour of frustration.

</details>

## Key takeaways
Modern .NET has several publish modes, increasingly hard: framework-dependent, self-contained, single-file, R2R, NativeAOT. Single-file is just a bundle, so extract it (dnSpy, ExtractAllTheThings) and open each DLL, since it's still IL. R2R keeps both native and IL, so just read the IL and decompile as usual.

NativeAOT discards the IL/managed metadata, so you have to reverse it like C++ with IDA/Ghidra, and this is the turning point. Always triage with DIE first, because whether there's a CLI header (managed) decides the whole approach.
