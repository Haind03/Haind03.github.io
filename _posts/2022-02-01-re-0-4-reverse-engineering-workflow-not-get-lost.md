---
title: "Lesson 0.4: The reverse engineering workflow, or how not to get lost in a sea of assembly"
date: 2022-02-01 16:57:00 +0700
categories: ["Technique Reverse", "Part 00 · Getting Started"]
tags: [reverse-engineering, basics]
render_with_liquid: false
---
Beginners open a file and jump straight into reading code from top to bottom. Two hours later they're still inside the C runtime's init function, haven't touched a single line the author wrote, and give up. Experienced people do the opposite: they spend the first ten minutes **not reading code**, and instead answer the question "what is this thing, and where is the part worth looking at".

This lesson is the framework you apply to every target, from a tiny crackme to complex malware. Four steps: **Triage, Static, Dynamic, Notes.** It's not a straight line, you'll jump back and forth constantly, but you always start with triage.

## Step 1: Triage, look from a distance before getting close

Triage is a quick checkup. You haven't opened a disassembler yet, you just need to know what you're holding. A few minutes here saves hours later.

The first question is what kind of file it is: PE (Windows), ELF (Linux), Mach-O (macOS), APK, `.pyc`, `.NET`, or something else. Drop it into Detect It Easy (DIE) and most of this is done. DIE also usually shows the compiler, which is where you decide which way to go: see ".NET" and open dnSpy happily, see "Go" and brace yourself for a long one.

Next, check whether it's packed. Look at the entropy in DIE: entropy close to 8.0 plus a poor import table is a sign of a packer. If so, the first job is to unpack, because reading packed code is pointless. Also note whether it's 32-bit or 64-bit, so you pick the right x32dbg or x64dbg and the right mode in IDA.

Finally, see whether anything leaks in the strings. Run `strings` or FLOSS and look for URLs, file paths, error messages, function names, registry keys. Often the answer is right there and you don't need to disassemble anything.

By the end of triage you should have a one-line summary like: "64-bit PE, written in C++ with MSVC, not packed, has strings that mention checking a serial". Now you know where to go next.

## Step 2: Static analysis, reading without running

Open a disassembler/decompiler (Ghidra, IDA) and start reading, but with a strategy, not top to bottom.

The best way to narrow things down is to work backwards from strings. See an interesting string like "Wrong password"? Click it, look at the cross-references (xrefs) to see where that string is used. That place is almost certainly the password check function. This is the number one beginner technique and it's extremely effective. You can also work from imports: when you see `CreateFileW`, `RegSetValueEx`, `InternetOpen`, each API tells part of the story (files, registry, network), so put xrefs on the suspicious ones.

The entry point of a native binary is not the author's `main` but the runtime's startup code, so you have to find the real `main`. Lesson [3.1](https://github.com/Haind03/Technique-Reverse/tree/main/phan-03-c) shows how to spot it in that pile. Once you're in the code, read the decompiler first and assembly second. For beginners, the C pseudocode from Hex-Rays or Ghidra is much easier to swallow, and you only drop down to assembly when the decompiler gets it wrong or you need instruction-level accuracy.

Rename and comment as soon as you understand something. Found out `sub_401000` hashes a string? Rename it to `hash_string` right away. Every name you assign makes the next function easier to read. This is the big difference between someone slow but steady and someone drowning in `sub_xxx`.

Static gives you the map. But the map has blurry spots: encrypted code, values only known at runtime, loops that are hard to trace by eye. That's when you switch to dynamic.

## Step 3: Dynamic analysis, run it and see it with your own eyes

Open a debugger (x64dbg, GDB), set breakpoints where static analysis narrowed things down, then run to there and inspect.

Dynamic is the right tool when you want to see the real values, such as the arguments passed to the check function, strings after decryption, or comparison results. It also fits when the code decrypts or unpacks itself at runtime and so looks like nothing on disk, when you need to follow a specific branch (for example enter a wrong serial to see where it goes), or when the logic is so tangled that reading it statically costs more than just running it.

A basic tip is to set breakpoints on important APIs (for example `strcmp`, `GetWindowTextW`) to catch the exact moment. When you reach the serial comparison, look at both operands: one is what you typed, and the other is often the correct serial itself, sitting naked in a register. With malware, remember you're really running it, so work in an isolated VM as in [Lesson 0.3](/posts/re-0-3-set-up-safe-lab-before-touching/).

Static and dynamic complement each other all the time. Read statically and spot something suspicious, confirm by running it, then go back to reading statically with the new understanding. This loop is the real rhythm of RE work.

## Step 4: Notes, the step everyone is lazy about and everyone regrets skipping

Reversing a medium-sized program can take days. Today you understand a function well, three days later you come back and have forgotten everything. Not taking notes means forcing yourself to start over.

Inside the tool, rename functions and variables and add comments right in IDA/Ghidra. This is the most valuable kind of note because it sits right next to the code. Outside the tool, keep a separate file with the question you're chasing, hypotheses, important addresses, and what you tried and failed. Markdown is enough. For malware, also record the IOCs (hashes, IPs, domains, mutexes, registry keys), the behavior, and finally a YARA or capa rule if you need to recognize it again.

One small tip that works well: write the question first, answer later. "What does the function at 0x401500 do?" and when you figure it out, write the answer right below. It keeps you focused instead of drifting.

## Putting it together as a loop

![The reverse workflow is a loop of Triage, Static, Dynamic, Notes](/assets/img/technique-reverse/assets/common/quy-trinh-reverse.svg)

```
   TRIAGE  (DIE, strings, file type)
      |  know what you're holding
      v
   STATIC  <--------------------+
      |  read, narrow down      |
      v                         |  new understanding -> read again
   DYNAMIC -----------------------+
      |  confirm with your eyes
      v
   NOTES  (rename, comment, note, IOC)
      |
      v
   repeat until the original question is answered
```

The most important thing isn't memorizing the diagram but **always starting with a question**. "What do I want to know?" What's the correct serial? Where does this malware talk to? What algorithm does this function encrypt with? With a clear question you know when to stop. Without one, you'll read assembly until morning for nothing.

## Key takeaways
Always triage first: file type, language, packed or not, bitness, strings. Use static to draw the map, working backwards from strings and imports and renaming as soon as you understand. Use dynamic to see the truth at runtime, since it complements static rather than replacing it.

Take notes inside the tool and in a separate file, otherwise you'll start over from scratch. Start each session with a specific question, so you know when you're done.
