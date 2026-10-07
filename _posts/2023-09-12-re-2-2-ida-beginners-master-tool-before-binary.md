---
title: "Lesson 2.2: IDA for beginners, master the tool before the binary"
date: 2023-09-12 20:26:00 +0700
categories: ["Technique Reverse", "Part 02 · The Toolkit"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
IDA is the name you hear most when you first get into this field, and also the one that discourages the most people in the first ten minutes. A screen full of windows, strange shortcuts, a pile of `sub_401000` that tell you nothing. But IDA isn't hard, it's just big. This lesson goes through exactly the things you'll use 90% of the time, and skips the rest until you really need it.

The series uses IDA Free as the baseline because it's free and enough to learn x86/x64. The Pro version adds the Hex-Rays decompiler (the F5 key) and more architectures, but the basic operations are identical.

## Opening a file for the first time

Drag a file into IDA and it shows a dialog asking for the file type and architecture. For a normal PE or ELF, just leave the defaults and click OK, IDA detects it itself. Then it runs auto-analysis: it scans the whole file, finds functions, identifies code and data, and marks strings. Wait for the progress indicator at the bottom to finish (the text "AU: idle") before you start working, and don't click around while it's still analyzing.

## The windows you'll live in

IDA has a huge number of windows, but a day of work revolves around about five. Reopen any you accidentally closed through the View > Open subviews menu.

The IDA View (disassembly) is where you read assembly. It has two modes, graph view (blocks connected by arrows, easy to see the flow) and text view (a linear listing), and you press `Space` to switch between them. Beginners should use graph view to see the branches clearly. The Functions window, on the left, lists every function IDA found, and you double-click to jump to one. It's the table of contents of the binary.

The Strings window lists every string in the file and opens with `Shift+F12`. It's the golden window for beginners, covered in detail below. Imports shows the API functions the program calls from external DLLs, and looking at that list you can guess what the program does (touches files, registry, network...). Pseudocode is the Hex-Rays output, C-like pseudo code, which you open with `F5` when the cursor is inside a function (Pro version only).

## Moving around without getting lost

Reversing is constantly jumping back and forth between functions. Master a few operations and you'll never get lost. `G` lets you type an address or name to jump straight to it. Double-clicking a function or variable name jumps to its definition, and double-clicking a string or constant also jumps to where it's defined. `Esc` goes back to where you just left (like a browser's Back button), and `Ctrl+Enter` goes forward. You'll press these two constantly.

Tip: just treat IDA like a web browser. You click a link (a function name), read, then `Esc` to go back. Being fluent with back/forward is half the road to mastering IDA.

## Three habits that turn you from a rookie into someone who gets things done

This is the most important part of the whole lesson. IDA is powerful not because it understands code by itself, but because it lets you record your understanding on top of the code. The more you record, the easier the next function is to read.

### Rename (the N key)

Put the cursor on a function `sub_401500`, a variable `v3`, or a label, press `N`, and type a meaningful name. Just figured out that `sub_401500` compares two strings? Rename it `compare_password`. Next time you see where it's called, you read the meaning right away instead of having to open it again. Every name you set is an investment that pays interest.

### Cross-reference (the X key)

This is IDA's superpower. Put the cursor on a function, a global variable, or a string and press `X`, and IDA lists every place that references it. See the string "Wrong password"? Press `X` on it, and IDA immediately points to which function uses that string, and that function is almost certainly where the password check is. Going backwards from data to code is the fastest locating technique for beginners.

### Comment (the colon key)

Press `:` to add a comment to a line, `;` for a repeatable comment (shown at every place that references it). The moment you understand what a section does, write it down. Three days later when you come back, your own comment saves you from reading it all again from scratch.

## Start from strings, the number one tactic for beginners

For most crackmes and small programs, the fastest way to find "the interesting spot" isn't to read from `main`, but to go backwards from strings. Open the Strings window (`Shift+F12`) and look for a string that hints at logic: "Correct!", "Wrong password", "Access granted", "Invalid license". Double-click it to jump to where the string is defined in data, then press `X` to see which function uses that string. Jump into that function, and you're standing right in the middle of the checking logic.

Why it works: the program has to print a message to the user, so the message string always sits next to the code that decides what to print. A string is a thread leading straight to the heart of the logic.

## Decompile with F5

If you have the Pro version with Hex-Rays, put the cursor in a function and press `F5`, and IDA rebuilds C-like pseudo code. It's much easier to read than assembly. Pseudocode is a guess, not the original source, so it can translate slightly off, especially with heavily optimized or obfuscated code. You can still rename (`N`) and set types (`Y`) right in the pseudocode window, and the changes carry over to the assembly. When the pseudocode looks nonsensical, drop down to assembly to verify. The two windows complement each other.

What if you don't have F5? You can still do RE normally, just reading assembly more slowly. Ghidra (Lesson 2.3) gives you a free decompiler if you need one.

## Lab

There's a small crackme for you to practice exactly the workflow above at `labs/2.2/`. Task: build it, open it in IDA, use the Strings window to find the message, go `X` to the checking function, rename the functions and variables to make them readable, then find the correct password. The step-by-step writeup is in `labs/2.2/solution.md`, but struggle with it yourself first.

## Common pitfalls

A common mistake is starting to read from the entry point and getting lost in the runtime's init code, when going from strings or imports is much faster. Another is forgetting to rename, leaving `sub_xxx` and `v1 v2 v3` as they are, and half an hour later not remembering which function is which. Some people click around before auto-analysis is done, see wrong results, and panic. And it's easy to mix up the static address in IDA with the real address at runtime in the debugger (ASLR, see Lesson 1.2).

## Key takeaways
Wait for auto-analysis to finish (AU: idle) before working. The five main windows are IDA View, Functions, Strings (`Shift+F12`), Imports, and Pseudocode (`F5`). `Space` switches graph/text, `G` jumps to an address, and `Esc`/`Ctrl+Enter` are back/forward.

The three golden habits are rename (`N`), xref (`X`), and comment (`:`), and you should record your understanding as soon as you have it. Going backwards from strings through `X` is the fastest way to locate logic. The full shortcut table is in the [cheatsheet](/posts/re-resources-cheatsheet-shortcuts-quick-reference/).
