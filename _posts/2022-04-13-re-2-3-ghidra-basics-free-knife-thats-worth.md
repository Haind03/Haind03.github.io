---
title: "Lesson 2.3: Ghidra basics, the free knife that's worth a lot"
image:
  path: /assets/img/covers/re-2-3-ghidra-basics-free-knife-thats-worth.webp
  alt: "Lesson 2.3: Ghidra basics, the free knife that's worth a lot"
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

On power: IDA's decompiler (Hex-Rays) usually produces slightly smoother code, especially with heavily optimized code, but Ghidra is free and the quality is very close, and the scripting side (Java or Python) for automation is extremely powerful, covered in [Lesson 18.1](/technique-reverse/). For a learner, Ghidra loses nothing significant.

## Lab

The goal is to go through a full round in Ghidra, from import to finding the password, and compare the experience with IDA from [Lesson 2.2](/posts/re-2-2-ida-beginners-master-tool-before-binary/). The binary reuses the idea of the lesson 2.2 lab (a crackme that compares a password), so you can reuse the file you built there or build `crackme01.c` on its own. Pick the build command for your system:

```
Linux/macOS:  gcc -O0 -no-pie -o crackme01 crackme01.c
MinGW (Win):  x86_64-w64-mingw32-gcc -O0 -o crackme01.exe crackme01.c
MSVC (Win):   cl /Od crackme01.c
```

I use `-O0` so the decompiler output stays close to the source, which suits a first time. Don't open `crackme01.c` to peek at the answer before you've tried it yourself.

Create a Non-Shared Project in Ghidra, import `crackme01`, answer Yes when asked to analyze, and let auto-analysis finish. Open Window > Defined Strings and find the two result messages. Ask yourself which one hints that this is where the right/wrong decision is made. Double-click the success string to jump to the Listing, then press Ctrl+Shift+F (Find References To) to find the function that references it, and check whether it is `main` or some other function that calls into it. Open the check function in the Decompiler, rename it (L) to `check_password`, and rename the parameter to `input` for readability. Then read the pseudocode: what does the function compare `input` against? Find the correct password, run the binary, type it in, and confirm you get "Access granted". Finally, if you did the lesson 2.2 lab, open the same binary in IDA and compare. Which job was faster, which keys differed, and which decompiler reads better to you?

A few hints. If Defined Strings doesn't show the string you expect, check that auto-analysis has actually finished (the bar at the bottom). The password sits right in the pseudocode as a string constant being compared, so there's no need to debug, reading is enough. And if the decompiler shows variables of type `undefined`, try retyping them (Ctrl+L) to `char *` or `int` to make them clearer.

<div class="lab-box">
<div class="lab-head"><b>LAB 2.3</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/2.3/src/crackme01.c" download><i class="fa-solid fa-file-code"></i>src/crackme01.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The password is `Gh1dra_R0cks`. Typing it gives "Access granted. Congratulations!".

After creating the project and importing `crackme01`, answer Yes to "Analyze now?" and leave the analyzers at their defaults. For a small binary like this, auto-analysis finishes in a few seconds, and you're done when the status bar at the bottom stops running.

Window > Defined Strings shows, among others, `Enter password: `, `Access granted. Congratulations!`, `Wrong password. Try again.` and `Gh1dra_R0cks`, which is the password itself, sitting in `.rodata`. The `Access granted` string marks the success branch. Notice that even `Gh1dra_R0cks` shows up here: plenty of easy crackmes leak the password in the strings table before you ever open a function.

For the xref step, double-click `Access granted...` to get to the Listing, put the cursor on it and press Ctrl+Shift+F. The reference leads back to `main`, since the result string is printed there. But if you xref the string `Gh1dra_R0cks` instead, it leads straight into the `check_password` function (named `FUN_...` at first in the Listing), because that is where the real comparison happens. In the Decompiler, put the cursor on the name of the `FUN_...` function that holds the comparison, press L and rename it to `check_password`, then rename the parameter to `input`. The pseudocode becomes noticeably easier to read right away.

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

The function compares the input character by character against the string constant `Gh1dra_R0cks`. That is the password. Ghidra may render the loop a little differently (with an internal index variable, calling `strlen` repeatedly), but the logic is the same: match the length, then match each character. To confirm, run the binary, type `Gh1dra_R0cks`, and the success message appears.

On the comparison with IDA, going from a string to a function takes about the same number of steps in both: IDA uses Shift+F12 to open Strings and X for xrefs, while Ghidra uses Defined Strings and then Ctrl+Shift+F. As decompilers, both read the password out easily on `-O0` code. Hex-Rays (IDA) tends to fold `strlen` a bit more neatly, while Ghidra spells it out more. Renaming is N in IDA and L in Ghidra: different key, same effect. In practice the two tools are on par for something this size. The big differences only show up on complex binaries and when you need scripting, where each tool has its own strengths.

</details>

## Key takeaways
Ghidra makes you create a project first, then import, then Analyze (auto-analysis) before it's usable. The four main windows are Listing (asm), Decompiler (pseudocode), Symbol Tree (functions), and Data Type Manager (types). To get to work fast, use Window > Defined Strings, double-click a string, and press Ctrl+Shift+F to xref to the function that uses it. Rename with L, retype with Ctrl+L, comment with the semicolon, and name things as soon as you understand them. Compared to IDA the concepts are the same but the keys differ, and the decompiler is always showing, so no F5 is needed.
