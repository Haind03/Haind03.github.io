---
title: "Lesson 5.3: Debugging .NET without source using dnSpy"
image:
  path: /assets/img/covers/re-5-3-debugging-net-without-source-using-dnspy.webp
  alt: "Lesson 5.3: Debugging .NET without source using dnSpy"
date: 2022-08-16 09:08:00 +0700
categories: ["Technique Reverse", "Part 05 · C# and .NET"]
tags: [reverse-engineering, dotnet]
render_with_liquid: false
---
Debugging native code means dealing with addresses, registers, stack frames. .NET is a lot easier. dnSpy lets you set a breakpoint on a line of C# it decompiled from a file with no source at all, then run, stop, look at variables and edit them, just like debugging your own project in Visual Studio. It sounds a bit absurd, but it works, and this lesson shows how to use it.

## Why managed debugging is easy

Recall [Lesson 5.1](/posts/re-5-1-net-internals-why-decompiling-gives-back/): a .NET assembly carries full metadata and IL. dnSpy decompiles the IL into C#, and it also knows which IL instructions each line of C# corresponds to. When you set a breakpoint on a line, dnSpy sets a real breakpoint at the matching IL offset. The CLR stops there, and because the metadata keeps the names of local variables, parameters, and fields, dnSpy displays everything with proper names.

In x64dbg you look at `[rbp-4]` and have to guess what variable that is. In dnSpy you see `int attempts = 3` directly.

dnSpy is a portable download (run `dnSpy.exe`), no installation needed.

## Start and Attach

There are two situations. With Start, dnSpy launches the program itself under a debugger: open the assembly in dnSpy, click Start (F5), and pick the right executable. Use it when you want to debug from the beginning and catch code that runs early. With Attach, the program is already running and you attach the debugger: Debug menu, Attach to Process, pick the .NET process. Use it when you want to catch it in a running state, or when the program is started by something else.

For a simple crackme, just use Start.

## Where to set breakpoints

It's the same process as native but easier: use static first to narrow things down, then set a breakpoint there. Open the assembly, use search (Ctrl+Shift+K) or browse the tree to find message strings like "Wrong" or "Correct". Click the string, and use Analyze to see which method uses it. That's the check function.

In the decompiled C# of that function, click the left margin of the line you want to stop at (or put the cursor there and press F9) to toggle a breakpoint, and a red dot appears. The best spot is the comparison line: `if (input == password)` or `if (CheckSerial(...))`.

## Once stopped

When the breakpoint hits, the program freezes and dnSpy highlights the line about to run. There are several windows. Locals shows every local variable and parameter with its current value, and the answer is often right there: if the function compares `input` with a variable `expected`, Locals shows that `expected` holds the correct serial. In Watch you add expressions you want to track, for example `input.Length`. Call Stack shows the chain of functions called to get here, and Immediate runs C# expressions at the stop.

The control keys: F10 step over (don't go inside child functions), F11 step into (go inside), Shift+F11 step out (run to the end of the current function and then stop), F5 continue.

## Editing variables at runtime

This is what makes .NET debugging so convenient. When stopped at `if (input == password)`, you don't need to know the password to get past the check. In the Locals window, double-click the value of the condition variable and edit it.

For example, a function returns `bool isValid`. You let it run to the line `return isValid`, set a breakpoint, and when it stops, change `isValid` from `false` to `true` in Locals, then F5. The program thinks you entered the right thing. You get past the check without understanding the algorithm, which is useful for confirming that this really is the spot that decides before you sit down to read carefully.

If you see `expected = "S3cr3t"` in Locals, you already have the answer, nothing to edit.

## Conditional breakpoints

If the check function sits in a loop that runs hundreds of times, stopping on every iteration is tiring. Right-click the breakpoint, choose Edit Breakpoint (or Settings), and set a condition like `i == 10` or `c == 'X'`. dnSpy only stops when the condition is true. It's like x64dbg's conditional breakpoints but written in C# syntax, which is nicer.

## A working rhythm

Put together, it goes like this. Start with static in dnSpy/ILSpy, finding the check function through strings and Analyze. Then set a breakpoint at the comparison line, Start, and enter a wrong value to test. When it stops, read Locals to get the right value, or edit the condition variable to get past. If needed, use a conditional breakpoint to catch the right iteration.

Most entry-level .NET crackmes fall to these steps. Obfuscated samples are harder, and [Lesson 5.5](/posts/re-5-5-net-obfuscators-strip-them/) handles those.

## Lab

In this lab you debug a small .NET crackme with dnSpy, without any source code. You set a breakpoint at the comparison, read the variables while the program runs, and then edit the condition variable to get past the check without knowing the serial. The crackme is `Program.cs`. You need dnSpy (run `dnSpy.exe`) and the dotnet SDK to build it.

Create a console project, replace its default `Program.cs` with the provided one, and build in Debug configuration, which lets dnSpy map lines more accurately.

```
dotnet new console -o crackme53
copy Program.cs crackme53/Program.cs   (replace the default file)
cd crackme53
dotnet build -c Debug
```

The output is `crackme53/bin/Debug/netX.0/crackme53.dll`, which you run with `dotnet crackme53.dll`, or an `.exe` on Windows. If you have no dotnet SDK you can still practice the dnSpy operations on any .NET assembly, such as `ILSpy.dll`, though you will not have the serial check to modify.

Open the crackme assembly in dnSpy and find the `CheckSerial` function, either with search (Ctrl+Shift+K) or by starting from the "Wrong" or "Correct" strings and using Analyze. Put a breakpoint on the line `bool isValid = ...` inside `CheckSerial`, start the program with F5, and enter any username with a wrong serial. When the breakpoint hits, open the Locals window and read the variable `expected`. That is the correct serial for the username you just typed. Run again with that username and the serial you read, and confirm you get "Correct!".

There is a second way that does not require knowing the serial. Put a breakpoint on `return isValid`, enter a wrong serial, and when execution stops change `isValid` from `false` to `true` in Locals, then press F5. The program now reports success. As a last step, try a conditional breakpoint inside the loop of `MakeSerial`, for example one that stops when the last character is being processed, so you can watch `acc` change.

Two questions to think about. Why does the correct serial differ for every username? And between reading `expected` and editing `isValid`, which one is suitable if you want to write a keygen, and which only gets you through a single run? Try it yourself before opening the solution.

<div class="lab-box">
<div class="lab-head"><b>LAB 5.3</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/5.3/src/Program.cs" download><i class="fa-solid fa-file-code"></i>src/Program.cs</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

In dnSpy, start from the string "Correct!" or "Wrong serial." and use Analyze to reach `Program.Main`, where you can see it calls `CheckSerial(user, serial)`. Decompiled, `CheckSerial` looks like this.

```csharp
static bool CheckSerial(string user, string serial)
{
    string expected = MakeSerial(user);
    bool isValid = string.Equals(serial, expected, StringComparison.Ordinal);
    return isValid;
}
```

The correct serial is not hard-coded. It is computed from the username by `MakeSerial`.

```csharp
static string MakeSerial(string user)
{
    int acc = 0x1337;
    foreach (char c in user)
        acc = (acc * 31 + c) & 0xFFFFF;
    return acc.ToString("X5");
}
```

For the first method, reading `expected`, put a breakpoint on the line `bool isValid = ...` in `CheckSerial`, start, enter a username such as `alice` and a random serial such as `00000`. The breakpoint hits, and in Locals you see `expected = "7EDA9"`. Run again with `alice` and `7EDA9`, and the program prints `Correct! Welcome, alice`.

A few reference serials, computed with the exact algorithm (mask `& 0xFFFFF`, formatted as 5 uppercase hex digits) and checked with a Python simulation, are below.

| Username | Correct serial |
|---|---|
| alice | 7EDA9 |
| bob | D8B1E |
| RE_Learner | DFA3C |

The second method is editing `isValid` at run time. You do not need to know the serial. Put a breakpoint on `return isValid`, enter a wrong serial, and when it stops double-click the value of `isValid` in Locals (currently `false`), change it to `true`, and press F5. The program prints `Correct!`. This only gets you through that one run, and does not give you a serial you can reuse or turn into a keygen. The first method gives you a real serial, and if you understand `MakeSerial` you can write a keygen for any username (see the keygen mindset from Lesson 3.6).

The correct serial differs per username because it is a hash of the username itself, with `acc` rolling through each character. This is an algorithmic check, not a comparison against a fixed serial. To write a keygen you have to use the first method, understanding and reproducing the algorithm. Editing `isValid` is only a one-off runtime patch.

One caveat on verification: the serials in the table come from a Python simulation that follows `MakeSerial` step by step (start at `0x1337`, multiply by 31 and add the character code, mask with `0xFFFFF`, print 5 uppercase hex digits). When you build the crackme with the dotnet SDK, the `expected` value you see in dnSpy should match this table exactly.

</details>

## Key takeaways
dnSpy maps decompiled C# lines back to the exact IL, so you can set breakpoints directly on code with no source. Use Start to run from the beginning and Attach to hook into a running process. Locals is where the right value often shows up, so look there before sitting down to read the algorithm.

You can edit the condition variable at runtime (for example `isValid = true`) to get past a check without understanding the logic. Conditional breakpoints are written in C# syntax, which is handy for loops.
