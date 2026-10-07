---
title: "Lesson 5.3: Debugging .NET without source using dnSpy"
date: 2023-10-01 21:20:00 +0700
categories: ["Technique Reverse", "Part 05 · C# and .NET"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
With native code, to debug you have to wrestle with addresses, registers, stack frames. With .NET it's completely different, and this is when you see why RE people like running into a .NET program: dnSpy lets you set a breakpoint right on the line of C# it just decompiled from a file with no source at all, then run, stop, look at variables, edit variables, just like debugging your own project in Visual Studio. It sounds a bit absurd, but it's true, and this lesson shows you how to take advantage of it.

## Why managed debugging is so easy

Recall [Lesson 5.1](/posts/re-5-1-net-internals-why-decompiling-gives-back/): a .NET assembly carries full metadata and IL. dnSpy decompiles the IL into C#, but more importantly, it knows which IL instructions each line of C# corresponds to. When you set a breakpoint on a line, dnSpy sets a real breakpoint at the matching IL offset. The CLR stops there, and because the metadata keeps the names of local variables, parameters, and fields intact, dnSpy displays everything with proper names.

Compared with native: in x64dbg you look at `[rbp-4]` and have to guess what variable that is. In dnSpy you see `int attempts = 3` directly. The gap is exactly the gap between reading hex and reading words.

dnSpy is already in this repo, in the parent folder `dnSpy-net-win64` (run `dnSpy.exe`), no extra installation needed.

## Two ways to start: Start and Attach

There are two situations. With Start, dnSpy launches the program itself under a debugger: open the assembly in dnSpy, click Start (F5), and pick the right executable. Use it when you want to debug from the beginning and catch code that runs early. With Attach, the program is already running and you attach the debugger: Debug menu, Attach to Process, pick the .NET process. Use it when you want to catch it in a running state, or when the program is started by something else.

For a simple crackme, just use Start to keep it tidy.

## Where to set breakpoints

The process is exactly like native but easier: use static first to narrow things down, then set a breakpoint there. Open the assembly, use search (Ctrl+Shift+K) or browse the tree to find message strings like "Wrong" or "Correct". Click the string, and use Analyze to see which method uses it. That's the check function.

In the decompiled C# of that function, click the left margin of the line you want to stop at (or put the cursor there and press F9) to toggle a breakpoint, and a red dot appears. The best spot is right at the comparison line: `if (input == password)` or `if (CheckSerial(...))`.

## Once stopped, what to look at

When the breakpoint hits, the program freezes and dnSpy highlights the line about to run. Now you have several windows. Locals shows every local variable and parameter with its current value, and it's where the answer often sits: if the function compares `input` with a variable `expected`, looking at Locals shows you right away that `expected` holds the correct serial. In Watch you add expressions you want to track yourself, for example `input.Length`. Call Stack shows the chain of functions that were called to get here, so you know where you are in the flow, and Immediate runs C# expressions right at the stop.

The familiar control keys: F10 step over (step past, without going inside child functions), F11 step into (go inside), Shift+F11 step out (run to the end of the current function and then stop), F5 continue.

## The strongest trick: edit variables at runtime

This is what makes .NET debugging a weapon. When stopped at `if (input == password)`, you don't need to know what the password is to get past the check. In the Locals window, double-click the value of the condition variable and edit it.

For example, a function returns `bool isValid`. You let it run to the line `return isValid`, set a breakpoint, and when it stops, change `isValid` from `false` to `true` right in Locals, then F5. The program thinks you entered the right thing. This is a way to get past a check without understanding the algorithm, useful for confirming "this really is the spot that decides" before sitting down to read carefully.

You can also edit string variables: if you see `expected = "S3cr3t"` in Locals, you already have the answer, nothing to edit.

## Conditional breakpoints, when a loop runs many times

If the check function sits in a loop that runs hundreds of times, stopping on every iteration is exhausting. Right-click the breakpoint, choose Edit Breakpoint (or Settings), and set a condition like `i == 10` or `c == 'X'`. dnSpy only stops when the condition is true. Like x64dbg's conditional breakpoints but written in C# syntax, which is much nicer.

## A tidy working rhythm

Put together, it's a process you'll repeat over and over. You start with static in dnSpy/ILSpy, finding the check function through strings and Analyze. Then you set a breakpoint at the comparison line, Start, and enter a wrong value to test. When it stops, read Locals to get the right value, or edit the condition variable to get past. If needed, use a conditional breakpoint to catch the right iteration.

Most entry-level .NET crackmes fall to exactly these steps. Samples that have been obfuscated are harder, and [Lesson 5.5](/posts/re-5-5-net-obfuscators-strip-them/) handles those.

## Lab

The exercise is in `labs/5.3/`: debug a small .NET crackme with dnSpy, set a breakpoint at the comparison, read the variables to get the answer, then try editing the condition variable to get past the check without knowing the password. There's a build guide (needs the dotnet SDK) and a step-by-step writeup in `solution.md`.

## Key takeaways
dnSpy maps decompiled C# lines back to the exact IL, so you can set breakpoints directly on code with no source. Use Start to run from the beginning and Attach to hook into a running process. Locals is where the right value often shows up, so look there before sitting down to read the algorithm.

You can edit the condition variable at runtime (for example `isValid = true`) to get past a check without understanding the logic. Conditional breakpoints are written in C# syntax, which is handy for loops.
