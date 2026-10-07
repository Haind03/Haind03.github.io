---
title: "Lesson 2.3: Ghidra basics, the free knife that's worth a lot"
date: 2026-10-06 08:19:00 +0700
categories: ["Technique Reverse", "Part 02 · The Toolkit"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
Ghidra is a reversing suite written by the NSA and open sourced in 2019, and the first question everyone asks is "what can a free tool do". The short answer: it has a decompiler that turns assembly into C-like pseudocode, runs on almost every architecture, and costs you nothing. For a beginner, that's a perfectly good reason to start with Ghidra instead of waiting until you can afford IDA Pro.

This lesson takes you through one full loop from opening Ghidra to reading a function's pseudocode. The full shortcut list is in the [cheatsheet](/posts/tr-tai-nguyen-cheatsheet/), here I only mention the ones that get used.

## A project, not opening the file directly

Unlike IDA (drag a file in and it runs), Ghidra makes you create a project first. Sounds annoying but there's a reason: a project gathers several related files in one place, keeps all your notes and analysis, and lets you compare multiple binaries with each other later.

Steps:
1. Open Ghidra, choose File > New Project, choose Non-Shared Project (you're working alone), set a name and a location.
2. Drag the file you want to analyze into the project window, or File > Import File. Ghidra recognizes the format (PE, ELF, Mach-O) and the architecture itself. Usually just leave the defaults and OK.
3. Double-click the file you just imported to open CodeBrowser, the main working window.
4. Ghidra asks "Analyze now?", choose Yes. The analyzer list shows up, just leave the defaults and Analyze.

Auto-analysis is the step where Ghidra scans the whole file: finding functions, building cross-references, recognizing strings, guessing data types. A small file finishes in seconds, a big one takes a bit longer. When the progress bar finishes you can start.

## CodeBrowser, the four windows you live in

The CodeBrowser interface looks messy at first, but there are really only four places you use all the time:

- **Listing** (middle of the screen): the disassembly, meaning assembly with addresses, comments, labels. This is the most accurate original.
- **Decompiler** (usually on the right): C-like pseudocode of the selected function. Open it by clicking a function, or pressing Ctrl+E. This is where beginners read the most because it goes down easier than assembly.
- **Symbol Tree** (on the left): the list of functions (Functions), imports, exports, labels. The place to jump quickly to a function by name.
- **Data Type Manager** (bottom left): the store of data types. When you want to apply a struct or a Windows type to a variable, you get it from here.

Listing and Decompiler are always in sync: click a line on one side and the other jumps along. A good habit is to read the Decompiler to get the idea, then glance at the Listing when you need instruction-level accuracy.

## Start from strings, the fastest way to get to work

Like in any RE tool, the fastest way to find "the interesting spot" in Ghidra is to work backwards from a string. Open Window > Defined Strings. A table of every string in the file appears. See a suspicious string like "Wrong password" or "Access granted"? Double-click it to jump to where it sits in the Listing, then see what references it.

To see references, put the cursor on the string (or function, variable) and press Ctrl+Shift+F (Find References To). Ghidra lists every place that uses it. The place that references the string "Wrong password" is almost certainly the password check function. Double-click and you're standing right in the function you were looking for, skipping thousands of lines of runtime initialization.

## Rename and retype, turning junk into something readable

After auto-analysis, functions without names are called things like `FUN_00401000`, variables are `local_8`, `uVar1`. Hard to read. The difference between someone who works slow but steady and someone drowning in `FUN_xxx` is this: whatever you understand, name it right away.

- **Rename**: put the cursor on a function or variable, press **L**, type the new name. For example if `FUN_00401000` turns out to hash a string, rename it to `hash_string`.
- **Retype**: press **Ctrl+L** to change a variable's type. A variable Ghidra guessed as `undefined4` that you know is an `int` or a struct pointer, fix it, and the decompiler displays much more nicely.
- **Comment**: press **;** to leave a note right at the line.

Every name you set makes the next function easier to read, because Ghidra propagates that name to everywhere that calls it. This isn't busywork to make things pretty, it's how you keep your head clear when functions pile on functions.

## Navigation, don't get lost

- Double-click a function name or address to jump to it.
- The back/forward arrow buttons on the toolbar (or Alt+Left/Right arrow) to return to where you just left, just like a browser. Use them constantly when following a chain of calls.
- Press **G** to jump straight to a specific address.

## Ghidra vs IDA, and a few places people trip

If you come from IDA, most concepts are the same but the names and shortcuts differ, and this is what annoys people at first:

| Task | IDA | Ghidra |
|---|---|---|
| Rename | N | L |
| Decompile | F5 | Ctrl+E (or click the function) |
| Xrefs to | X | Ctrl+Shift+F |
| String list | Shift+F12 | Window > Defined Strings |
| Jump to address | G | G |

A few points IDA people often trip on:
- Ghidra does **not** open the decompiler with F5. The decompiler is a panel that's always showing, you just click the function.
- Undo/Redo in Ghidra is Ctrl+Z/Ctrl+Y and it remembers analysis operations too, stronger than IDA on this point.
- Ghidra saves automatically into the project, but remember File > Save (Ctrl+S) before closing to be safe.

On power: IDA's decompiler (Hex-Rays) usually produces slightly smoother code, especially with heavily optimized code, but Ghidra is free and the quality is very close, and the scripting side (Java or Python) for automation is extremely powerful, covered in [Lesson 18.1](https://github.com/Haind03/Technique-Reverse/tree/main/phan-18-nang-cao). For a learner, Ghidra loses nothing significant.

## Lab

The hands-on exercise and writeup are at [labs/2.3/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/2.3). You'll import the same small crackme into Ghidra, run auto-analysis, go from Defined Strings to the check function, rename and retype so the pseudocode is readable, then compare the feel with IDA in [Lesson 2.2](/posts/tr-2-2-ida-co-ban/). Doing both tools on the same binary is the fastest way to see where they're alike and different.

## Key takeaways
- Ghidra makes you create a project first, then import, then Analyze (auto-analysis) before it's usable.
- Four main windows: Listing (asm), Decompiler (pseudocode), Symbol Tree (functions), Data Type Manager (types).
- Getting to work fast: Window > Defined Strings, double-click a string, Ctrl+Shift+F to xref to the function that uses it.
- Rename with L, retype with Ctrl+L, comment with the semicolon. Name things as soon as you understand them.
- Compared to IDA: same concepts, different keys. The decompiler is always showing, no F5 needed.
