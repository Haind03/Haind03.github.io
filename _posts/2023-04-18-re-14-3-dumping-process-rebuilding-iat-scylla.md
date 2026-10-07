---
title: "Lesson 14.3: Dumping a process and rebuilding the IAT with Scylla"
date: 2023-04-18 23:54:00 +0700
categories: ["Technique Reverse", "Part 14 · Packers and Obfuscation"]
tags: [reverse-engineering, packer, obfuscation]
render_with_liquid: false
---
In [lesson 14.2](/posts/re-14-2-unpacking-upx-automatic-manual/) you traced your way to the OEP, which means the unpacking stub has finished running and the original code is sitting intact in memory. The natural next step is to get it out as a runnable file. Sounds simple: just dump the memory region to disk, right? Try it, and you'll see the dumped file crashes as soon as you run it. This lesson explains why, and how Scylla fixes it.

## Why a raw dump doesn't run

The problem is the IAT (Import Address Table), the table holding the addresses of the API functions the program calls.

When Windows loads a normal PE file, the loader reads the import directory (the list of "I need the function `MessageBoxA` from `user32.dll`"), finds the real address of each function itself, and fills it into the IAT. At runtime, the program calls APIs through this table.

Now look at the unpacked file in memory. The IAT in memory already holds the real addresses, because the unpacking stub resolved them at runtime. But the import directory that describes "which function from which DLL" was thrown away or damaged by the packer, since it doesn't need it anymore.

So when you dump it raw to disk and run it again, on another machine (or after ASLR changes the DLL base), the real addresses in the IAT become meaningless, and the loader has no import directory to resolve them again. The program calls into garbage addresses and dies.

In short: the dump has the IAT values but lost the description needed to rebuild the IAT. Scylla's job is to rebuild that description.

## What Scylla does

Scylla (the x64 version is Scylla x64, often used as a plugin inside x64dbg) follows exactly the logic above. First you attach to the process stopped at the OEP (or pick it from the process list). Note the process has to be alive and stopped at the right spot, so don't let it keep running or exit. Then you set the OEP by typing the address you just found into the OEP field, which becomes the entry point of the new file.

Next comes IAT Autosearch, where Scylla scans memory around the code region to find the IAT (a run of pointers into system DLLs) and guesses the start and the size. Get Imports then takes each pointer in the IAT, looks up which function of which DLL that address belongs to, and rebuilds the full import list. This is the step that rebuilds the lost description.

After that, Dump writes the module's memory out to a file. Finally Fix Dump merges the dump you just made with the newly built import directory, adds a section holding the import table, and fixes the PE header (setting the entry point back to the OEP and pointing the Import Directory at the new table).

The result is a standalone PE file, and the Windows loader can resolve its imports again like any normal file.

## Reading the Get Imports result

After Get Imports, Scylla shows a tree: each DLL and its functions. What to watch for are lines marked red or "not found". Those are pointers in the IAT that Scylla couldn't map back to any function. A few possibilities exist.

One is that IAT Autosearch grabbed too much, so the region it guessed as the IAT also includes data that isn't import pointers. Narrow the start or the size. Another is redirected imports: some protectors don't let the IAT point straight at the DLL but at an intermediate stub of their own (an import-hiding thunk), and that stub then jumps to the real function. Scylla sees a pointer into the packer's region rather than into user32/kernel32, so it gives up. Scylla has a "Trace redirected imports" option that tries to walk through the stub, but with a cleverly hidden IAT you have to fix it by hand or use another tool.

Rule of thumb: delete the junk entries (right-click, cut thunk) before Fix Dump, otherwise the new import table will contain broken entries and the file still won't run.

## When Autosearch finds nothing

If IAT Autosearch gets it wrong, you can identify the IAT yourself by looking in x64dbg: go to an API call in the unpacked code (for example `call [0x00407120]`), and `0x00407120` is one slot in the IAT. Follow that address in the dump, scroll up and down to see the boundaries of the run of pointers into DLLs, then enter the start and size into Scylla by hand.

## Short workflow

```
x64dbg: unpack to the OEP (lesson 14.2)
   |
Scylla: Attach process
   |
set OEP = the OEP address
   |
IAT Autosearch  ->  Get Imports
   |
clean up red / redirected entries
   |
Dump  ->  Fix Dump
   |
run the _dump_SCY.exe file
```

## Common pitfalls

If you dump before reaching the OEP, the code isn't fully unpacked yet and the dump is garbage, so always make sure you're at the OEP. Forgetting Fix Dump leaves the raw Dump file without imports, since only Fix Dump merges the import table in.

A wrong OEP, even by a few bytes, shifts the entry point and the program runs wrong right from the start. The OEP has to be the exact first instruction of the original code (usually a standard prologue or a call to the CRT init). Sometimes you also have to adjust the section characteristics (readable/executable) if the dumped file has permission errors.

## Key takeaways
A raw dump doesn't run because it has the IAT values but lost the import directory the loader needs to rebuild them. With Scylla you attach, set the OEP, run IAT Autosearch, Get Imports, Dump, and Fix Dump. Clean up red entries and handle redirected imports before Fix Dump.

If Autosearch is wrong, find the IAT by hand from a `call [address]` in the unpacked code. Always dump at the correct OEP, because a wrong OEP ruins the whole file.

## Lab
See [labs/14.3/](https://github.com/Haind03/Technique-Reverse/blob/main/labs/14.3/README.md). Continuing from the file you unpacked by hand in lab 14.2, use Scylla to dump it and fix the IAT into a standalone runnable file.
