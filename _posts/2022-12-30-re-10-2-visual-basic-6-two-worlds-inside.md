---
title: "Lesson 10.2: Visual Basic 6, two worlds inside the same exe"
image:
  path: /assets/img/covers/re-10-2-visual-basic-6-two-worlds-inside.webp
  alt: "Lesson 10.2: Visual Basic 6, two worlds inside the same exe"
date: 2022-12-30 14:23:00 +0700
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

The goal is to tell VB6 apart from other kinds of programs, work out the compile mode (P-Code versus Native), and use VB Decompiler to find the logic through the forms and event handlers. You need any VB6 exe (plenty of old tools and shareware from the 2000s are VB6). If you have a machine with the Visual Basic 6 IDE, build two versions of the same project yourself, one P-Code and one Native, to compare. You also need Detect It Easy, VB Decompiler (the free version is enough for this lab, from the official site), and IDA Free or x64dbg for the native part.

Start by recognizing VB6. Open the exe in DIE, confirm it imports `msvbvm60.dll` and note what DIE says about the compiler. How do you tell this file apart from a VB.NET exe? Then determine the mode: open the exe in VB Decompiler and see whether it reports P-Code or Native. If you have both builds, compare which one VB Decompiler recovers closer to the source.

Next rebuild the forms. In VB Decompiler open the tree of forms and controls, list the forms and a few main controls (buttons, textboxes), and find the event handler of an important button, for example `Command1_Click`. Go into that handler and read the decompiled code. If the program has a check (a serial or a password), trace down to where the comparison happens.

If it is a native build, go deeper. Open it in IDA and find the calls to `__vbaStrCmp` (the string comparison). Set a breakpoint there in x64dbg (or OllyDbg), run, enter a wrong value and look at the two BSTR operands, which expose the correct value.

Two questions to think about. Why do you see very little real logic when you open a P-Code exe in plain IDA? And how does a VB6 string appear in a hex editor, and why?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

This writeup describes the procedure and the typical results you will see on a VB6 exe. The steps and function names are standard, and the specific numbers will differ from file to file.

In DIE, a VB6 exe reports the compiler as "Microsoft Visual Basic", and in the Import tab you see `msvbvm60.dll` with functions starting with `__vba` (for example `__vbaStrCmp`, `__vbaVarTstEq`) and ordinal-only functions from the runtime. VB.NET is different: it doesn't import `msvbvm60.dll`. Instead it has a CLI header (the COM Descriptor directory in the Optional Header, see Lessons 1.7 and 5.6) and imports `mscoree.dll`, and DIE reports ".NET" outright. In short, seeing `msvbvm60` means VB6, and seeing `mscoree` plus a CLI header means VB.NET.

VB Decompiler tells you the mode as soon as you open the file, with "Native Code" or "P-Code" in the status bar or the project title. If you build the same project both ways, the P-Code build gets recovered by VB Decompiler into code that looks a lot like the VB source (variable assignments, If/Then, clear function calls), because the bytecode keeps the high-level structure. The Native build gives x86 assembly annotated with runtime calls, with the logic broken into small pieces and harder to recover into the original If/Then. The familiar conclusion among VB6 people is that P-Code is easier to read back than native, which is the opposite of what intuition says.

The VB header stores the list of forms and controls. VB Decompiler reads it and shows a tree like:

```
Form1
  Command1 (CommandButton)   -> Command1_Click
  Text1 (TextBox)
  Label1 (Label)
```

Event handlers are named by the convention `<control name>_<event>`, so `Command1_Click` is the code that runs when Command1 is clicked. That is the fastest way to jump straight to the UI logic without reading from the start. In `Command1_Click` (or the handler of the relevant button) a P-Code build reads almost like source: take the text from Text1, compare it with a string or call a check function, branch to show a message. Going backwards from the message string ("Wrong" or "Correct") also leads here.

In a native build, string comparison goes through `__vbaStrCmp` (or `__vbaStrComp`). Set a breakpoint:

```
bp msvbvm60.__vbaStrCmp
```

Run it, enter a wrong value and, when it stops, look at the two BSTR parameters. One is the string you typed, and the other is often the correct string, laid bare. It is exactly the same technique as a breakpoint on `strcmp` in a C crackme (Lesson 2.5), only the runtime function name differs.

On the questions, P-Code is almost useless in plain IDA because the logic sits in P-Code bytecode that `msvbvm60.dll` interprets at run time, not in x86 code. IDA only sees the loader part and the calls into the runtime, never the logic, and you need a tool that understands P-Code (VB Decompiler) to read it. As for strings, VB6 stores them as Unicode UTF-16: each ASCII character is followed by an interleaved `00` byte (for example "OK" is `4F 00 4B 00`), with a length dword in front of the BSTR pointer and two null bytes at the end. So to find strings you have to turn on Unicode mode in the hex editor or IDA, and an ASCII search will miss them.

</details>

## Key takeaways
The `msvbvm60.dll` import is a sure sign of VB6, which is completely different from VB.NET running on the CLR. VB6 has two modes, P-Code (bytecode running on the runtime, little real x86) and Native (real x86 but flooded with `__vba*` calls), and counterintuitively P-Code is usually easier to recover to near-source than native. VB Decompiler is the central tool, since it rebuilds forms and event handlers, decompiles P-Code, and annotates native. VB6 strings are BSTR (Unicode with a length prefix), compared through `__vbaStrCmp`.
