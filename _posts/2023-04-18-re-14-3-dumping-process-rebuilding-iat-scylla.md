---
title: "Lesson 14.3: Dumping a process and rebuilding the IAT with Scylla"
image:
  path: /assets/img/covers/re-14-3-dumping-process-rebuilding-iat-scylla.webp
  alt: "Lesson 14.3: Dumping a process and rebuilding the IAT with Scylla"
date: 2023-04-18 23:54:00 +0700
categories: ["Technique Reverse", "Part 14 · Packers and Obfuscation"]
tags: [reverse-engineering, packer, obfuscation]
render_with_liquid: false
---
In [lesson 14.2](/posts/re-14-2-unpacking-upx-automatic-manual/) you traced your way to the OEP, which means the unpacking stub has finished running and the original code is in memory. Next you want to get it out as a runnable file. You'd think you can just dump the memory region to disk. Try it and the dumped file crashes as soon as you run it. This lesson explains why, and how Scylla fixes it.

## Why a raw dump doesn't run

The problem is the IAT (Import Address Table), the table holding the addresses of the API functions the program calls.

When Windows loads a normal PE file, the loader reads the import directory (the list of "I need the function `MessageBoxA` from `user32.dll`"), finds the real address of each function, and fills it into the IAT. At runtime, the program calls APIs through this table.

Now look at the unpacked file in memory. The IAT in memory already holds the real addresses, because the unpacking stub resolved them at runtime. But the import directory that says "which function from which DLL" was thrown away or damaged by the packer, since it doesn't need it anymore.

So when you dump it raw to disk and run it again, on another machine (or after ASLR changes the DLL base), the real addresses in the IAT mean nothing, and the loader has no import directory to resolve them again. The program calls into garbage addresses and dies.

The dump has the IAT values but lost the information needed to rebuild the IAT. Scylla rebuilds that information.

## What Scylla does

Scylla (the x64 version is Scylla x64, often used as a plugin inside x64dbg) follows the logic above. First you attach to the process stopped at the OEP (or pick it from the process list). The process has to be alive and stopped at the right spot, so don't let it keep running or exit. Then you set the OEP by typing the address you just found into the OEP field, which becomes the entry point of the new file.

Next is IAT Autosearch, where Scylla scans memory around the code region to find the IAT (a run of pointers into system DLLs) and guesses the start and the size. Get Imports then takes each pointer in the IAT, looks up which function of which DLL that address belongs to, and rebuilds the full import list. This step rebuilds the lost information.

After that, Dump writes the module's memory out to a file. Finally Fix Dump merges the dump with the newly built import directory, adds a section holding the import table, and fixes the PE header (setting the entry point back to the OEP and pointing the Import Directory at the new table).

The result is a standalone PE file, and the Windows loader can resolve its imports again like any normal file.

## Reading the Get Imports result

After Get Imports, Scylla shows a tree: each DLL and its functions. Watch for lines marked red or "not found". Those are pointers in the IAT that Scylla couldn't map back to any function. There are a few possible causes.

One is that IAT Autosearch grabbed too much, so the region it guessed as the IAT also includes data that isn't import pointers. Narrow the start or the size. Another is redirected imports. Some protectors don't let the IAT point straight at the DLL but at an intermediate stub of their own (an import-hiding thunk), and that stub then jumps to the real function. Scylla sees a pointer into the packer's region rather than into user32/kernel32, so it gives up. Scylla has a "Trace redirected imports" option that tries to walk through the stub, but with a well-hidden IAT you have to fix it by hand or use another tool.

Delete the junk entries (right-click, cut thunk) before Fix Dump, otherwise the new import table will contain broken entries and the file still won't run.

## When Autosearch finds nothing

If IAT Autosearch gets it wrong, you can find the IAT yourself in x64dbg. Go to an API call in the unpacked code (for example `call [0x00407120]`), and `0x00407120` is one slot in the IAT. Follow that address in the dump, scroll up and down to see the boundaries of the run of pointers into DLLs, then enter the start and size into Scylla by hand.

## Workflow

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

If you dump before reaching the OEP, the code isn't fully unpacked yet and the dump is garbage, so make sure you're at the OEP. If you forget Fix Dump, the raw Dump file has no imports, since only Fix Dump merges the import table in.

A wrong OEP, even by a few bytes, shifts the entry point and the program runs wrong from the start. The OEP has to be the exact first instruction of the original code (usually a standard prologue or a call to the CRT init). Sometimes you also have to adjust the section characteristics (readable/executable) if the dumped file has permission errors.

## Key takeaways
A raw dump doesn't run because it has the IAT values but lost the import directory the loader needs to rebuild them. With Scylla you attach, set the OEP, run IAT Autosearch, Get Imports, Dump, and Fix Dump. Clean up red entries and handle redirected imports before Fix Dump.

If Autosearch is wrong, find the IAT by hand from a `call [address]` in the unpacked code. Always dump at the correct OEP, because a wrong OEP ruins the whole file.

## Lab

This continues from Lab 14.2, where you manually unpacked a UPX file with a modified header all the way to the OEP in x64dbg. The task now is to turn that live memory state into a standalone runnable file. You need the file stopped at the OEP in x64dbg from that previous lab, and Scylla (the x64 build for a 64-bit file), either standalone or the Scylla plugin that ships inside x64dbg under Plugins > Scylla.

With x64dbg stopped at the OEP, open Scylla without letting the process run any further. Confirm the OEP field shows the correct address. If you're using the plugin inside x64dbg, it usually fills in the current EIP/RIP automatically, so just double check it. Click IAT Autosearch, then Get Imports. Look through the import tree and mark and cut (cut thunk) any entry that's red, not found, or redirected. Click Dump to save the dumped file, then click Fix Dump and select that dump file, which makes Scylla produce a `*_SCY.exe`. Run the fixed file, and it should behave like the original unpacked program.

Three questions to think about. If you skip Fix Dump and run the raw Dump file directly, what happens and why? If IAT Autosearch reports too many pointers, how do you find the real boundaries of the IAT? And why do some entries point into the packer's own region instead of into kernel32 or user32?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Try it yourself before reading this.

The full workflow. Starting from the OEP: from Lab 14.2, after the ESP trick and the tail jump, x64dbg stops at the first instruction of the original code. Don't press F9 again, since Scylla needs the process alive and standing still here. Open Scylla and select the process: a standalone Scylla needs you to pick it from the dropdown at the top, while the plugin inside x64dbg is already attached to the process being debugged. Set the OEP field to the current RIP/EIP address, copying it from the current line in x64dbg, since this becomes the entry point of the new file.

Run IAT Autosearch. Scylla scans and reports a starting address (VA) and an estimated IAT size, and Advanced IAT Autosearch scans more broadly if the normal pass misses something. Get Imports then shows the DLL and function tree, where each green line is a valid import that resolved correctly and each red line is a pointer that didn't resolve.

Cleaning up. Right-click the red entries and choose "Cut thunk(s)" to remove them. For redirected imports, try "Trace redirected imports" (or the equivalent option) before cutting, since Scylla might be able to see through the stub.

Dump the whole module to `file_dump.exe`, then run Fix Dump and select that file. Scylla adds a `.scy` section holding a new import directory, patches the header (entry point set to the OEP, the Import Directory RVA pointing at the new section), and writes out `file_dump_SCY.exe`. Running `file_dump_SCY.exe` should work like the original.

On running the raw dump without Fix Dump: the dump has an IAT filled with the real addresses from that one run, but no import directory for the loader to resolve against. On the next run, ASLR places the DLLs at different base addresses, so the old addresses become garbage, the program calls into the wrong region, and it crashes almost immediately. Fix Dump rebuilds the import table so the loader can resolve it properly.

On finding the real IAT boundaries when Autosearch grabs too much: go into the unpacked code in x64dbg and find an API call of the form `call [address]` or `jmp [address]`. That `address` is one IAT slot. Follow it in the dump, scroll up until the run of pointers into DLLs ends (you hit a zero or non-pointer data), which marks the upper boundary, and scroll down the same way for the lower boundary. Enter the exact start and size into Scylla.

On entries pointing into the packer's own region instead of kernel32 or user32: that's a redirected import, a form of IAT obfuscation. The protector doesn't let the IAT point straight at the real API function, instead pointing at its own stub, which then jumps to the real function. The purpose is to hide the API list from an analyst. Scylla sees the pointer sitting inside the packer's region and doesn't know what function it is. You have to trace through the stub (Scylla has an option for this), or in tricky cases, recover each thunk manually.

The Scylla workflow above follows the tool's standard steps. In practice on Windows, the exact OEP and IAT boundaries depend on the file you're working with.

</details>
