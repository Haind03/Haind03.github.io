---
title: "Lesson 2.2: IDA for beginners, master the tool before the binary"
image:
  path: /assets/img/covers/re-2-2-ida-beginners-master-tool-before-binary.webp
  alt: "Lesson 2.2: IDA for beginners, master the tool before the binary"
date: 2022-04-12 23:38:00 +0700
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

There is a small crackme for you to practice exactly the workflow above, `crackme01.c`. It is harmless and fine to run on a normal machine. The aim is to drill the IDA routine: start from strings, use xrefs, rename, read the logic. Build it first. On Windows with the MSVC Developer Command Prompt:

```
cl /Fe:crackme01.exe crackme01.c
```

On Windows with MinGW:

```
x86_64-w64-mingw32-gcc crackme01.c -o crackme01.exe
```

On Linux:

```
gcc crackme01.c -o crackme01
```

Don't open `crackme01.c` to read it. The whole exercise is finding the password without the source.

Run the program, type a random password and see what it prints. Then open the built file in IDA and wait for auto-analysis to finish (AU: idle). Open the Strings window (`Shift+F12`) and look for a message about a right or wrong password. Double-click it to land in the data, then press `X` to see which function references it. Jump into that function and find the sub-function that does the real checking, and rename it (`N`) to `check_password`. Inside it, find the secret string the input is compared against, rename variables so they read well and add comments (`:`). If you have Hex-Rays, press `F5` to read the pseudocode and compare it with the assembly. Finally work out the correct password, run the program again and type it in to confirm you see "Correct!".

A few questions are worth thinking about afterwards. Why is going from strings faster than reading from `main`? What does the program check before comparing the strings (hint: look at a length comparison)? And if there were no Strings window, what other way would you have to locate the check function (hint: Imports, and functions like `strcmp`)?

<div class="lab-box">
<div class="lab-head"><b>LAB 2.2</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/2.2/src/crackme01.c" download><i class="fa-solid fa-file-code"></i>src/crackme01.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Don't read this if you haven't tried it yet, since the value of the lab is in the struggle. The correct password is:

```
R3v3rs3_M3
```

Type it into the program and you will see "Correct!".

In the Strings window (`Shift+F12`) you see a few interesting strings: `Enter password: `, `Correct! Congratulations, you solved the crackme.`, `Wrong password. Try again.`, and one that looks like a password, `R3v3rs3_M3`. Right at this step a sharp eye spots `R3v3rs3_M3` sitting oddly among the messages. That is the secret, because the programmer embedded the comparison string straight into the binary. The lesson is that hardcoding a secret string in native code protects nothing, since it is exposed in Strings immediately.

To confirm that `R3v3rs3_M3` really is the password and not something else, double-click it and press `X`. IDA shows it being loaded inside one function, right before a call to `strcmp` (or `strlen` and then `strcmp`). Rename that function to `check_password`. The pseudocode (F5) of the check function looks roughly like this:

```c
int check_password(const char *input)
{
    const char *secret = "R3v3rs3_M3";
    if (strlen(input) != strlen(secret))   // check the length first
        return 0;
    if (strcmp(input, secret) == 0)        // then compare character by character
        return 1;
    return 0;
}
```

Two things to notice. The program compares lengths first (a `cmp`/`jne` pair in the assembly), a small optimization that avoids comparing strings when the lengths already differ. Then `strcmp` compares everything and returns 1 on a match. Back in `main`, the return value of `check_password` decides whether to print "Correct!" or "Wrong password", following the usual `cmp`/`test` plus `j*` pattern from Lesson 1.3.

If you don't use Strings, there is another route. Open Imports, find `strcmp` and `strlen`, and press `X` on `strcmp` to go to where it is called, which also lands you in the check function. Starting from an API is the second way in after starting from strings.

What to take away: hardcoded strings are the first weakness of every beginner crackme, and the two fastest ways to locate logic are from strings (`Shift+F12` then `X`) and from imports (`strcmp`, `strcpy` and so on, then `X`). Renaming a function as soon as you understand it makes `main` read far more clearly.

</details>

## Common pitfalls

A common mistake is starting to read from the entry point and getting lost in the runtime's init code, when going from strings or imports is much faster. Another is forgetting to rename, leaving `sub_xxx` and `v1 v2 v3` as they are, and half an hour later not remembering which function is which. Some people click around before auto-analysis is done, see wrong results, and panic. And it's easy to mix up the static address in IDA with the real address at runtime in the debugger (ASLR, see Lesson 1.2).

## Key takeaways
Wait for auto-analysis to finish (AU: idle) before working. The five main windows are IDA View, Functions, Strings (`Shift+F12`), Imports, and Pseudocode (`F5`). `Space` switches graph/text, `G` jumps to an address, and `Esc`/`Ctrl+Enter` are back/forward.

The three golden habits are rename (`N`), xref (`X`), and comment (`:`), and you should record your understanding as soon as you have it. Going backwards from strings through `X` is the fastest way to locate logic. The full shortcut table is in the [cheatsheet](/posts/re-resources-cheatsheet-shortcuts-quick-reference/).
