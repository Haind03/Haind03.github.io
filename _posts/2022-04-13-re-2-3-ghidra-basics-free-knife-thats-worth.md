---
title: "Lesson 2.3: Ghidra basics"
image:
  path: /assets/img/covers/re-2-3-ghidra-basics-free-knife-thats-worth.webp
  alt: "Lesson 2.3: Ghidra basics"
date: 2022-04-13 09:56:00 +0700
categories: ["Reverse Engineering", "Part 02 · The Toolkit"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
Ghidra is a reversing suite written by the NSA and open sourced in 2019. People ask what a free tool can do. It has a decompiler that turns assembly into C-like pseudocode, runs on almost every architecture, and costs nothing. For a beginner that's a good enough reason to start with Ghidra instead of waiting until you can afford IDA Pro.

This lesson goes through one full loop, from opening Ghidra to reading a function's pseudocode. The full shortcut list is in the [cheatsheet](/posts/re-resources-cheatsheet-shortcuts-quick-reference/), here I only mention the ones we use.

## Projects

Unlike IDA (drag a file in and it runs), Ghidra makes you create a project first. It's a bit annoying, but a project gathers related files in one place, keeps your notes and analysis, and lets you compare multiple binaries later.

Open Ghidra, choose File > New Project, choose Non-Shared Project (you're working alone), and set a name and a location. Then drag the file you want to analyze into the project window, or use File > Import File. Ghidra recognizes the format (PE, ELF, Mach-O) and the architecture itself, so usually you leave the defaults and click OK. Double-click the imported file to open CodeBrowser, the main working window. Ghidra asks "Analyze now?". Choose Yes, and when the analyzer list shows up leave the defaults and click Analyze.

Auto-analysis is where Ghidra scans the whole file, finding functions, building cross-references, recognizing strings, guessing data types. A small file finishes in seconds, a big one takes longer. When the progress bar finishes you can start.

## CodeBrowser

The CodeBrowser interface looks messy at first, but you only use four places all the time. The Listing (middle of the screen) is the disassembly, which is assembly with addresses, comments, labels. It's the most accurate view of the original. The Decompiler (usually on the right) shows C-like pseudocode of the selected function. You open it by clicking a function or pressing Ctrl+E, and beginners read it the most because it's easier than assembly. The Symbol Tree (on the left) lists functions, imports, exports, and labels, and it's where you jump to a function by name. The Data Type Manager (bottom left) stores data types, and when you want to apply a struct or a Windows type to a variable, you get it from here.

Listing and Decompiler stay in sync. Click a line on one side and the other jumps along. I usually read the Decompiler to get the idea, then check the Listing when I need instruction-level accuracy.

## Start from strings

As in any RE tool, the fastest way to find the interesting spot in Ghidra is to work backwards from a string. Open Window > Defined Strings to get a table of every string in the file. See something suspicious like "Wrong password" or "Access granted"? Double-click it to jump to where it sits in the Listing, then see what references it.

To see references, put the cursor on the string (or function, variable) and press Ctrl+Shift+F (Find References To). Ghidra lists every place that uses it. The place that references "Wrong password" is almost certainly the password check function. Double-click and you're in the function you were looking for, skipping thousands of lines of runtime initialization.

## Rename and retype

After auto-analysis, functions without names are called things like `FUN_00401000`, and variables are `local_8`, `uVar1`. That's hard to read. Whatever you understand, name it right away, or you'll drown in `FUN_xxx`.

To rename, put the cursor on a function or variable, press L, and type the new name. For example if `FUN_00401000` turns out to hash a string, rename it to `hash_string`. To retype, press Ctrl+L to change a variable's type. If Ghidra guessed `undefined4` for something you know is an `int` or a struct pointer, fix it and the decompiler output gets much nicer. To comment, press the semicolon key to leave a note at the line.

Every name you set makes the next function easier to read, because Ghidra propagates the name to everywhere that calls it. It isn't busywork, it keeps your head clear when functions pile on functions.

## Navigation

Double-click a function name or address to jump to it. The back/forward arrow buttons on the toolbar (or Alt+Left/Right arrow) take you back to where you just were, and you'll use them constantly when following a chain of calls. Press G to jump to a specific address.

## Ghidra vs IDA

If you come from IDA, most concepts are the same but the names and shortcuts differ, which annoys people at first:

| Task | IDA | Ghidra |
|---|---|---|
| Rename | N | L |
| Decompile | F5 | Ctrl+E (or click the function) |
| Xrefs to | X | Ctrl+Shift+F |
| String list | Shift+F12 | Window > Defined Strings |
| Jump to address | G | G |

IDA people often trip on a few things. Ghidra doesn't open the decompiler with F5, since the decompiler is a panel that's always showing and you just click the function. Undo/Redo in Ghidra is Ctrl+Z/Ctrl+Y and it remembers analysis operations too, which is better than IDA here. Ghidra saves automatically into the project, but I still press File > Save (Ctrl+S) before closing to be safe.

IDA's decompiler (Hex-Rays) usually produces slightly smoother code, especially on heavily optimized code. Ghidra is free and the quality is very close, and scripting (Java or Python) for automation is very good, covered in [Lesson 18.1](/reverse-engineering/). For a learner, Ghidra loses nothing significant.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 2.3</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/2.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/2.3/src/crackme01.c" download><i class="fa-solid fa-download"></i>src/crackme01.c</a>
</div>
</div>

The goal is to do a full round in Ghidra, from import to finding the password, and compare the experience with IDA from [Lesson 2.2](/posts/re-2-2-ida-beginners-master-tool-before-binary/). The binary reuses the idea of the lesson 2.2 lab (a crackme that compares a password), so you can reuse the file you built there or build `crackme01.c` on its own. Pick the build command for your system:

```
Linux/macOS:  gcc -O0 -no-pie -o crackme01 crackme01.c
MinGW (Win):  x86_64-w64-mingw32-gcc -O0 -o crackme01.exe crackme01.c
MSVC (Win):   cl /Od crackme01.c
```

I use `-O0` so the decompiler output stays close to the source, which suits a first time. Don't open `crackme01.c` to peek at the answer before you've tried it yourself.

Create a Non-Shared Project in Ghidra, import `crackme01`, answer Yes when asked to analyze, and let auto-analysis finish. Open Window > Defined Strings and find the two result messages. Which one hints that this is where the right/wrong decision is made? Double-click the success string to jump to the Listing, then press Ctrl+Shift+F (Find References To) to find the function that references it, and check whether it is `main` or some other function that calls into it. Open the check function in the Decompiler, rename it (L) to `check_password`, and rename the parameter to `input` for readability. Then read the pseudocode. What does the function compare `input` against? Find the correct password, run the binary, type it in, and confirm you get "Access granted". Finally, if you did the lesson 2.2 lab, open the same binary in IDA and compare. Which job was faster, which keys differed, and which decompiler reads better to you?

A few hints. If Defined Strings doesn't show the string you expect, check that auto-analysis has actually finished (the bar at the bottom). The password sits in the pseudocode as a string constant being compared, so you don't need to debug, reading is enough. If the decompiler shows variables of type `undefined`, try retyping them (Ctrl+L) to `char *` or `int` to make them clearer.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The password is `Gh1dra_R0cks`. Typing it gives "Access granted. Congratulations!".

After creating the project and importing `crackme01`, answer Yes to "Analyze now?" and leave the analyzers at their defaults. For a small binary like this, auto-analysis finishes in a few seconds, and you're done when the status bar at the bottom stops running.

Window > Defined Strings shows, among others, `Enter password: `, `Access granted. Congratulations!`, `Wrong password. Try again.` and `Gh1dra_R0cks`, which is the password itself, sitting in `.rodata`. The `Access granted` string marks the success branch. Even `Gh1dra_R0cks` shows up here, and plenty of easy crackmes leak the password in the strings table before you ever open a function.

For the xref step, double-click `Access granted...` to get to the Listing, put the cursor on it and press Ctrl+Shift+F. The reference leads back to `main`, since the result string is printed there. If you xref the string `Gh1dra_R0cks` instead, it leads straight into the `check_password` function (named `FUN_...` at first in the Listing), because that's where the real comparison happens. In the Decompiler, put the cursor on the name of the `FUN_...` function that holds the comparison, press L and rename it to `check_password`, then rename the parameter to `input`. The pseudocode gets noticeably easier to read right away.

After the cleanup, the decompiler gives roughly this:

```c
int check_password(char *input)
{
    char *secret = "Gh1dra_R0cks";
    if (strlen(input) != strlen(secret))
        return 0;
    for (i = 0; i < strlen(secret); i++) {
        if (input[i] != secret[i])
            return 0;
    }
    return 1;
}
```

The function compares the input character by character against the string constant `Gh1dra_R0cks`. That's the password. Ghidra may render the loop a little differently (with an internal index variable, calling `strlen` repeatedly), but the logic is the same, which is to match the length, then match each character. To confirm, run the binary, type `Gh1dra_R0cks`, and the success message appears.

Compared with IDA, going from a string to a function takes about the same number of steps. IDA uses Shift+F12 to open Strings and X for xrefs, while Ghidra uses Defined Strings and then Ctrl+Shift+F. As decompilers, both read the password out easily on `-O0` code. Hex-Rays (IDA) tends to fold `strlen` a bit more neatly, while Ghidra spells it out more. Renaming is N in IDA and L in Ghidra, a different key with the same effect. For something this size the two tools are on par. The big differences only show up on complex binaries and when you need scripting.

</details>

## Key takeaways
Ghidra makes you create a project first, then import, then Analyze (auto-analysis) before it's usable. The four main windows are Listing (asm), Decompiler (pseudocode), Symbol Tree (functions), and Data Type Manager (types). To get to work fast, use Window > Defined Strings, double-click a string, and press Ctrl+Shift+F to xref to the function that uses it. Rename with L, retype with Ctrl+L, comment with the semicolon, and name things as soon as you understand them. Compared to IDA the concepts are the same but the keys differ, and the decompiler is always showing, so no F5 is needed.
