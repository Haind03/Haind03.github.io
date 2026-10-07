---
title: "Lesson 15.7: Anti-attach, anti-dump, anti-hook, three layers against your tools"
image:
  path: /assets/img/covers/re-15-7-anti-attach-anti-dump-anti-hook.webp
  alt: "Lesson 15.7: Anti-attach, anti-dump, anti-hook, three layers against your tools"
date: 2023-06-21 09:26:00 +0700
categories: ["Technique Reverse", "Part 15 · Anti-Reversing and Bypasses"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
The previous three lessons covered anti-debug: how a program knows it's being debugged. This lesson goes one step further, to tricks aimed straight at three specific things you often do: attach a debugger to a running process, dump memory to a file, and hook APIs. Each one blocks a different tool, so you have to understand each separately to undo it properly.

Like every lesson in this part, the point of view here is the analyst's: understand the mechanism so you can recognize and get past it when you meet it in your own samples, not to plant it in other people's software.

## Anti-attach: locking the back door after you're in the house

Normally there are two ways to get a debugger into a program: run it from the debugger from the start (spawn), or let it run and attach later. Anti-attach targets the second way.

The most classic trick relies on a Windows limitation: a process can have only one debugger at a time. If the program debugs itself (or spawns a child process and lets the child debug the parent), the debugger slot is already taken. Your real debugger attaching will be refused with an error like "a debugger is already attached". The self-debugging technique was covered in [Lesson 15.4](/posts/re-15-4-advanced-anti-debug-self-debug-tls/), here it serves the anti-attach purpose.

The second way is subtler: when Windows attaches a debugger, it calls `DbgUiRemoteBreakin` in `ntdll` to create a breakin thread in the target process. The program just needs to patch this function (overwrite the start of the function with a call to `ExitProcess` or a `ret` that breaks the logic) and every time someone tries to attach, the process exits instead of stopping for you. Same with `DbgBreakPoint`.

The third way is simple but annoying: periodic checks. A background thread re-runs all the anti-debug checks from the previous three lessons (BeingDebugged, NtQueryInformationProcess...) every few seconds. You attach cleanly, and a few seconds later it detects you and exits.

The general ways around anti-attach start with attaching early, or not attaching at all. If you can, run the program straight from the debugger from the start (spawn) instead of attaching later, and then the debugger slot is yours before the anti-attach code gets to run. To disable the periodic check loop, find the thread doing it and patch the check function to return "no debugger", or use ScyllaHide/TitanHide to hide it entirely (see [Lesson 15.9](/technique-reverse/)). If `DbgUiRemoteBreakin` was patched, restore it to its original in memory before attaching.

## Anti-dump: turning your dump into garbage

When you unpack a sample by running to the OEP and dumping memory (the workflow in [Lesson 14.3](/posts/re-14-3-dumping-process-rebuilding-iat-scylla/)), a dump tool like Scylla reads the PE header in memory to know where the sections are and how big they are, and rebuilds the file. Anti-dump breaks exactly that header.

You see a few tricks often. After the loader has finished loading and no longer needs the header, the program can wipe the MZ and PE signatures by overwriting the two bytes `4D 5A` ("MZ") at the start and the `50 45` ("PE") signature with zeros or junk, and a dump tool scanning memory no longer sees a valid PE to anchor on. It can also falsify SizeOfImage by changing that field in the Optional Header to a huge or too-small value, so the dump tool trusts it and dumps too little, or overflows into junk regions. Modifying the section count, virtual addresses, and raw sizes smears the section table so rebuilding the file gets the layout wrong. Finally, the important code can be kept in dynamically allocated regions (VirtualAlloc) that don't belong to the main image, so a normal image dump misses it.

Recognizing anti-dump isn't hard: you dump a file, open it in PE-bear or CFF Explorer and it reports a broken header, or the dumped file doesn't run even though you're sure you reached the right OEP.

To get around it, you can rebuild the header by hand. You know the ImageBase (from the Memory Map in the debugger) and you know what the original PE header looks like, so copy back the two MZ bytes and the PE signature, and fix SizeOfImage to the correct value. Scylla has a rebuild option that helps with this part. You can also dump earlier: if the header-wiping code runs after the OEP, put a breakpoint right at the OEP and dump before it gets a chance to break things. With some packers the original header is still somewhere in memory before being overwritten, or you can patch the branch that does the wiping (NOP it out) and only then let it continue. PE-sieve also often handles many broken-header cases on its own when dumping an unpacked module.

## Anti-hook: checking the mirror to see if someone touched it

When you hook an API with an inline hook (Detours, MinHook), or when Frida/an EDR attaches, the most common way is to overwrite the first few bytes of the function (the prologue) with a `jmp` instruction that jumps to your code. Anti-hook exploits exactly that: it checks whether the starts of important functions are still intact.

The simplest mechanism is comparing the prologue to the expected value. The program knows which bytes `NtProtectVirtualMemory` or `VirtualProtect` normally start with, reads the first few bytes of the function at runtime, and if it sees a strange `jmp` (`E9 ...`) or `push/ret` it knows it's hooked. A subtler way is comparing to a clean copy on disk: it reads the `ntdll.dll` file from disk itself, maps a clean copy, and compares the prologue bytes one by one between the in-memory copy (possibly hooked) and the clean copy. A difference means a hook. Some samples also compare `kernel32` calling down into `ntdll` to detect which layer the hook sits at.

This is exactly how a lot of malware detects EDR, and also how a program detects Frida attached.

To get around it, hook more quietly. Instead of an inline hook overwriting the prologue, use a hardware breakpoint (registers DR0 to DR3) to catch the call without modifying a single byte of code. There's nothing to compare, so prologue-check anti-hook is blind. You can also hook deeper than the checked layer: if it only checks the `kernel32` prologue, hook at the `ntdll` layer, or vice versa. Another option is to find the function that compares prologues and patch it to always report "clean". Restoring the prologue before the check and hooking again after is more complicated and rarely used.

Note the connection: anti-hook checking the prologue is exactly why RE people like hardware breakpoints. They're powerful because they leave no trace in the code.

## These three often come together

In a serious protector (Themida, VMProtect with full options) you'll meet all three layers at once, stacked on top of the anti-debug from the earlier lessons. A reasonable order of handling is to get past the basic anti-debug first so it can run under the debugger (ScyllaHide), then spawn instead of attach to dodge anti-attach, then hook with hardware breakpoints to dodge anti-hook, and finally, at the OEP, dump early and rebuild the header to dodge anti-dump.

The overall strategy for multiple layers is covered in [Lesson 15.10](/posts/re-15-10-when-several-anti-layers-are-stacked/).

## Lab

The goal is to see a program corrupt its own PE header in memory, then rebuild the header yourself so you can dump it, plus two observation exercises on anti-attach and anti-hook. The tools are x64dbg, Scylla (or PE-sieve), PE-bear and Process Hacker.

`antidump.c` is a small program that, once its startup is done, blanks the MZ and PE signatures of its own image in memory. It prints the ImageBase and then waits for Enter, which gives you time to work. Build it on Windows with:

```
cl antidump.c
rem or MinGW:
x86_64-w64-mingw32-gcc antidump.c -o antidump.exe
```

First, observe the anti-dump. Run `antidump.exe` and note the ImageBase it prints. Open Process Hacker, find the process and look at the memory region at ImageBase. Before the program prints "Wiped the PE header in memory", the first two bytes are `4D 5A` ("MZ"), and afterwards they become `00 00`. Try dumping the image with Scylla or PE-sieve and notice that the tool does not recognize a valid PE or produces a broken file.

Second, rebuild the header. In x64dbg, attach to the process while it waits for Enter and go to the ImageBase region. Restore the first two bytes to `4D 5A`, and at the `e_lfanew` offset (read the dword at `ImageBase+0x3C`) restore `50 45` ("PE"). Dump again with Scylla. This time the header is valid and the dump can be rebuilt. If you run out of time, increase the wait in the source or set a breakpoint right before `wipe_pe_header`.

Third, think about anti-attach. Suppose the program also had a background thread that every 3 seconds checks `IsDebuggerPresent` and calls `ExitProcess` when it sees a debugger. What happens when you attach in the second exercise, and how could you avoid it? A hint: spawn instead of attach, or use ScyllaHide.

Fourth, think about anti-hook. Suppose a program reads the first 5 bytes of `VirtualProtect` in memory and compares them with the first 5 bytes of the same function read from `C:\Windows\System32\kernel32.dll` on disk. If you inline-hook `VirtualProtect` with Detours, it detects that immediately. Which kind of hook is not caught by this prologue comparison?

<div class="lab-box">
<div class="lab-head"><b>LAB 15.7</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/15.7/src/antidump.c" download><i class="fa-solid fa-file-code"></i>src/antidump.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The x64dbg and Scylla workflow below is the standard procedure and needs a Windows machine. The C logic of `antidump.c` follows the PE layout (e_lfanew at offset 0x3C, the MZ and PE signatures), so build and run it on Windows to confirm.

For the anti-dump observation, after the run you see this at ImageBase:

```
Before: 4D 5A 90 00 ...        ("MZ")
...at ImageBase+e_lfanew:  50 45 00 00   ("PE\0\0")

After wipe_pe_header() is called:
        00 00 90 00 ...        (MZ wiped)
...at the NT headers:  00 00 00 00   (PE wiped)
```

When Scylla or PE-sieve scans the image at ImageBase, it doesn't match the PE pattern and reports that no header was found, or dumps a file that PE-bear reports as corrupt.

To rebuild the header in x64dbg, press `Ctrl+G` to go to ImageBase (the value the program prints, or look in the Memory Map for the main module). In the Dump window, restore the first 2 bytes to `4D 5A`. Read the dword at `ImageBase+0x3C` to get `e_lfanew`, go to `ImageBase + e_lfanew` and restore the 4 bytes `50 45 00 00`. Then open Scylla, choose the process, run IAT Autosearch if needed, and Dump. This time the header is valid. With a real sample you would also check `SizeOfImage` in the Optional Header (offset `e_lfanew + 0x18 + 0x38` for PE32+) in case it was changed to a nonsensical value, and set it back to the total size of the sections. Scylla's "Fix Dump" button does most of this work.

For anti-attach, if a thread checks periodically and then calls `ExitProcess`, attaching in the second exercise makes the process quit by itself after a few seconds and you lose your session. There are three ways around it. You can spawn instead of attach, opening `antidump.exe` directly in x64dbg from the start. A breakpoint at the entry point gives you control before the anti-attach code runs, and you can patch the check loop too. ScyllaHide hides `IsDebuggerPresent` and the common checks so the loop no longer sees the debugger. Or you can find that thread (the Threads view in x64dbg), set a breakpoint at the check function and patch it to always return "no debugger", or suspend the thread.

For anti-hook, comparing the 5 prologue bytes with the clean copy on disk catches inline hooks (Detours, MinHook, Frida inline) because they overwrite the function start with `jmp` or `push+ret`. The kind of hook this does not catch is the hardware breakpoint (DR0 to DR3). The CPU stops when execution reaches the address, but not a single byte of code is modified, so the prologue comparison still sees it clean. A hook placed at a different layer than the one being checked also slips through (for example a hook in `ntdll` when only `kernel32` is checked), although it is still inline and therefore risky if the program checks both layers. This is why, when you meet anti-hook, a hardware breakpoint is the safest choice.

The takeaways are these. Anti-dump doesn't stop you from reading memory, it only corrupts the metadata so automatic tools give up, and if you understand the PE layout you can rebuild it. Anti-attach loses to the spawn tactic. Anti-hook of the prologue-check kind loses to the hardware breakpoint.

</details>

## Key takeaways
Anti-attach blocks attaching after the program runs, by occupying the debug slot itself, patching `DbgUiRemoteBreakin`, or checking periodically, and you get around it by spawning instead of attaching. Anti-dump breaks the PE header in memory (wiping MZ/PE, wrong SizeOfImage) so the dump becomes garbage, and you get around it by dumping early and rebuilding the header (Scylla/PE-sieve).

Anti-hook compares API prologues against the clean copy on disk to detect inline hooks, EDR, or Frida. Hardware breakpoints are your best friend here, since they modify no bytes and leave no trace in the code. Strong protectors combine all three layers, so handle them in the order anti-debug, anti-attach, anti-hook, anti-dump.
