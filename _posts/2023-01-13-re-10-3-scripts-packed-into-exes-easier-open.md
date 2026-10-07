---
title: "Lesson 10.3: Scripts packed into exes, easier to open back up than you think"
image:
  path: /assets/img/covers/re-10-3-scripts-packed-into-exes-easier-open.webp
  alt: "Lesson 10.3: Scripts packed into exes, easier to open back up than you think"
date: 2023-01-13 11:38:00 +0700
categories: ["Technique Reverse", "Part 10 · Legacy: Delphi, VB6, AutoIt, AHK"]
tags: [reverse-engineering, legacy]
render_with_liquid: false
---
There's a group of "exes" where dragging them straight into IDA wastes your whole evening: scripts packed into an executable. Inside isn't compiled C code, but an AutoIt or AutoHotkey script, or an NSIS installer, plus a stub whose only job is to unpack the script and run it. The right way to reverse these isn't reading the stub's assembly, it's extracting the original script. A lot of the time you get back nearly the exact source.

This isn't side knowledge. Malware loves AutoIt and NSIS because they're quick to pack, hard to kill by signature, and look harmless. Knowing how to dig the script out is a skill you really use.

## General principle: identify first, extract after

Every type in this lesson follows the same rhythm. First identify the wrapper type with Detect It Easy (DIE) and `strings`, since each type leaves very clear traces. Then use the right extraction tool for that type. Never jump into a disassembler before ruling out that it's just a packed script.

Quick tells in `strings` or DIE:

| Type | Common traces |
|---|---|
| AutoIt | the strings `AU3!`, `>>>AUTOIT SCRIPT<<<`, `AutoIt v3` |
| AutoHotkey | an `RCDATA` resource named `>AUTOHOTKEY SCRIPT<`, the string `AutoHotkey` |
| NSIS | the strings `Nullsoft Install System`, `NSIS` |
| Inno Setup | the string `Inno Setup`, a `JR.` section in the resources |
| PyInstaller | the strings `MEI`, `pyi` (see Lesson 7.4 again) |

## AutoIt

AutoIt is an automation scripting language for Windows. When compiled, it embeds the script code (tokenized, not plain text) into an interpreter stub. Luckily, tokenizing isn't strong encryption, so tools can reverse almost all of it.

The simplest tool is Exe2Aut: drag and drop the exe in and it unpacks the original `.au3` file, and it runs on Windows. There's also AutoIt-Ripper (Python), which is cross-platform and extracts the script from the exe or from a memory dump.

For newer AutoIt variants with extra encryption, Exe2Aut sometimes has to run the file itself (dangerous if it's malware) to catch the moment the script gets decoded in memory. When analyzing malicious samples, do it in an isolated VM following [Lesson 0.3](/posts/re-0-3-set-up-safe-lab-before-touching/).

## AutoHotkey

AutoHotkey (AHK) is even easier. The script is embedded almost verbatim in an `RCDATA`-type resource, usually named `>AUTOHOTKEY SCRIPT<`. You don't need a specialized tool. Open the exe with Resource Hacker or CFF Explorer, find the RCDATA resource, export it and you have the `.ahk` script. For AHK v2 or compressed builds, you may need to decompress the resource first, but the approach doesn't change.

Since the script is in text form, a lot of the time just running `strings` already shows the content peeking out.

## NSIS installer

NSIS (Nullsoft Scriptable Install System) is a very popular installer builder. Inside is an archive holding the files to be installed, plus the compiled install script.

7-Zip (the version that supports NSIS) opens an NSIS `.exe` directly as an archive, letting you view and extract the files inside. This is the fastest way to get the payload the installer will drop. Note that newer 7-Zip versions dropped some support for viewing the `.nsi` script, but they can still extract the files. To read the script logic back, use specialized forks like nsisunbz or an older 7-Zip.

With malware, NSIS is often just a shell: extract it and you'll see the real payload (another exe/dll/script) to analyze next.

## Inno Setup

Inno Setup is another popular installer builder. Its format differs from NSIS so 7-Zip can't open it properly.

The tool for it is innounp (Inno Setup Unpacker), on the command line: `innounp -x setup.exe` extracts all the files and also the decompiled `install_script.iss` script. UniExtract2 bundles many extractors, auto-detecting NSIS, Inno and a few other types, which is handy when you're too lazy to remember which tool goes with which type.

## Other wrappers

BAT to EXE (batch packed into an exe) can usually be extracted with tools like a reverse `Batch2Exe`, or simply by dumping strings/temp files at runtime. For homemade script packers with no ready tool, the general approach that always works is to run it in a VM and catch the temp file or dump memory at the moment the script is decoded (use Procmon to see which files it writes to `%TEMP%`, see [Lesson 2.8](/posts/re-2-8-system-monitoring-watching-behavior-without-opening/) again).

## Why you should try this route first

A malware sample is reported as "hard", you drag it into IDA and see nothing but strange code, and it turns out to be just an AutoIt stub. Extracting the script lets you read the intent in a few minutes, instead of wading through assembly all day. A good habit: before complaining a binary is hard, rule out that it's just a packed script. DIE and `strings` give you the answer in ten seconds.

## Lab

The goal is to build the reflex of asking "is this just a packaged script?" and to extract the original source. You need Detect It Easy (the `diec.exe` command line tool and the GUI), Exe2Aut or AutoIt-Ripper for AutoIt, Resource Hacker or CFF Explorer for AutoHotkey, 7-Zip for NSIS, and innounp or UniExtract2 for Inno Setup. If the sample is malware, run everything inside an isolated VM (see [Lesson 0.3](/posts/re-0-3-set-up-safe-lab-before-touching/)).

Collect a few exes, either from your machine or made yourself: install a small program packed with NSIS or Inno (a lot of free software uses them), write a short AutoHotkey script and compile it, and write an AutoIt script and compile it. For each file, run `diec.exe <file>` and open the DIE GUI, and note the identification traces: AU3, AUTOHOTKEY SCRIPT, Nullsoft Install System, Inno Setup. Compare them against the table in the lesson.

Then extract the script or payload with the right tool. For AutoIt use Exe2Aut or `autoit-ripper <file> out/`. For AutoHotkey, open Resource Hacker, find the RCDATA entry named `>AUTOHOTKEY SCRIPT<` and export it. For NSIS, open the file with 7-Zip and extract everything. For Inno, run `innounp -x setup.exe`. Compare the extracted script with the original you wrote (for AutoIt and AHK): does it match, and is anything lost? For the NSIS and Inno files, list the payload files the installer will drop. If this were real malware, which payload would be worth analyzing next?

Two questions to think about. Why is extracting the script so much faster than reading the assembly of the stub? And when Exe2Aut can't extract statically (an encrypted variant), what do you do next that is still safe?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

This writeup describes the standard procedure. The Exe2Aut and Resource Hacker steps need a Windows machine, while the identification with `strings` and DIE works on any platform.

For identification, run `diec.exe` or `strings <file> | grep -i` for each type. For AutoIt you see `AU3!EA06` or `AU3!EA05` (the marker for the start of the script block), along with `>>>AUTOIT SCRIPT<<<` and `This is a third-party compiled AutoIt script`, and DIE reports the AutoIt compiler. For AutoHotkey, `strings` exposes `>AUTOHOTKEY SCRIPT<` and many AHK commands as plain text (`MsgBox`, `Gui`, `Send`), and DIE recognizes AutoHotkey. For NSIS you see `Nullsoft Install System v3.xx` and DIE reports Installer: Nullsoft. For Inno Setup you see `Inno Setup Setup Data (x.y.z)`, with resource sections whose names start with `JR.` or `zlb`. The rule is that once you see one of these strings, it is almost certainly a packaged script or installer, and you don't need to open IDA.

For extraction, with AutoIt and Exe2Aut you drag the exe into the window, it prints the `.au3` in the right panel, and you save it. On the command line with AutoIt-Ripper:

```
python -m autoit_ripper -i target.exe -o out/
```

The result is an `.au3` file holding the script almost verbatim (variable names, function names and strings are kept). For AutoHotkey with Resource Hacker, open the exe, go to the resource tree > RCDATA > `>AUTOHOTKEY SCRIPT<`, right-click and choose Save resource to file, and you get an `.ahk` file that is readable at once. For NSIS with 7-Zip:

```
7z x installer.exe -oout_nsis/
```

The folder `out_nsis/` holds every file the installer would install, plus `[NSIS].nsi` (if your 7-Zip version still supports exporting the script). For Inno Setup with innounp:

```
innounp -x setup.exe
```

This extracts the files and a decompiled `install_script.iss` that tells you what the installer does (writes the registry, runs commands, drops which files).

In the comparison, for AutoIt and AHK the extracted script is almost identical to the original: variable and function names are kept, comments are usually lost (they aren't embedded), and the strings and logic stay intact. That is why compiled scripts belong to the same "easy to reverse" group as managed code rather than native C.

For the payload question, with NSIS and Inno the files worth analyzing next are usually another exe or dll in the extracted list (the real payload), or a script (bat, vbs, ps1, au3) that the installer runs after installing. Read `install_script.iss` or a Procmon log to learn which file gets run (`Exec`, `Run`), since that is the next target.

On the reflection questions, extraction is faster because the stub is just a fixed interpreter, so reading its assembly tells you nothing about behavior. The behavior lives in the script, and the script comes out at a high language level that reads like source. When static extraction fails, run the sample in an isolated VM and use Procmon to watch which files it writes to `%TEMP%` (scripts are often decoded to disk or loaded into memory), or dump the process memory at the moment the script has been decoded. Always do this in an isolated environment following Lesson 0.3.

</details>

## Key takeaways
Many "exes" are really packed scripts (AutoIt/AHK) or installers (NSIS/Inno), so don't read the stub's assembly. Always identify first with DIE and `strings`, since each type has very clear traces. For AutoIt use Exe2Aut or AutoIt-Ripper, for AHK extract the RCDATA resource with Resource Hacker, for NSIS use 7-Zip, and for Inno use innounp (or UniExtract2 if you're lazy, since it handles both). Malware likes AutoIt and NSIS, so extracting the script/payload is a practical skill. When there's no tool, run it in an isolated VM and catch the temp file or dump memory.
