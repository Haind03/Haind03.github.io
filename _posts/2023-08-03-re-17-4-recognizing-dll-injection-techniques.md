---
title: "Lesson 17.4: Recognizing DLL injection techniques"
image:
  path: /assets/img/covers/re-17-4-recognizing-dll-injection-techniques.webp
  alt: "Lesson 17.4: Recognizing DLL injection techniques"
date: 2023-08-03 23:30:00 +0700
categories: ["Technique Reverse", "Part 17 · Patching, Hooking, Injection"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
DLL injection is when one process forces another process to load and run its code. Legit software uses it now and then too (game overlays, accessibility tools, EDR), but malware uses it all the time to run hidden inside a legitimate process like `explorer.exe`, dodge allowlists, and be hard to kill.

This lesson doesn't teach you to write an injector. The goal is the opposite. When you're dissecting a sample or looking at a suspicious process, you should be able to say "this is CreateRemoteThread injection" or "this is manual mapping", know where to set breakpoints, and know which tool will show it. This is standard analyst knowledge, from the defender's side.

## A common frame for reading every injection technique

Whatever the variant, an injection almost always has three steps. First it opens the target process to get the rights to manipulate it (usually via `OpenProcess` with `PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_CREATE_THREAD`). Then it puts code or the DLL path into the target's memory (allocate a region, then write into it). Finally it forces the target to execute that code (create a new thread, hijack an existing thread, or use a Windows callback mechanism).

If you catch this three-step chain, you've caught the injection. The techniques mostly differ in steps 2 and 3.

## 1. LoadLibrary + CreateRemoteThread

This is the classic technique, the simplest, and still the most common.

The injector writes the string with the path to the DLL file into the target's memory, then creates a remote thread that starts at the `kernel32` function `LoadLibraryW` with that string as the parameter. `LoadLibraryW` has a signature like a thread start routine (takes one pointer, returns one value), so Windows runs it without complaint, and the DLL gets loaded through the standard loader.

The characteristic API chain is below, and it's where to set breakpoints when debugging:
```
OpenProcess
VirtualAllocEx        ; allocate a region in the target process
WriteProcessMemory    ; write the DLL path into that region
GetProcAddress        ; get the address of LoadLibraryW
CreateRemoteThread    ; run LoadLibraryW(dll_path)
```

The tells are a strange DLL in the module list of a process that has no reason to load it (a DLL file in the temp folder, with a random name), a thread whose start address points straight at `LoadLibraryW`, and a real DLL file on disk, since this technique needs the DLL to be a file (later techniques don't).

To detect it, open the process in Process Hacker or System Informer, check the Modules tab for strange DLLs, and check the Threads tab for a thread with a start address at `kernel32!LoadLibraryW`. Procmon catches the `Load Image` operation of the strange DLL.

## 2. SetWindowsHookEx

Windows lets you register a hook into the message chain of windows (for example `WH_KEYBOARD`, `WH_GETMESSAGE`). When the hook is in a DLL, Windows automatically loads that DLL into every process with a window that receives the corresponding message. So registering a hook that points at a function in your own DLL spreads the DLL everywhere, with no `CreateRemoteThread`.

The tells are a `SetWindowsHookEx` call with `hMod` pointing to a strange DLL, and the DLL appearing in many GUI processes at once. Old keyloggers used this a lot. For detection, look for the same suspicious DLL present in many processes. GMER and some anti-rootkit tools list hooks.

## 3. AppInit_DLLs (and other registry autoloads)

The registry key `HKLM\Software\Microsoft\Windows NT\CurrentVersion\Windows\AppInit_DLLs` lists DLLs that `user32.dll` automatically loads into every process that uses `user32`. Putting a DLL name there gives you persistence and system-wide injection together, without touching any target process.

The tells are an `AppInit_DLLs` value that's non-empty and `LoadAppInit_DLLs` equal to 1. Other variants with the same idea are IFEO (Image File Execution Options) with `Debugger`, `Netsh Helper DLL`, and `COM hijacking`. For detection, Autoruns (Sysinternals) has a dedicated AppInit tab and scans almost every autoload point. A blue team checks here first when it suspects persistence.

## 4. Manual mapping

This one avoids the standard loader. Instead of relying on `LoadLibrary`, the injector does the Windows loader's job by hand.

The injector parses the DLL's PE itself, allocates a region in the target, copies each section into place, applies relocations itself, resolves imports (IAT) itself, then calls the entry point (DllMain). Since it doesn't go through `LoadLibrary`, the DLL doesn't appear in the process's module list (Windows doesn't know it's there in the official sense).

Because manual mapping is used for hiding, the tells are more subtle. One is a `PRIVATE` memory region with execute permission (RX or RWX) that doesn't belong to any module (unbacked executable memory), which is the classic sign of this technique. Another is a full PE-like layout (the `MZ`/`PE` markers, section headers) inside a private region, even though the module list doesn't show it.

PE-sieve and HollowsHunter were built to catch this kind. They scan each memory region, compare against the file on disk, and report code regions that don't match a module or have no backing module. Process Hacker can also show strange regions with execute permission.

## 5. Reflective DLL loading

Same idea as manual mapping but pushed further, where the DLL loads itself. The DLL contains a special bootstrap function (a reflective loader) that can map itself into memory from a buffer, with no file on disk and no `LoadLibrary`.

The shellcode in the buffer finds the addresses of the APIs it needs (parsing the PEB to find `kernel32`, walking the export table to get `LoadLibraryA`/`GetProcAddress`), then does the loader's work itself. Since the DLL never sat on disk, static analysis of a file has almost nothing to work with.

The tells are like manual mapping (unbacked RX/RWX region, PE in private memory), plus the code parsing the PEB itself to resolve APIs (a pattern you've met in the anti-analysis lessons). Metasploit and Cobalt Strike use it widely, so their traces are well documented in threat intel material. PE-sieve is still the best detection tool here. Behavior monitoring also works well for EDR, since a process suddenly allocating an RWX region and then running code in it is a strong indicator.

## Analysis workflow when you suspect injection

Start by triaging the live process. In Process Hacker, look at Modules (strange DLLs) and Memory (private RX/RWX regions, unbacked). Then run PE-sieve/HollowsHunter on the suspect process, which dumps the implanted modules so you can open them in IDA/Ghidra. Next, do dynamic monitoring with Procmon filtered by process, watching for `Load Image` of strange paths and registry operations (AppInit, IFEO).

If you have the injector sample, set breakpoints at the API chain in each item above and read the parameters (see [Lesson 1.13](/posts/re-1-13-recognizing-windows-apis-when-reversing-reading/)) to know where it injects and how. Finally, dump the injected payload and analyze it as a standalone module.

Shellcode injection, APC injection, thread hijacking and process hollowing (variants of step 3) are in [Lesson 17.5](/technique-reverse/).

## Lab

This lab trains a blue-team/analyst skill, recognizing that a process has been injected into and working out which technique was used. There's no injector to write here, only observation and detection. You need Windows (a VM, following Lesson 0.3 if you're using a real sample), Process Hacker or System Informer, PE-sieve and HollowsHunter (from hasherezade's GitHub), and Procmon and Autoruns from Sysinternals. For a safe suspicious process to practice on, use a sample from an authorized malware lab, a legitimate game overlay app (these also use injection), or a public sample from MalwareBazaar run inside an isolated VM.

Start by inspecting modules. Open a process in Process Hacker's Modules tab and list any DLL sitting at an unusual path, such as temp, AppData, or a randomized name. Then inspect threads, in the Threads tab, looking for one whose start address points into `kernel32!LoadLibraryW` or into a memory region that doesn't belong to any module, since that's a sign of CreateRemoteThread injection. Next inspect memory, in the Memory tab, looking for a `Private` region whose protection includes `Execute` (RX/RWX) and whose Use column isn't tied to any module file, which is suspicious for manual mapping or reflective loading.

Run PE-sieve with `pe-sieve.exe /pid <PID>` and read its report, which lists implanted or patched modules and dumps them to a folder, then open the dumped file in Ghidra or IDA. Scan registry autoload points with Autoruns, checking the AppInit tab and other autoload entries for any unfamiliar DLL configured to load system-wide.

Finally, pull the signals together. Based on what you found, decide which of the five techniques from the lesson was used, and write down your reasoning.

Three questions worth thinking through. Why is manual mapping harder to detect than LoadLibrary injection just by looking at the module list? What does a private, RWX memory region with no backing module tell you? And if a DLL never touched disk at all, what static tool still lets you get its code for analysis?

Do it yourself first, the reference answers are below.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

This write-up describes the standard detection procedure and a signal table. The Process Hacker and PE-sieve steps need a Windows machine and a specific process to look at. The table below is based on each technique's and tool's documented behavior.

A signal and detection table:

| Technique | API chain / mechanism | Signal during analysis | Detection tool |
|---|---|---|---|
| LoadLibrary + CreateRemoteThread | OpenProcess, VirtualAllocEx, WriteProcessMemory, CreateRemoteThread(LoadLibraryW) | Unfamiliar DLL in the module list; thread start = LoadLibraryW; the DLL exists on disk | Process Hacker (Modules, Threads), Procmon (Load Image) |
| SetWindowsHookEx | SetWindowsHookEx with hMod being an unfamiliar DLL | The same DLL present in several GUI processes | Autoruns, GMER, cross-process module listing |
| AppInit_DLLs | The AppInit_DLLs registry value with LoadAppInit_DLLs=1 | A non-empty registry value; the DLL loads system-wide | Autoruns (AppInit tab) |
| Manual mapping | Parsing the PE itself, mapping sections, applying relocations, resolving the IAT, calling DllMain | An executable PRIVATE region with no backing module; a PE-shaped layout sitting in private memory; absent from the module list | PE-sieve, HollowsHunter |
| Reflective DLL loading | The DLL maps itself from a buffer and resolves APIs itself via the PEB | Same as manual mapping plus code that parses the PEB to find APIs; never touches disk | PE-sieve, monitoring for RWX allocation followed by execution |

On inspecting modules, a legitimate DLL usually sits in `C:\Windows\System32` or the app's own install folder. A DLL in `%TEMP%`, `%APPDATA%`, or with a randomized name is suspicious enough to point at LoadLibrary-based injection.

On inspecting threads, a thread created by injection usually has a start address of `LoadLibraryW` (the classic CreateRemoteThread pattern) or points into a memory region not mapped to any module (a shellcode or reflective pattern). A legitimate thread's start address sits inside a known module.

On inspecting memory, a `MEM_PRIVATE` region with `PAGE_EXECUTE_READWRITE` or `PAGE_EXECUTE_READ` that isn't tied to any file is a sign of code placed into memory outside the normal loader path. Legitimate code almost always lives in a `MEM_IMAGE` region, backed by a module file, and is read plus execute only.

On the PE-sieve report, it classifies each module as clean, hooked, replaced, or implanted, and dumps the suspicious ones, and the dumped file opens in IDA or Ghidra to read the payload.

On the registry scan, Autoruns gathers every autoload point. A non-empty AppInit_DLLs is suspicious, and it's worth also checking IFEO Debugger entries and COM/Netsh helper DLLs.

Pulling it together, the reasoning goes like this. A DLL on disk plus a LoadLibraryW thread points to CreateRemoteThread injection. The same DLL across multiple GUI processes points to SetWindowsHookEx. A DLL loading everywhere plus a populated AppInit registry value points to AppInit_DLLs. Executable private code with no module and a PE-sieve report of implanted content points to manual mapping or reflective loading, distinguished by whether the code resolves its own APIs by parsing the PEB.

Why is manual mapping harder to detect? `LoadLibrary` registers the DLL with the loader, so it shows up in the module list (the PEB's `InLoadOrderModuleList`). Manual mapping bypasses the loader entirely, so Windows never learns the DLL exists and the module list stays clean. You have to inspect memory instead of modules.

What does an RWX private region with no backing module tell you? Legitimate code comes from a file (MEM_IMAGE, RX only). A private region that's both writable and executable is where decrypted code, shellcode, or a manually mapped module typically ends up. It's rare in clean software, which makes it a strong indicator.

What do you use when the DLL never touched disk? PE-sieve can dump it straight out of live memory, since while it's running it has to exist in RAM regardless. Once dumped, you have an ordinary file to analyze statically like any other module.

</details>

## Key takeaways
Almost every injection consists of opening the process, putting code or a path into the target's memory, and forcing it to run. LoadLibrary + CreateRemoteThread needs a DLL on disk, has a thread start of LoadLibraryW, and is the easiest to spot. SetWindowsHookEx and AppInit_DLLs let Windows spread the DLL itself, and you inspect them with Autoruns. Manual mapping and reflective loading dodge the loader so the DLL isn't in the module list, and the tell is a private execute region with no backing module. PE-sieve/HollowsHunter are the main detection tools, with Process Hacker and Procmon supporting them.
