---
title: "Lesson 17.4: Recognizing DLL injection techniques"
date: 2023-08-03 23:30:00 +0700
categories: ["Technique Reverse", "Part 17 · Patching, Hooking, Injection"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
DLL injection is when one process forces another process to load and run its code. Legit software uses it now and then too (game overlays, accessibility tools, EDR), but malware uses it constantly: to run hidden inside a legitimate process like `explorer.exe`, dodge allowlists, and be hard to kill.

This lesson doesn't teach you to write an injector. The goal is the opposite: when you're dissecting a sample or looking at a suspicious process, you recognize right away "ah, this is CreateRemoteThread injection" or "this is manual mapping", know where to set breakpoints, and know which tool will show it. This is standard analyst knowledge, seen from the defender's side.

## A common frame for reading every injection technique

Whatever the variant, one injection almost always consists of three things. First it opens the target process to get the rights to manipulate it (usually via `OpenProcess` with `PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_CREATE_THREAD`). Then it puts code or the DLL path into the target's memory (allocate a region, then write into it). Finally it forces the target to execute that code (create a new thread, or hijack an existing thread, or use a Windows callback mechanism).

Catching this three-step chain is catching the injection. The differences between techniques mostly lie in steps 2 and 3.

## 1. LoadLibrary + CreateRemoteThread

This is the classic technique, the simplest, and still the most common.

Conceptually, the injector writes the string with the path to the DLL file into the target's memory, then creates a remote thread that runs straight into the `kernel32` function `LoadLibraryW` with that string as the parameter. Since `LoadLibraryW` has a signature like a thread start routine (takes one pointer, returns one value), Windows happily runs it, and the DLL gets loaded through the standard loader.

The characteristic API chain is below, and it's where to set breakpoints when debugging:
```
OpenProcess
VirtualAllocEx        ; allocate a region in the target process
WriteProcessMemory    ; write the DLL path into that region
GetProcAddress        ; get the address of LoadLibraryW
CreateRemoteThread    ; run LoadLibraryW(dll_path)
```

The tells are a strange DLL showing up in the module list of a process that has no reason to load it (a DLL file in the temp folder, with a random name), a thread whose start address points straight at `LoadLibraryW`, and a real DLL file on disk, since this technique needs the DLL to be a file (later techniques don't).

To detect it, open the process in Process Hacker or System Informer, check the Modules tab for strange DLLs, and check the Threads tab for a thread with a start address at `kernel32!LoadLibraryW`. Procmon catches the `Load Image` operation of the strange DLL.

## 2. SetWindowsHookEx

Windows lets you register a hook into the message chain of windows (for example `WH_KEYBOARD`, `WH_GETMESSAGE`). When the hook is in a DLL, Windows automatically loads that DLL into every process with a window that receives the corresponding message. So just registering a hook pointing at a function in your own DLL spreads the DLL everywhere, no `CreateRemoteThread` needed.

The tells are a `SetWindowsHookEx` call with `hMod` pointing to a strange DLL, and the DLL appearing in many GUI processes at once. Old keyloggers loved this approach. For detection, look for the same suspicious DLL present in many processes; GMER and some anti-rootkit tools list hooks.

## 3. AppInit_DLLs (and other registry autoloads)

The registry key `HKLM\Software\Microsoft\Windows NT\CurrentVersion\Windows\AppInit_DLLs` lists DLLs that `user32.dll` automatically loads into every process that uses `user32`. Putting a DLL name there gets you persistence and system-wide injection in one, without touching any target process.

The tells are an `AppInit_DLLs` value that's non-empty and `LoadAppInit_DLLs` equal to 1. Other variants with the same idea are IFEO (Image File Execution Options) with `Debugger`, `Netsh Helper DLL`, and `COM hijacking`. For detection, Autoruns (Sysinternals) has a dedicated AppInit tab and scans almost every autoload point. This is the first place a blue team looks when suspecting persistence.

## 4. Manual mapping

This is the upgrade to dodge the standard loader. Instead of relying on `LoadLibrary`, the injector does the Windows loader's job by hand.

Conceptually, the injector parses the DLL's PE itself, allocates a region in the target, copies each section into place, applies relocations itself, resolves imports (IAT) itself, then calls the entry point (DllMain). Since it doesn't go through `LoadLibrary`, the DLL doesn't appear in the process's module list (Windows doesn't know it exists in the official sense).

This is why manual mapping is favored for hiding, so the tells are more subtle. One is a `PRIVATE` memory region with execute permission (RX or RWX) that doesn't belong to any module (unbacked executable memory), which is the classic red flag. Another is a full PE-like layout (the `MZ`/`PE` markers, section headers) inside a private region, even though the module list doesn't declare it.

PE-sieve and HollowsHunter were built precisely to catch this kind. They scan each memory region, compare against the file on disk, and report code regions that don't match a module or have no backing module. Process Hacker can also show strange regions with execute permission.

## 5. Reflective DLL loading

The same spirit as manual mapping but pushed further: the DLL loads itself. The DLL contains a special bootstrap function (a reflective loader) that can map itself into memory from a buffer, with no file on disk and no `LoadLibrary`.

The shellcode in the buffer finds the addresses of the APIs it needs (parsing the PEB to find `kernel32`, walking the export table to get `LoadLibraryA`/`GetProcAddress`), then does the loader's work itself. Since the DLL never sat on disk, static analysis of a file has almost nothing to grab onto.

The tells are like manual mapping (unbacked RX/RWX region, PE in private memory), plus the code parsing the PEB itself to resolve APIs (a pattern you've met in the anti-analysis lessons). Metasploit and Cobalt Strike use it widely, so their traces are well documented in threat intel material. PE-sieve is still your best friend for detection; besides that, behavior monitoring (a process suddenly allocating an RWX region and then running code in it) is a strong indicator for EDR.

## Analysis workflow when you suspect injection

Start by triaging the live process: in Process Hacker, look at Modules (strange DLLs) and Memory (private RX/RWX regions, unbacked). Then run PE-sieve/HollowsHunter on the suspect process, which dumps the implanted modules so you can open them in IDA/Ghidra. Next, do dynamic monitoring with Procmon filtered by process, watching for `Load Image` of strange paths and registry operations (AppInit, IFEO).

If you have the injector sample, set breakpoints at the API chain in each item above and read the parameters (tying back to [Lesson 1.13](/posts/re-1-13-recognizing-windows-apis-when-reversing-reading/)) to know where it injects and how. Finally, dump the injected payload and analyze it as a standalone module.

Shellcode injection, APC injection, thread hijacking and process hollowing (variants of step 3) are split off into [Lesson 17.5](https://github.com/Haind03/Technique-Reverse/blob/main/phan-17-patch-hook-frida/17.5-shellcode-apc-hollowing.md).

## Key takeaways
Almost every injection consists of opening the process, putting code or a path into the target's memory, and forcing it to run. LoadLibrary + CreateRemoteThread needs a DLL on disk, has a thread start of LoadLibraryW, and is the easiest to spot. SetWindowsHookEx and AppInit_DLLs let Windows spread the DLL itself, and you inspect them with Autoruns. Manual mapping and reflective loading dodge the loader so the DLL isn't in the module list, and the tell is a private execute region with no backing module. PE-sieve/HollowsHunter are the main detection tools, with Process Hacker and Procmon supporting them.
