---
title: "Lesson 15.2: Anti-debug reading the PEB directly, when there's no API to hook"
image:
  path: /assets/img/covers/re-15-2-anti-debug-reading-peb-directly-when.webp
  alt: "Lesson 15.2: Anti-debug reading the PEB directly, when there's no API to hook"
date: 2023-05-09 22:59:00 +0700
categories: ["Technique Reverse", "Part 15 · Anti-Reversing and Bypasses"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
The previous lesson was about anti-debug calling APIs like IsDebuggerPresent. The weakness of that approach: if it's an API, you can set a breakpoint or hook on it and return a fake value, done. So smarter protector authors skip the API and read the memory structure directly, the one that API was only reading on your behalf. There's no call left for you to intercept, just a few `mov` instructions reading memory, mixed in with ordinary code. This is the more annoying group of anti-debug, and it's also why you need to understand the PEB from [Lesson 1.11](/posts/re-1-11-windows-internals-2-peb-teb-handles/).

## Where the PEB is, and why a program can read it itself

The PEB (Process Environment Block) is a struct Windows creates for each process, holding information about that process. IsDebuggerPresent really just reads one byte in the PEB and returns it. If the program finds the PEB itself, it gets exactly that information without calling anyone.

The PEB is always reachable through a segment register, no API needed. On x64, `gs:[0x60]` points to the PEB, and on x86, `fs:[0x30]` does.

Seeing a read of `gs:[0x60]` (or `fs:[0x30]`) should put you on alert right away: the program is fetching the PEB itself, and nine times out of ten it's to check an anti-debug flag.

## BeingDebugged, the byte that gives you away

The simplest field is `PEB.BeingDebugged` at offset `0x2`. It's 1 when the process is being debugged, 0 when not. This is exactly what IsDebuggerPresent returns.

A typical asm snippet on x64:

```asm
mov  rax, gs:[0x60]     ; rax = PEB address
movzx eax, byte ptr [rax+2]  ; eax = PEB.BeingDebugged
test eax, eax
jnz  detected           ; nonzero means being debugged
```

Translated to C it's equivalent to:

```c
if (((PEB*)__readgsqword(0x60))->BeingDebugged)
    exit_or_crash();
```

How to recognize it: read `gs:[0x60]`, then read the byte at `[rax+2]`, then `test` and jump. No API name shows up, so searching by function name misses it. You have to search for the segment access pattern.

## NtGlobalFlag, a subtler trace

`PEB.NtGlobalFlag` is at offset `0xBC` (x64) or `0x68` (x86). When a process is created under a debugger, the loader turns on three flags in this field: `FLG_HEAP_ENABLE_TAIL_CHECK` (0x10), `FLG_HEAP_ENABLE_FREE_CHECK` (0x20) and `FLG_HEAP_VALIDATE_PARAMETERS` (0x40).

Added together that's `0x70`. So the usual check looks like:

```asm
mov  rax, gs:[0x60]
mov  eax, [rax+0xBC]    ; eax = NtGlobalFlag
and  eax, 0x70
cmp  eax, 0x70
jz   detected           ; all three flags on means a debugger is present
```

This field is subtler than BeingDebugged because many beginners don't know it exists, and it's set by the loader and not by the program's code, so patching BeingDebugged alone isn't enough.

## Heap flags, a knock-on effect

The NtGlobalFlag above makes the heap get created in debug mode, leaving a mark in the heap header itself. Two fields, `Flags` and `ForceFlags` in the heap structure (get the heap through `PEB.ProcessHeap` at offset `0x30` on x64), hold different values when a debugger is present. Normally `Flags` = `HEAP_GROWABLE` (0x2) and `ForceFlags` = 0, but under a debugger `Flags` has extra bits like `HEAP_TAIL_CHECKING_ENABLED` and `ForceFlags` is nonzero.

The checking code gets ProcessHeap and reads `ForceFlags`, and if it's nonzero it knows. The offsets of Flags/ForceFlags in the heap differ by Windows version, so this is a version-picky check, less common but it still shows up.

## Why this group is harder than the API group

With the API group (Lesson 15.1), you set a breakpoint at `IsDebuggerPresent` and force it to return 0. This group has no function to put a breakpoint on. The code is just `mov` and `cmp` mixed in with normal logic, looking no different from reading an ordinary variable. You have to read and understand it to realize it's reading a sensitive PEB offset.

A quick tip for recognizing it when reading statically: find every spot that touches `gs:[0x60]` (x64) or `fs:[0x30]` (x86), then see which offset it reads next. A byte at `[...+2]` is BeingDebugged, a dword at `[...+0xBC]` is NtGlobalFlag, and `[...+0x30]` followed by a read into the heap is the ProcessHeap flags.

## How to get past it

Since these flags live in the memory of your own process (running in the debugger), you can modify them directly. You can edit by hand in the debugger: before the check code runs, go to the PEB and write `BeingDebugged = 0`, clear the three bits of NtGlobalFlag. In x64dbg, use `dump` on the PEB then edit the byte, or use an expression. You can also use ScyllaHide, which does it automatically and thoroughly: it cleans BeingDebugged, NtGlobalFlag, heap flags, and a whole bunch of other checks as soon as the process starts. For most user-mode anti-debug, turning on ScyllaHide is it, no need to patch each one. See also [Lesson 15.9](/posts/re-15-9-bypassing-anti-debug-from-mouse-click/). The third option is to patch the check code: if there are only a few places, flip the detecting `jnz`/`jz` to jump the opposite way, or NOP out the check. This holds up if you plan to run it many times.

Usually ScyllaHide is the first choice because it covers almost the whole PEB group in one go. Patching by hand is for when you want to understand each check clearly or when the check is well hidden.

## Lab

The goal is to see with your own eyes an anti-debug check that calls no API, and to practice recognizing it in the disassembly and getting past it. The platform is Windows x64, since the file uses the PEB and so won't run on Linux. You need x64dbg, and optionally IDA or Ghidra and ScyllaHide. Build `peb_check.c` with MSVC:

```
cl /O2 peb_check.c
```

or with MinGW:

```
x86_64-w64-mingw32-gcc -O2 peb_check.c -o peb_check.exe
```

Run `peb_check.exe` normally (double-click or in cmd), write down the output and note that it reports no debugger detected. Then open `peb_check.exe` in x64dbg and run until it prints to the screen. This time it reports a debugger. Why, and which field is set? Open it in IDA or Ghidra and find the code that reads `gs:[0x60]`. Which offset does it read right after that? Compare with the lesson: what is `+2` and what is `+0xBC`?

In x64dbg, before the check code runs, set `BeingDebugged` to 0 and clear the three bits of `NtGlobalFlag`, then continue and see whether it still reports a detection. After that install ScyllaHide for x64dbg, turn it on and run again from the start without editing anything by hand, and compare the result.

A few questions to think about. Why is a breakpoint at `IsDebuggerPresent` useless in this lab? Is patching `BeingDebugged` alone enough, or does `NtGlobalFlag` still give you away? And if you were writing a protector, what other sensitive offsets in the PEB could you read?

<div class="lab-box">
<div class="lab-head"><b>LAB 15.2</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/15.2/src/peb_check.c" download><i class="fa-solid fa-file-code"></i>src/peb_check.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

This solution describes the results that follow from the Windows mechanism and from how MSVC and MinGW generate code for the PEB-reading intrinsics. The file needs the PEB of Windows x64, so run it on Windows to compare.

Running normally prints:

```
BeingDebugged = 0
NtGlobalFlag debug bits = 0
No debugger detected.
```

With no debugger, both fields are clean. Running inside x64dbg prints:

```
BeingDebugged = 1
NtGlobalFlag debug bits = 1
Debugger detected (PEB).
```

x64dbg creates the process under the debugger, so the loader sets `BeingDebugged = 1` and puts the three heap debug flags in `NtGlobalFlag` (a total of `0x70`). Both checks fire.

In the disassembly, `check_being_debugged` compiles to roughly:

```asm
mov   rax, gs:[0x60]          ; get the PEB
movzx eax, byte ptr [rax+2]   ; BeingDebugged
```

and `check_nt_global_flag` to:

```asm
mov   rax, gs:[0x60]
mov   eax, [rax+0xBC]         ; NtGlobalFlag
and   eax, 0x70
cmp   eax, 0x70
```

There is no API name anywhere. The anchor you recognize it by is `gs:[0x60]`, and then the offset read next tells you which check it is: `+2` is `BeingDebugged` and `+0xBC` is `NtGlobalFlag`.

To fix the flags by hand in x64dbg, get the PEB address (the `peb()` command, or look in the Memory Map tab, or use `dump peb()+2`). Before the check function runs, write 0 to the byte at `PEB+0x2` (`BeingDebugged`) and write 0 (or clear the `0x70` bits) in the dword at `PEB+0xBC` (`NtGlobalFlag`). Continue and the program prints `No debugger detected.` Note that if you only fix `BeingDebugged` and forget `NtGlobalFlag`, the second check still fires, and that is the point of the task.

With ScyllaHide, turn on the PEB options (BeingDebugged, NtGlobalFlag, HeapFlags) and run again from the start without editing by hand. It cleans every PEB flag automatically and the program reports it isn't being debugged. That is why ScyllaHide is the first choice: one switch covers the whole group.

On the questions, a breakpoint on `IsDebuggerPresent` is useless because the program never calls that function and reads the byte in the PEB directly, so there is no call to stop at. Patching `BeingDebugged` alone isn't enough, because `NtGlobalFlag` is an independent check, set by the loader, and still gives you away, so you must handle both (and the heap flags if present). Other sensitive offsets in the PEB include `ProcessHeap` (`+0x30`) for reading the heap's Flags and ForceFlags, the `Ldr` pointer for walking the loaded modules yourself (to detect a debugger or hook DLL), and other fields depending on the version.

</details>

## Key takeaways
The PEB can be accessed without an API: `gs:[0x60]` (x64), `fs:[0x30]` (x86), and when you see it, be alert. BeingDebugged is at offset `0x2` and is 1 when debugged. NtGlobalFlag is at offset `0xBC` (x64), the three heap debug bits add up to `0x70`, and it's set by the loader and not by the code. Heap Flags/ForceFlags are nonzero when a debugger is present, though that check is picky about the Windows version.

This group has no API to hook, so you have to read and recognize the segment access pattern. To get past it, edit the flags in memory, use ScyllaHide (fastest), or patch the check branch.
