---
title: "Lesson 10.2: Visual Basic 6, two worlds inside the same exe"
date: 2023-10-31 23:17:00 +0700
categories: ["Technique Reverse", "Part 10 · Legacy: Delphi, VB6, AutoIt, AHK"]
tags: [reverse-engineering, legacy]
render_with_liquid: false
---
Visual Basic 6 came out in the late 90s but there's still a huge amount of internal software, small tools, and even malware written in it. Reversing VB6 has a big trap right from the start: two exe files look the same, both VB6, but the way you analyze them is completely different. The reason is the compile mode. Understanding this first saves you a whole session of fumbling around.

First, don't confuse VB6 with VB.NET. The names are similar but they're entirely different technologies. VB.NET compiles to IL and runs on the CLR, and you open it with dnSpy/ILSpy like any other .NET assembly (see Part 5 again). VB6 has nothing to do with .NET, it compiles to a very distinct form that this lesson covers. Recognizing which one you're holding is the first job, and Detect It Easy does it in a second.

## Signs of a VB6 file

Open the file in DIE or look at the import table, the surest sign is that it links to `msvbvm60.dll` (Microsoft Visual Basic Virtual Machine 6.0). Every VB6 program, however it was compiled, needs this runtime. Seeing `msvbvm60.dll` in the imports tells you right away it's VB6, not VB.NET, not C++.

Another sign is that the VB6 entry point always calls `ThunRTMain` (the function that starts the VB runtime). And the file contains a structure called the VB header (starting with the string "VB5!") describing forms, objects, and the project. This structure is a gold mine, specialized tools read it to rebuild the UI and the list of events.

## P-Code and Native, where everything is decided

When compiling VB6, the programmer picks one of two modes (in Project Properties, the Compile tab). This is the main trap.

In P-Code (Pseudo-Code) mode, the program is compiled to a VB-specific bytecode, and `msvbvm60.dll` acts as a virtual machine interpreting that bytecode at runtime, quite like how CPython runs .pyc or the JVM runs .class. When you open a P-Code exe in IDA, you see very little real x86 code, mostly calls into the runtime, because the real logic is in the P-Code bytecode. IDA doesn't understand P-Code, so it's almost useless to look at. But good news: P-Code is high-level bytecode that keeps quite a lot of information, so a specialized decompiler can recover it fairly cleanly, close to the original source.

In Native mode, the program is compiled straight to x86 like C/C++. Open IDA and you see real assembly, readable with the knowledge from Part 1. But don't celebrate yet: VB6 native code still calls the runtime constantly for everything (BSTR string management, Variant variables, form operations), so it's flooded with `__vba*` calls into `msvbvm60.dll`. Readable but cluttered, and paradoxically native is harder to restore to the original source than P-Code, because the compiler tore the logic into assembly and threw away the high-level structure.

Sounds backwards but it's true: with VB6, P-Code is usually easier to recover to near-source than native, because the bytecode keeps more information than optimized machine code. This is an important difference from the usual intuition (in other languages, native is always the hardest form).

To tell the two modes apart, look in DIE or a specialized tool. If the code is mostly calls into msvbvm60 with very little real x86 logic, it's P-Code. If there are lots of real assembly blocks mixed with runtime calls, it's native. VB Decompiler also reports the type as soon as you open the file.

## VB Decompiler, a nearly mandatory tool

For VB6, the central tool is VB Decompiler (there's a limited free version and a pro version). It does things IDA alone can't. It reads the VB header to rebuild the list of forms, controls, and event handlers (for example `Command1_Click`, `Form_Load`), which is the fastest way to know "when the OK button is clicked, which function runs". For P-Code, it decompiles the bytecode into something close to VB source, so you can read the logic directly. For native, it disassembles and annotates the runtime calls, which is easier to follow than raw IDA. It also lists strings and their references, helping you go from a message ("Wrong password") back to the check function, the familiar start-from-the-string technique.

A typical workflow is to open the exe in VB Decompiler, see whether it reports P-Code or native, open the form tree, find the event handler for the button or field related to the logic you care about (for example a registration button), and read the decompiled code there. If it's native and you need to go deeper, switch to IDA/x64dbg but bring along the function address info that VB Decompiler pointed out.

## Strings in VB6: BSTR, not C strings

A detail that often confuses beginners: VB6 uses BSTR for strings, which are Unicode (UTF-16) strings with a dword length right before the data pointer, and still ending in two null bytes. So when you look at strings in a hex editor or IDA, you see them in Unicode form (each ASCII character interleaved with a 00 byte), not plain ASCII strings like in C. String comparison in VB6 usually goes through the runtime function `__vbaStrCmp` rather than `strcmp`, so setting a breakpoint there when debugging native catches exactly the comparison spot.

## Lab

See [labs/10.2/](https://github.com/Haind03/Technique-Reverse/blob/main/labs/10.2). The task is to identify a VB6 exe through the `msvbvm60.dll` import, work out whether it's P-Code or native, then use VB Decompiler to open the forms and find the event handler holding the check logic.

## Key takeaways
The `msvbvm60.dll` import is a sure sign of VB6, which is completely different from VB.NET running on the CLR. VB6 has two modes, P-Code (bytecode running on the runtime, little real x86) and Native (real x86 but flooded with `__vba*` calls), and counterintuitively P-Code is usually easier to recover to near-source than native. VB Decompiler is the central tool, since it rebuilds forms and event handlers, decompiles P-Code, and annotates native. VB6 strings are BSTR (Unicode with a length prefix), compared through `__vbaStrCmp`.
