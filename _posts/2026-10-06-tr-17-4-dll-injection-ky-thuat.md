---
title: "Lesson 17.4: Recognizing DLL injection techniques"
date: 2026-10-06 09:43:00 +0700
categories: ["Technique Reverse", "Part 17 · Patching, Hooking, Injection"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
DLL injection is when one process forces another process to load and run its code. Legit software uses it now and then too (game overlays, accessibility tools, EDR), but malware uses it constantly: to run hidden inside a legitimate process like `explorer.exe`, dodge allowlists, and be hard to kill.

This lesson doesn't teach you to write an injector. The goal is the opposite: when you're dissecting a sample or looking at a suspicious process, you recognize right away "ah, this is CreateRemoteThread injection" or "this is manual mapping", know where to set breakpoints, and know which tool will show it. This is standard analyst knowledge, seen from the defender's side.

## A common frame for reading every injection technique

Whatever the variant, one injection almost always consists of three things:

1. **Open the target process** to get the rights to manipulate it (usually via `OpenProcess` with `PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_CREATE_THREAD`).
2. **Put code or the DLL path into the target's memory** (allocate a region, then write into it).
3. **Force the target to execute that code** (create a new thread, or hijack an existing thread, or use a Windows callback mechanism).

Catching this three-step chain is catching the injection. The differences between techniques mostly lie in steps 2 and 3.

## 1. LoadLibrary + CreateRemoteThread

This is the classic technique, the simplest, and still the most common.

**Mechanism (conceptually):** the injector writes the *string with the path to the DLL file* into the target's memory, then creates a remote thread that runs straight into the `kernel32` function `LoadLibraryW` with that string as the parameter. Since `LoadLibraryW` has a signature like a thread start routine (takes one pointer, returns one value), Windows happily runs it, and the DLL gets loaded through the standard loader.

**Characteristic API chain** (set breakpoints here when debugging):
```
OpenProcess
VirtualAllocEx        ; allocate a region in the target process
WriteProcessMemory    ; write the DLL path into that region
GetProcAddress        ; get the address of LoadLibraryW
CreateRemoteThread    ; run LoadLibraryW(dll_path)
```

**Tells:**
- A strange DLL shows up in the module list of a process that has no reason to load it (a DLL file in the temp folder, with a random name).
- A thread whose start address points straight at `LoadLibraryW`.
- A real DLL file on disk, since this technique needs the DLL to be a file (later techniques don't).

**Detection:** Process Hacker or System Informer, open the process, check the Modules tab for strange DLLs, check the Threads tab for a thread with a start address at `kernel32!LoadLibraryW`. Procmon catches the `Load Image` operation of the strange DLL.

## 2. SetWindowsHookEx

**Mechanism:** Windows lets you register a hook into the message chain of windows (for example `WH_KEYBOARD`, `WH_GETMESSAGE`). When the hook is in a DLL, Windows **automatically loads that DLL into every process with a window** that receives the corresponding message. So just registering a hook pointing at a function in your own DLL spreads the DLL everywhere, no `CreateRemoteThread` needed.

**Tells:** a `SetWindowsHookEx` call with `hMod` pointing to a strange DLL, and the DLL appearing in many GUI processes at once. Old keyloggers loved this approach.

**Detection:** the same suspicious DLL present in many processes; GMER and some anti-rootkit tools list hooks.

## 3. AppInit_DLLs (and other registry autoloads)

**Mechanism:** the registry key `HKLM\Software\Microsoft\Windows NT\CurrentVersion\Windows\AppInit_DLLs` lists DLLs that `user32.dll` automatically loads into every process that uses `user32`. Putting a DLL name there gets you persistence and system-wide injection in one, without touching any target process.

**Tells:** the `AppInit_DLLs` value is non-empty, `LoadAppInit_DLLs` equals 1. Other variants with the same idea: IFEO (Image File Execution Options) with `Debugger`, `Netsh Helper DLL`, `COM hijacking`.

**Detection:** Autoruns (Sysinternals) has a dedicated AppInit tab and scans almost every autoload point. This is the first place a blue team looks when suspecting persistence.

## 4. Manual mapping

This is the upgrade to **dodge the standard loader**. Instead of relying on `LoadLibrary`, the injector does the Windows loader's job by hand.

**Mechanism (conceptually):** the injector parses the DLL's PE itself, allocates a region in the target, copies each section into place, applies relocations itself, resolves imports (IAT) itself, then calls the entry point (DllMain). Since it doesn't go through `LoadLibrary`, the DLL **doesn't appear in the process's module list** (Windows doesn't know it exists in the official sense).

**Tells:** this is why manual mapping is favored for hiding, so the tells are more subtle:
- A `PRIVATE` memory region with execute permission (RX or RWX) that **doesn't belong to any module** (unbacked executable memory). This is the classic red flag.
- A full PE-like layout (the `MZ`/`PE` markers, section headers) inside a private region, even though the module list doesn't declare it.

**Detection:** **PE-sieve** and **HollowsHunter** were built precisely to catch this kind. They scan each memory region, compare against the file on disk, and report code regions that don't match a module or have no backing module. Process Hacker can also show strange regions with execute permission.

## 5. Reflective DLL loading

The same spirit as manual mapping but pushed further: **the DLL loads itself**. The DLL contains a special bootstrap function (a reflective loader) that can map itself into memory from a buffer, with no file on disk and no `LoadLibrary`.

**Mechanism:** the shellcode in the buffer finds the addresses of the APIs it needs (parsing the PEB to find `kernel32`, walking the export table to get `LoadLibraryA`/`GetProcAddress`), then does the loader's work itself. Since the DLL never sat on disk, static analysis of a file has almost nothing to grab onto.

**Tells:** like manual mapping (unbacked RX/RWX region, PE in private memory), plus the code parsing the PEB itself to resolve APIs (a pattern you've met in the anti-analysis lessons). Metasploit and Cobalt Strike use it widely, so their traces are well documented in threat intel material.

**Detection:** PE-sieve is still your best friend; besides that, behavior monitoring (a process suddenly allocating an RWX region and then running code in it) is a strong indicator for EDR.

## Analysis workflow when you suspect injection

1. **Triage the live process:** Process Hacker, look at Modules (strange DLLs) and Memory (private RX/RWX regions, unbacked).
2. **Run PE-sieve/HollowsHunter** on the suspect process, it dumps the implanted modules so you can open them in IDA/Ghidra.
3. **Dynamic monitoring:** Procmon filtered by process, watch for `Load Image` of strange paths and registry operations (AppInit, IFEO).
4. **If you have the injector sample:** set breakpoints at the API chain in each item above, read the parameters (tying back to [Lesson 1.13](/posts/tr-1-13-nhan-dien-windows-api/)) to know where it injects and how.
5. **Dump the injected payload** and analyze it as a standalone module.

Shellcode injection, APC injection, thread hijacking and process hollowing (variants of step 3) are split off into [Lesson 17.5](https://github.com/Haind03/Technique-Reverse/blob/main/phan-17-patch-hook-frida/17.5-shellcode-apc-hollowing.md).

## Key takeaways
- Almost every injection consists of: open the process, put code/path into the target's memory, force it to run.
- LoadLibrary + CreateRemoteThread: needs a DLL on disk, thread start = LoadLibraryW, the easiest to spot.
- SetWindowsHookEx and AppInit_DLLs: let Windows spread the DLL itself, inspect with Autoruns.
- Manual mapping and reflective loading: dodge the loader, the DLL isn't in the module list. The tell is a private execute region with no backing module.
- PE-sieve/HollowsHunter are the main detection tools; Process Hacker and Procmon support them.
