---
title: "Lesson 2.1: Five-minute triage with DIE, strings and PE-bear"
image:
  path: /assets/img/covers/re-2-1-five-minute-triage-die-strings-pe.webp
  alt: "Lesson 2.1: Five-minute triage with DIE, strings and PE-bear"
date: 2022-04-10 15:52:00 +0700
categories: ["Technique Reverse", "Part 02 · The Toolkit"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
Before opening IDA or Ghidra, there's one thing veterans always do and beginners often skip: a quick checkup. Five minutes of asking "what am I holding" saves you hours of wandering later. Open a disassembler on a packed file and you're staring at garbage, open it in the wrong 32/64-bit mode and every address is off, skip the strings first and you miss an answer sitting right on the surface.

This lesson is a practical triage workflow with four tools, and Detect It Easy is a portable build, so there's nothing to install.

## Detect It Easy, the opening knife

DIE answers the three most important triage questions: what is this file, what was it written with, and is it packed.

### Using the GUI

Run `die.exe` and drag and drop the file in. The main result line tells you the file type (PE32, PE32+, ELF, ...) and what DIE guessed: the compiler (MSVC, GCC, MinGW), linker, or protector/packer (UPX, VMProtect, Themida, .NET). "PE32+" means 64-bit, "PE32" is 32-bit.

The Entropy button is often ignored but extremely valuable. Entropy measures how "random" the data is, on a scale of 0 to 8. Normal code is around 6, compressed or encrypted data shoots up to nearly 8. A `.text` section with entropy 7.9 is almost certainly packed or encrypted. DIE draws an entropy chart per section, and you see at a glance where something's abnormal.

The Import and PE buttons let you quickly see which DLLs and functions the file imports. An import table so poor that only `LoadLibrary` and `GetProcAddress` remain is a classic sign of a packer: it hides the real APIs and only loads them at runtime.

### Using the command line (diec)

`diec.exe` is the console version, handy for batch work or scripting:

```
diec.exe path_to_file.exe
```

It prints the file type and what it detected. Add an option to get the entropy:

```
diec.exe -e path_to_file.exe
```

When you have to triage a whole folder of samples, a loop calling `diec` does it, with no need to open the GUI for each one.

## The file command, a quick answer on Linux

On Linux (or WSL), `file` identifies the type by magic number in a few thousandths of a second:

```
$ file sample.bin
sample.bin: ELF 64-bit LSB pie executable, x86-64, dynamically linked, not stripped
```

This one line already says: 64-bit ELF, executable, dynamically linked, and importantly "not stripped" means it still has symbols, which will be much easier to read. If you see "stripped" brace yourself for no function names.

## Strings, where the answer often sits in the open

Many times, what you need is right there in the file's strings: URLs, paths, error messages, registry key names, even passwords or the flag in an easy crackme. Before disassembling, just glance at the strings.

```
$ strings -n 6 sample.exe
```

`-n 6` only takes strings of 6 or more characters, filtering out some junk. On Windows you can use Sysinternals' `strings.exe`, or let DIE/PE-bear list them.

The problem with classic `strings`: it only sees strings sitting in the open. Malware and even protected software often encrypt strings, or build strings on the stack one character at a time (stack strings), so `strings` finds nothing. This is when you use FLOSS (from Mandiant). FLOSS does what `strings` does, and also tries to decode simply-encrypted strings and rebuild stack strings:

```
floss sample.exe
```

Seeing empty strings while the file clearly does a lot is a clue: either it's packed, or it hides its strings. Both are worth noting.

## PE-bear, looking deep into the PE structure

When you need to look more closely inside a PE file, PE-bear shows the whole structure visually and lets you edit in place. During triage I mostly use three tabs. Sections shows the list of sections with raw size and virtual size, entropy per section, and permissions. A section whose virtual size is far larger than its raw size (for example raw near 0 but virtual large) is where a packer will unpack code at runtime, a very clear sign of packing. Imports shows the full list of imported DLLs and functions, which you compare against what the file claims to do. Resources is worth a look because sometimes the real payload sits in a resource as high-entropy data.

PE-bear also lets you edit bytes and save, but at the triage step we only read.

## Putting it together as a workflow

Side by side, your first five minutes go like this. Drop the file into DIE to see what type it is, what compiler or packer, and whether it's 32 or 64-bit. Check the entropy in DIE for any section near 8; if there is one it's likely packed, and the next job is unpacking, not reading code yet. Glance at the imports (DIE or PE-bear), since a poor import table is another vote for "packed". Run strings or FLOSS to pick up the clues sitting in the open, like URLs, paths and messages. Then write a one-line summary such as "64-bit PE, MSVC, not packed, has strings mentioning a license check", and only now open the disassembler.

The goal of triage isn't to understand the program, but to know which way to go next. Spotting early that a file is packed keeps you from wasting an hour reading meaningless bytes.

## Lab

Practice right away on tools you probably already have lying around. The targets are four executables: `die.exe`, `dnSpy.exe`, `ILSpy.exe` and `jadx-gui-1.5.1.exe`. Open a terminal (PowerShell or cmd) in the folder that holds them and run the console version of DIE on each one:

```
diec.exe die.exe
diec.exe dnSpy.exe
diec.exe ILSpy.exe
diec.exe jadx-gui-1.5.1.exe
```

Write down the file type and the compiler or packer each one reports. Which are native C/C++ and which are .NET, and how does DIE tell them apart?

Next, take the entropy of two of them and compare, for example `diec.exe -e dnSpy.exe`. Is any section close to 8.0? If so, guess why: compression, a resource, encryption. Then open the DIE GUI, drag a file in, press the Entropy button to see the per-section chart, and press the PE/Import button to see the import table. Which file imports many functions and which imports few?

After that, run strings on one file (WSL or Sysinternals `strings.exe`) with `-n 6` and pick out three strings that tell you what the file does, such as a library name, a message or a path.

Finally, think about this: if a file has entropy around 7.9 in `.text` and an import table with only a few functions left, what is your next step? The hint is that it isn't opening IDA right away. Try it yourself first, then open the solution.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Here are the real results from triaging those four files.

For the first task, the file type and compiler come out like this:

| File | Type | What it really is |
|---|---|---|
| `die.exe` | PE32+ (64-bit) GUI | Native C++ built with Qt (strings such as `Qt5Core`, `Qt5Gui` and MinGW's `libgcc`) |
| `dnSpy.exe` | PE32+ (64-bit) GUI | .NET apphost launcher (strings `apphost`, `hostfxr`) |
| `ILSpy.exe` | PE32+ (64-bit) GUI | .NET apphost launcher (same `apphost` and `hostfxr` signs) |
| `jadx-gui-1.5.1.exe` | PE32 (32-bit) GUI, stripped | Java launcher stub built with launch4j (strings `launch4j`, `jre`, `java`, `.jar`) |

The lesson is that "it's a PE" does not mean "the main code lives in this file". `die.exe` is genuinely native, with its logic inside the exe, so that is the kind of thing you would reverse in IDA or Ghidra. `dnSpy.exe` and `ILSpy.exe` are native PE32+ files, but they are only .NET apphosts whose single job is to find the runtime and load the real managed file (`dnSpy.dll`, `ILSpy.dll`). Reversing those exes is nearly useless, because the C# code is in the `.dll` of the same name, which you open with dnSpy or ILSpy themselves. `jadx-gui-1.5.1.exe` is even more indirect: it is a 32-bit stub that only starts a JVM to run `jadx-gui-1.5.1-all.jar`, and the Java code is in the jar. This is exactly why triage matters. If you started disassembling `dnSpy.exe` you would only see code that hunts for a runtime, and no trace of dnSpy itself.

For the entropy and import tasks, a truly native file like `die.exe` has entropy around 6 in `.text` and a fair number of imports from the Qt DLLs and kernel32/user32, which is normal. The .NET apphosts have lower entropy and very few imports, because the real work is done by the runtime and not by the exe. None of these files is packed, so no section jumps toward 8. If you ever see an unknown file with `.text` entropy of 7.9, that is the moment to stop and think about unpacking. A file with both high entropy and only a handful of imports is almost certainly packed, since the two signs reinforce each other.

For the strings task, running `strings -n 6` on `die.exe` shows the names of the Qt DLLs, interface text and the formats it can recognize. On the `dnSpy.exe` apphost you see messages like "the application to execute does not exist" and strings related to `hostfxr`, which is typical of a .NET apphost.

For the last question, the right next step with a packed file is to unpack first and read code afterward, not to open IDA. Reading compressed or encrypted code means staring at garbage. The unpacking workflow is covered in Part 14.

To sum up, with only `file`, DIE and a few strings commands you sorted four files into one real native program, two .NET apphosts whose code is in a dll, and one Java launcher whose code is in a jar. You knew the right path for each without opening a disassembler, and that is the whole value of triage.

</details>

## Key takeaways
Always triage before opening a disassembler, because five minutes buys you hours. DIE answers the file type, compiler or packer, and 32/64-bit ("PE32+" is 64-bit). Entropy near 8 in a section means it's likely packed or encrypted, so the next job is unpacking, and a poor import table (only LoadLibrary/GetProcAddress left) is a sign of a packer hiding APIs.

Run strings before disassembling, and if they're empty use FLOSS to decode encrypted strings and stack strings. In PE-bear, a section whose virtual size is far larger than its raw size is where code will be unpacked at runtime.
