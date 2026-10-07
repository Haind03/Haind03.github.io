---
title: "Lesson 2.8: System monitoring, watching behavior without opening a debugger"
date: 2026-10-06 08:24:00 +0700
categories: ["Technique Reverse", "Part 02 · The Toolkit"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
Here's a comforting truth for beginners: a lot of the time you can tell what a program is doing without reading a single line of assembly. You just have to watch where it touches the system. Where it creates files, which registry keys it writes, which server it calls, what child processes it spawns. This is called behavioral analysis, and it's often the first dynamic step before you decide whether you need to sit down and debug in detail.

This lesson is the observation toolkit. None of it is hard to use, the hard part is knowing how to read the pile of events they spit out.

## Procmon, a diary of everything

Process Monitor (Procmon, from Sysinternals) records nearly every interaction between processes and the operating system in real time: file operations, registry, process creation/exit, basic network activity, and threads. Run it for a few seconds and you have tens of thousands of lines, so the real skill is in filtering.

The standard habits:

- Open Procmon, turn on capture, run the target program, then turn capture off right away so you don't drown.
- Filter by process first: `Process Name is <name>.exe then Include`. The whole sea of events shrinks to just what you need.
- Then filter by operation type with the buttons on the toolbar: file system, registry, network, process/thread. If you want to see what files it writes, only turn on file system.
- The columns worth looking at: Operation (e.g. `CreateFile`, `RegSetValue`, `WriteFile`), Path (which file or key), Result (`SUCCESS` or `NAME NOT FOUND`), and Detail.

A few patterns you can read right away without disassembling:
- A series of `RegSetValue` into `...\CurrentVersion\Run` means the program is installing persistence, that is, making itself run again after the machine boots.
- `CreateFile` then `WriteFile` into `%TEMP%` then `Process Create` of the file it just wrote: the classic sign of a dropper, dropping a payload and then running it.
- `RegQueryValue` on keys like `...\VMware` or `...\VirtualBox` means it's checking whether it's running in a virtual machine (anti-VM, covered in Part 15).

Procmon doesn't tell you why, but it tells you what and in which order. That's already half the story.

## Process Hacker / System Informer, a microscope for processes

Process Hacker (the successor goes by the name System Informer) is a Task Manager edition for people doing RE. It lets you look inside a running process:

- The process tree: who spawned whom, with color coding (services, .NET processes, packed...).
- The Memory tab: view the memory map, and importantly a button to scan strings right in live memory. Many programs hide strings on disk but have to decrypt them into RAM at runtime, and this is where you catch them.
- The Handles tab: the files, registry keys, mutexes, and events the process has open. Mutexes are especially useful, a lot of malware creates a mutex with a fixed name to avoid running twice, and that name becomes an IOC for identification.
- The Threads tab: view each thread's call stack, find the start point.
- Right-click a memory region or module and you can dump it to disk for static analysis, very handy when the code has been unpacked in memory.

When you suspect a program decrypts strings at runtime, opening Process Hacker and scanning memory strings is much faster than hunting for the decryption routine in a disassembler.

## Process Explorer, the slimmer version

Process Explorer is also from Sysinternals, lighter than Process Hacker, strong at the process tree, viewing the DLLs a process loaded, and quickly looking up who is holding a handle. If you only need an overview and parent-child relationships, it's enough. Process Hacker fits better when you need to dig into memory and handles.

## API Monitor, eavesdropping on API calls

Procmon only sees interactions at the operating system level. API Monitor gets closer to the code: it hooks and records Win32 API calls with the real parameters and return values. You pick the API groups you want to follow (file, registry, memory, crypto, network...), run the program, and then read things like:

- `CreateFileW(L"C:\\Users\\...\\secret.dat", GENERIC_READ, ...)`, giving you the full file name right away.
- `CryptEncrypt(...)` or `VirtualAlloc(..., PAGE_EXECUTE_READWRITE)`, allocating memory that's both writable and executable, a common red flag when code is preparing to run a payload.

The strength is seeing parameters in a human-readable form. The weakness is that a lot of malware evades its hooks, or calls the Native API/syscalls directly to go around (mentioned in lesson 1.12). When API Monitor is suspiciously silent, that silence is itself a clue.

## Autoruns, inspecting persistence

Autoruns lists nearly every spot where something can auto-start on Windows: Run keys, scheduled tasks, services, drivers, Explorer plugins, and dozens of other places you wouldn't think of. After running a sample, comparing Autoruns before and after shows right away what it planted to survive the next boot. There's an option to hide entries signed by Microsoft to cut down the noise.

## Wireshark, looking at network traffic

When a program talks to the outside, Wireshark captures every packet. You see which domain it resolves (DNS), which IP and port it connects to, and if it's not encrypted, even the contents. For malware, this is how you find the command-and-control (C2) server and understand the communication protocol. Remember to set up the lab network correctly: you usually run in a simulated network environment (INetSim/FakeNet) so the sample thinks it reached the internet while the packets go nowhere, see lesson 0.3.

## On Linux: strace and ltrace

The Linux world is tidier, and two commands are enough for most jobs:

- `strace ./program` records every system call: `open`, `read`, `write`, `connect`, `execve`. The equivalent of Procmon at the syscall level.
- `ltrace ./program` records calls to library functions (libc...), close to API Monitor. You see `strcmp`, `malloc`, `fopen` with their parameters right away.

For example, running `strace` on a license-checking program sometimes straight out reveals that it `open`s the file `/etc/mylicense` or `connect`s to an IP, and you understand the mechanism without opening a disassembler.

## Putting it together into a picture

No single tool gives you the full answer, but added together they do:

- Procmon answers which files and registry it touches.
- Process Hacker answers what it's hiding in memory, and which mutexes and handles it holds.
- API Monitor answers which APIs it calls and with what parameters.
- Autoruns answers where it plants itself to live long.
- Wireshark answers who it talks to.

Run the sample once with this whole set turned on, and you have a behavior profile before touching a single line of assembly. From that profile you decide which spots are worth sitting down and debugging deeply. That's exactly the spirit of triage, static, dynamic in lesson 0.4, the only difference being that the dynamic here is done by observation rather than by a debugger.

And a reminder to be sure: everything in this lesson, when the target is real malware, has to run in an isolated VM per [Lesson 0.3](/posts/tr-0-3-dung-lab-an-toan/). Turning on Procmon doesn't make you any safer, the program still really runs.

## Key takeaways
- Behavioral analysis tells you what a program does, often without reading assembly.
- Procmon: filter by process name first, then by operation type (file/registry/network).
- Process Hacker: scan strings in live memory, view handles and mutexes, dump unpacked regions.
- API Monitor: shows API calls with human-readable parameters; unusual silence is also a clue.
- Autoruns to inspect persistence, Wireshark to inspect the network.
- Linux: strace for syscalls, ltrace for library functions.
- Real malware: always in an isolated VM.
