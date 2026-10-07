---
title: "Lesson 5.6: Modern .NET, when the decompile gift gets taken back"
date: 2026-10-06 08:42:00 +0700
categories: ["Technique Reverse", "Part 05 · C# and .NET"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
The earlier lessons in Part 5 gave you a comfortable feeling: open dnSpy, click a button, get nearly the original source. That's the world of the old .NET Framework. But .NET Core and .NET 5, 6, 7, 8 onwards add many publish modes, and one of them takes back that whole gift, turning the problem into native reversing like C++. This lesson helps you recognize which kind you're holding, so you don't waste a whole session looking for IL in a file that has no IL left.

Three modes worth caring about: single-file, ReadyToRun, and NativeAOT. The difficulty goes up in that order, and NativeAOT is the turning point.

## First: how .NET Core differs from .NET Framework

The old .NET Framework runs on the CLR preinstalled in Windows, a small `.exe` file calling into the system runtime. .NET Core (and .NET 5+) carries its own runtime, so packaging is much more flexible. A modern .NET app can be published as:

- **framework-dependent**: needs the runtime installed on the machine, small file, still pure IL. As easy as .NET Framework.
- **self-contained**: ships the runtime too, heavier but still IL.
- **single-file**: merges everything into one exe.
- **ReadyToRun (R2R)**: puts precompiled native code next to the IL.
- **NativeAOT**: compiles straight to native, throwing away the IL.

The last three are where you need to understand things well.

## Single-file: everything in one exe

![Comparing single-file, ReadyToRun, NativeAOT in terms of decompilability](/assets/img/technique-reverse/assets/phan-05/dotnet-packaging.svg)

When you publish with `PublishSingleFile=true`, the toolchain stuffs all the dependent DLLs (and sometimes the runtime too) into a single `.exe` file for tidiness. It sounds like hiding, but it's really just a bundle: the `.NET` DLLs are still intact inside, just repacked.

How to handle it:
- Newer dnSpy and ILSpy can often open single-file directly and list the assemblies inside on their own.
- If not, use a bundle extraction tool like **ExtractAllTheThings** or `dotnet-bundle extract` scripts, which split the file back into individual DLLs. Then open each DLL as usual.
- Signs: the `.exe` is fairly large (tens of MB if self-contained), and DIE or a look at the hex shows traces of several `.NET` assemblies glued together.

In other words, single-file is only a packaging layer. The decompile gift is still fully there, you just have to open it the right way.

## ReadyToRun (R2R): native is there, but the IL is still there too

R2R compiles part of the IL ahead of time into native code so the app starts faster, without having to JIT from scratch. The key point for a reverser: **R2R keeps both**, there's precompiled native code, but the IL and metadata are still in the file.

That means you can still decompile to C#. dnSpy/ILSpy read the IL part as usual. The native part is just a compiled copy of that same IL, with no new information. Unless you suspect the runtime executes native differently from the IL (rare), reading the IL is enough.

In short, R2R looks scarier than it is. It's still managed, still decompiles fine.

## NativeAOT: this is the turning point

NativeAOT (Native Ahead-Of-Time) compiles the whole program straight to native machine code, like C++. There's no CLR loading IL at runtime, no JIT, and most importantly: **no IL, no managed metadata left to decompile.**

The consequences are very real:
- Opening a NativeAOT binary in dnSpy or ILSpy will fail, or only show a native PE with an empty managed part. Don't waste time.
- You have to reverse it **like a C++ binary**: IDA, Ghidra, x64dbg, read the assembly, recover the logic by hand. Everything learned in Part 1 through Part 4 comes back into use here.
- A small consolation: the .NET runtime leaves a few traces. There may be some metadata left for reflection, type names in runtime tables, or characteristic strings of the CoreCLR/NativeAOT runtime. A few community scripts try to recover method names from these tables, but don't expect nice C# like before.

NativeAOT is still new and not as common as the traditional IL kind, but it's being used more and more for CLI tools and apps that need fast startup. If you meet a ".NET app" that dnSpy gives up on, NativeAOT is the prime suspect.

## Quick identification with Detect It Easy

The triage step (recall [Lesson 2.1](/posts/tr-2-1-triage-die-strings-pebear/)) decides which direction you go:

- DIE reports **".NET"** with assembly info, and dnSpy shows a namespace tree: this is pure IL (framework-dependent, self-contained, or R2R). Decompile freely.
- The file is very large, DIE still recognizes the .NET signs but it opens a bit strangely: likely a single-file bundle. Extract it and then open.
- DIE reports a **plain native PE** (for example "C++" or just "PE") but you know for sure the origin is a .NET app, or you see strings related to the CoreCLR/NativeAOT runtime, mutexes, .NET type names in a file with no managed header: very likely NativeAOT. Switch to IDA/Ghidra.

A manual check tip: a PE with managed code has a CLI header (the COM Descriptor Data Directory is nonzero). Pure native has this entry empty. PE-bear or DIE shows you this.

## Key takeaways
- Modern .NET has several publish modes, increasingly hard: framework-dependent, self-contained, single-file, R2R, NativeAOT.
- Single-file is just a bundle: extract it (dnSpy, ExtractAllTheThings) then open each DLL. Still IL.
- R2R keeps both native and IL: just read the IL, decompile as usual.
- NativeAOT discards the IL/managed metadata: you have to reverse it like C++ with IDA/Ghidra. This is the turning point.
- Always triage with DIE first: whether there's a CLI header (managed) decides the whole approach.
