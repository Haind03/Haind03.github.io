---
title: "Lesson 2.3: Ghidra basics, the free knife that's worth a lot"
date: 2022-04-13 09:56:00 +0700
categories: ["Technique Reverse", "Part 02 · The Toolkit"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
Ghidra is a reversing suite written by the NSA and open sourced in 2019, and the first question everyone asks is "what can a free tool do". The short answer: it has a decompiler that turns assembly into C-like pseudocode, runs on almost every architecture, and costs you nothing. For a beginner, that's a perfectly good reason to start with Ghidra instead of waiting until you can afford IDA Pro.

This lesson takes you through one full loop from opening Ghidra to reading a function's pseudocode. The full shortcut list is in the [cheatsheet](/posts/re-resources-cheatsheet-shortcuts-quick-reference/), here I only mention the ones that get used.

## A project, not opening the file directly

Unlike IDA (drag a file in and it runs), Ghidra makes you create a project first. Sounds annoying but there's a reason: a project gathers several related files in one place, keeps all your notes and analysis, and lets you compare multiple binaries with each other later.

Open Ghidra, choose File > New Project, choose Non-Shared Project (you're working alone), and set a name and a location. Then drag the file you want to analyze into the project window, or use File > Import File. Ghidra recognizes the format (PE, ELF, Mach-O) and the architecture itself, so usually you just leave the defaults and OK. Double-click the file you just imported to open CodeBrowser, the main working window. Ghidra asks "Analyze now?", so choose Yes, and when the analyzer list shows up just leave the defaults and Analyze.

Auto-analysis is the step where Ghidra scans the whole file: finding functions, building cross-references, recognizing strings, guessing data types. A small file finishes in seconds, a big one takes a bit longer. When the progress bar finishes you can start.

## CodeBrowser, the four windows you live in

The CodeBrowser interface looks messy at first, but there are really only four places you use all the time. The Listing (middle of the screen) is the disassembly, meaning assembly with addresses, comments, labels, and it's the most accurate original. The Decompiler (usually on the right) shows C-like pseudocode of the selected function. You open it by clicking a function, or pressing Ctrl+E, and it's where beginners read the most because it goes down easier than assembly. The Symbol Tree (on the left) lists functions, imports, exports, and labels, and it's the place to jump quickly to a function by name. The Data Type Manager (bottom left) is the store of data types, and when you want to apply a struct or a Windows type to a variable, you get it from here.

Listing and Decompiler are always in sync: click a line on one side and the other jumps along. A good habit is to read the Decompiler to get the idea, then glance at the Listing when you need instruction-level accuracy.

## Start from strings, the fastest way to get to work

Like in any RE tool, the fastest way to find "the interesting spot" in Ghidra is to work backwards from a string. Open Window > Defined Strings. A table of every string in the file appears. See a suspicious string like "Wrong password" or "Access granted"? Double-click it to jump to where it sits in the Listing, then see what references it.

To see references, put the cursor on the string (or function, variable) and press Ctrl+Shift+F (Find References To). Ghidra lists every place that uses it. The place that references the string "Wrong password" is almost certainly the password check function. Double-click and you're standing right in the function you were looking for, skipping thousands of lines of runtime initialization.

## Rename and retype, turning junk into something readable

After auto-analysis, functions without names are called things like `FUN_00401000`, variables are `local_8`, `uVar1`. Hard to read. The difference between someone who works slow but steady and someone drowning in `FUN_xxx` is this: whatever you understand, name it right away.

To rename, put the cursor on a function or variable, press L, and type the new name. For example if `FUN_00401000` turns out to hash a string, rename it to `hash_string`. To retype, press Ctrl+L to change a variable's type. A variable Ghidra guessed as `undefined4` that you know is an `int` or a struct pointer should be fixed, and the decompiler displays much more nicely. To comment, press the semicolon key to leave a note right at the line.

Every name you set makes the next function easier to read, because Ghidra propagates that name to everywhere that calls it. This isn't busywork to make things pretty, it's how you keep your head clear when functions pile on functions.

## Navigation, don't get lost

Double-click a function name or address to jump to it. The back/forward arrow buttons on the toolbar (or Alt+Left/Right arrow) take you back to where you just left, just like a browser, and you'll use them constantly when following a chain of calls. Press G to jump straight to a specific address.

## Ghidra vs IDA, and a few places people trip

If you come from IDA, most concepts are the same but the names and shortcuts differ, and this is what annoys people at first:

| Task | IDA | Ghidra |
|---|---|---|
| Rename | N | L |
| Decompile | F5 | Ctrl+E (or click the function) |
| Xrefs to | X | Ctrl+Shift+F |
| String list | Shift+F12 | Window > Defined Strings |
| Jump to address | G | G |

A few points IDA people often trip on. Ghidra does not open the decompiler with F5, because the decompiler is a panel that's always showing and you just click the function. Undo/Redo in Ghidra is Ctrl+Z/Ctrl+Y and it remembers analysis operations too, which is stronger than IDA on this point. And Ghidra saves automatically into the project, but remember File > Save (Ctrl+S) before closing to be safe.

On power: IDA's decompiler (Hex-Rays) usually produces slightly smoother code, especially with heavily optimized code, but Ghidra is free and the quality is very close, and the scripting side (Java or Python) for automation is extremely powerful, covered in [Lesson 18.1](https://github.com/Haind03/Technique-Reverse/tree/main/phan-18-nang-cao). For a learner, Ghidra loses nothing significant.

## Lab

The hands-on exercise and writeup are at [labs/2.3/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/2.3). You'll import the same small crackme into Ghidra, run auto-analysis, go from Defined Strings to the check function, rename and retype so the pseudocode is readable, then compare the feel with IDA in [Lesson 2.2](/posts/re-2-2-ida-beginners-master-tool-before-binary/). Doing both tools on the same binary is the fastest way to see where they're alike and different.

## Key takeaways
Ghidra makes you create a project first, then import, then Analyze (auto-analysis) before it's usable. The four main windows are Listing (asm), Decompiler (pseudocode), Symbol Tree (functions), and Data Type Manager (types). To get to work fast, use Window > Defined Strings, double-click a string, and press Ctrl+Shift+F to xref to the function that uses it. Rename with L, retype with Ctrl+L, comment with the semicolon, and name things as soon as you understand them. Compared to IDA the concepts are the same but the keys differ, and the decompiler is always showing, so no F5 is needed.
