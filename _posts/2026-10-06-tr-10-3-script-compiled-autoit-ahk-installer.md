---
title: "Lesson 10.3: Scripts packed into exes, easier to open back up than you think"
date: 2026-10-06 09:08:00 +0700
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

Tools:
- **Exe2Aut**: drag and drop the exe in and it unpacks the original `.au3` file. Runs on Windows, the simplest.
- **AutoIt-Ripper** (Python): cross-platform, extracts the script from the exe or from a memory dump.

For newer AutoIt variants with extra encryption, Exe2Aut sometimes has to run the file itself (dangerous if it's malware) to catch the moment the script gets decoded in memory. When analyzing malicious samples, do it in an isolated VM following [Lesson 0.3](/posts/tr-0-3-dung-lab-an-toan/).

## AutoHotkey

AutoHotkey (AHK) is even easier. The script is embedded almost verbatim in an `RCDATA`-type resource, usually named `>AUTOHOTKEY SCRIPT<`. You don't need a specialized tool:

- Open the exe with **Resource Hacker** or **CFF Explorer**, find the RCDATA resource, export it and you have the `.ahk` script.
- For AHK v2 or compressed builds, you may need to decompress the resource first, but the approach doesn't change.

Since the script is in text form, a lot of the time just running `strings` already shows the content peeking out.

## NSIS installer

NSIS (Nullsoft Scriptable Install System) is a very popular installer builder. Inside is an archive holding the files to be installed, plus the compiled install script.

- **7-Zip** (the version that supports NSIS) opens an NSIS `.exe` directly as an archive, letting you view and extract the files inside. This is the fastest way to get the payload the installer will drop.
- Note that newer 7-Zip versions dropped some support for viewing the `.nsi` script, but they can still extract the files. To read the script logic back, use specialized forks like **nsisunbz** or an older 7-Zip.

With malware, NSIS is often just a shell: extract it and you'll see the real payload (another exe/dll/script) to analyze next.

## Inno Setup

Inno Setup is another popular installer builder. Its format differs from NSIS so 7-Zip can't open it properly.

- **innounp** (Inno Setup Unpacker): command line, `innounp -x setup.exe` extracts all the files and also the decompiled `install_script.iss` script.
- **UniExtract2** bundles many extractors, auto-detecting NSIS, Inno and a few other types, handy when you're too lazy to remember which tool goes with which type.

## Other wrappers

- **BAT to EXE** (batch packed into an exe): can usually be extracted with tools like a reverse `Batch2Exe`, or simply by dumping strings/temp files at runtime.
- **Homemade script packers**: when there's no ready tool, the general approach that always works is to run it in a VM and catch the temp file or dump memory at the moment the script is decoded (use Procmon to see which files it writes to `%TEMP%`, see [Lesson 2.8](/posts/tr-2-8-giam-sat-he-thong/) again).

## Why you should try this route first

A malware sample is reported as "hard", you drag it into IDA and see nothing but strange code, and it turns out to be just an AutoIt stub. Extracting the script lets you read the intent in a few minutes, instead of wading through assembly all day. A good habit: before complaining a binary is hard, rule out that it's just a packed script. DIE and `strings` give you the answer in ten seconds.

## Key takeaways
- Many "exes" are really packed scripts (AutoIt/AHK) or installers (NSIS/Inno). Don't read the stub's assembly.
- Always identify first with DIE and `strings`, each type has very clear traces.
- AutoIt: Exe2Aut or AutoIt-Ripper. AHK: extract the RCDATA resource with Resource Hacker.
- NSIS: 7-Zip. Inno: innounp. If you're lazy, UniExtract2 handles both.
- Malware likes AutoIt and NSIS, extracting the script/payload is a practical skill.
- When there's no tool, run it in an isolated VM and catch the temp file or dump memory.
