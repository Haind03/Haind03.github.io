---
title: "Lesson 2.8: System monitoring, watching behavior without opening a debugger"
image:
  path: /assets/img/covers/re-2-8-system-monitoring-watching-behavior-without-opening.webp
  alt: "Lesson 2.8: System monitoring, watching behavior without opening a debugger"
date: 2022-05-20 23:23:00 +0700
categories: ["Technique Reverse", "Part 02 · The Toolkit"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
Here's a comforting truth for beginners: a lot of the time you can tell what a program is doing without reading a single line of assembly. You just have to watch where it touches the system. Where it creates files, which registry keys it writes, which server it calls, what child processes it spawns. This is called behavioral analysis, and it's often the first dynamic step before you decide whether you need to sit down and debug in detail.

This lesson is the observation toolkit. None of it is hard to use, the hard part is knowing how to read the pile of events they spit out.

## Procmon, a diary of everything

Process Monitor (Procmon, from Sysinternals) records nearly every interaction between processes and the operating system in real time: file operations, registry, process creation/exit, basic network activity, and threads. Run it for a few seconds and you have tens of thousands of lines, so the real skill is in filtering.

The standard habit is to open Procmon, turn on capture, run the target program, then turn capture off right away so you don't drown. Filter by process first: `Process Name is <name>.exe then Include`. The whole sea of events shrinks to just what you need. Then filter by operation type with the buttons on the toolbar (file system, registry, network, process/thread), so if you want to see what files it writes, you only turn on file system. The columns worth looking at are Operation (e.g. `CreateFile`, `RegSetValue`, `WriteFile`), Path (which file or key), Result (`SUCCESS` or `NAME NOT FOUND`), and Detail.

A few patterns you can read right away without disassembling. A series of `RegSetValue` into `...\CurrentVersion\Run` means the program is installing persistence, that is, making itself run again after the machine boots. `CreateFile` then `WriteFile` into `%TEMP%` then `Process Create` of the file it just wrote is the classic sign of a dropper, dropping a payload and then running it. And `RegQueryValue` on keys like `...\VMware` or `...\VirtualBox` means it's checking whether it's running in a virtual machine (anti-VM, covered in Part 15).

Procmon doesn't tell you why, but it tells you what and in which order. That's already half the story.

## Process Hacker / System Informer, a microscope for processes

Process Hacker (the successor goes by the name System Informer) is a Task Manager edition for people doing RE. It lets you look inside a running process. The process tree shows who spawned whom, with color coding (services, .NET processes, packed...). The Memory tab shows the memory map, and importantly has a button to scan strings right in live memory. Many programs hide strings on disk but have to decrypt them into RAM at runtime, and this is where you catch them.

The Handles tab shows the files, registry keys, mutexes, and events the process has open. Mutexes are especially useful, since a lot of malware creates a mutex with a fixed name to avoid running twice, and that name becomes an IOC for identification. The Threads tab lets you view each thread's call stack and find the start point. Right-click a memory region or module and you can dump it to disk for static analysis, which is very handy when the code has been unpacked in memory.

When you suspect a program decrypts strings at runtime, opening Process Hacker and scanning memory strings is much faster than hunting for the decryption routine in a disassembler.

## Process Explorer, the slimmer version

Process Explorer is also from Sysinternals, lighter than Process Hacker, strong at the process tree, viewing the DLLs a process loaded, and quickly looking up who is holding a handle. If you only need an overview and parent-child relationships, it's enough. Process Hacker fits better when you need to dig into memory and handles.

## API Monitor, eavesdropping on API calls

Procmon only sees interactions at the operating system level. API Monitor gets closer to the code: it hooks and records Win32 API calls with the real parameters and return values. You pick the API groups you want to follow (file, registry, memory, crypto, network...), run the program, and then read things like `CreateFileW(L"C:\\Users\\...\\secret.dat", GENERIC_READ, ...)`, which gives you the full file name right away. You might also see `CryptEncrypt(...)` or `VirtualAlloc(..., PAGE_EXECUTE_READWRITE)`, which allocates memory that's both writable and executable, a common red flag when code is preparing to run a payload.

The strength is seeing parameters in a human-readable form. The weakness is that a lot of malware evades its hooks, or calls the Native API/syscalls directly to go around (mentioned in lesson 1.12). When API Monitor is suspiciously silent, that silence is itself a clue.

## Autoruns, inspecting persistence

Autoruns lists nearly every spot where something can auto-start on Windows: Run keys, scheduled tasks, services, drivers, Explorer plugins, and dozens of other places you wouldn't think of. After running a sample, comparing Autoruns before and after shows right away what it planted to survive the next boot. There's an option to hide entries signed by Microsoft to cut down the noise.

## Wireshark, looking at network traffic

When a program talks to the outside, Wireshark captures every packet. You see which domain it resolves (DNS), which IP and port it connects to, and if it's not encrypted, even the contents. For malware, this is how you find the command-and-control (C2) server and understand the communication protocol. Remember to set up the lab network correctly: you usually run in a simulated network environment (INetSim/FakeNet) so the sample thinks it reached the internet while the packets go nowhere, see lesson 0.3.

## On Linux: strace and ltrace

The Linux world is tidier, and two commands are enough for most jobs. `strace ./program` records every system call (`open`, `read`, `write`, `connect`, `execve`), the equivalent of Procmon at the syscall level. `ltrace ./program` records calls to library functions (libc...), close to API Monitor, so you see `strcmp`, `malloc`, `fopen` with their parameters right away.

For example, running `strace` on a license-checking program sometimes straight out reveals that it `open`s the file `/etc/mylicense` or `connect`s to an IP, and you understand the mechanism without opening a disassembler.

## Putting it together into a picture

No single tool gives you the full answer, but added together they do. Procmon answers which files and registry it touches. Process Hacker answers what it's hiding in memory, and which mutexes and handles it holds. API Monitor answers which APIs it calls and with what parameters. Autoruns answers where it plants itself to live long, and Wireshark answers who it talks to.

Run the sample once with this whole set turned on, and you have a behavior profile before touching a single line of assembly. From that profile you decide which spots are worth sitting down and debugging deeply. That's exactly the spirit of triage, static, dynamic in lesson 0.4, the only difference being that the dynamic here is done by observation rather than by a debugger.

And a reminder to be sure: everything in this lesson, when the target is real malware, has to run in an isolated VM per [Lesson 0.3](/posts/re-0-3-set-up-safe-lab-before-touching/). Turning on Procmon doesn't make you any safer, the program still really runs.

## Lab

Here is a way to build a behavior profile with monitoring tools only, no debugger. The target is `watchme.c`, a harmless program I wrote, so it is fine to run on a normal machine. When you apply the same workflow to real malware, do it in an isolated VM as described in [Lesson 0.3](/posts/re-0-3-set-up-safe-lab-before-touching/).

On Windows with an MSVC Developer Command Prompt, build it with:

```
cl /nologo watchme.c advapi32.lib
```

With MinGW:

```
gcc watchme.c -o watchme.exe -ladvapi32
```

On Linux:

```
gcc watchme.c -o watchme
```

The program reads an environment variable, creates and writes a file called `watchme_marker.txt` in the TEMP directory, reads a registry value (Windows only), and then sleeps for 3 seconds.

Start Procmon, turn on capture, run `watchme.exe`, then turn capture off. Add the filter `Process Name is watchme.exe then Include` and count how many events remain compared with the unfiltered view. Next, enable only the File System button and find the `CreateFile` then `WriteFile` pair on `watchme_marker.txt`, noting the full Path and the Result column. Switch to Registry only and find the `RegOpenKey` and `RegQueryValue` calls on the `...\CurrentVersion` key and the `ProductName` value. While the program is still sleeping, open Process Hacker, find the `watchme.exe` process, go to the Memory tab, scan the memory strings and look for `hello from watchme`. On Linux, run the following and look for the `openat` line that opens the marker file and the `write` that stores its content, then compare it with what Procmon showed on Windows:

```
strace -f -e trace=open,openat,read,write ./watchme
```

Two questions to think about. If `watchme` wrote the file and then ran it, which malware technique would that Procmon pattern resemble? And why is filtering by process name almost always the first step?

<div class="lab-box">
<div class="lab-head"><b>LAB 2.8</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/2.8/src/watchme.c" download><i class="fa-solid fa-file-code"></i>src/watchme.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Without a filter, a few seconds of `watchme.exe` can produce anywhere from a few thousand to tens of thousands of lines, mostly the DLL loader and the CRT touching all sorts of things at startup. After adding `Process Name is watchme.exe` the count drops to a few hundred. That is why filtering by process name always comes first: it cuts out the noise from other processes and keeps only your target.

With File System enabled on its own, you see a sequence along these lines:

```
watchme.exe  CreateFile   C:\Users\<you>\AppData\Local\Temp\watchme_marker.txt   SUCCESS   Desired Access: Generic Write, Disposition: Create
watchme.exe  WriteFile    C:\Users\<you>\AppData\Local\Temp\watchme_marker.txt   SUCCESS   Length: 20
watchme.exe  CloseFile    C:\Users\<you>\AppData\Local\Temp\watchme_marker.txt   SUCCESS
```

The Detail column of `CreateFile` shows Desired Access as Generic Write and Disposition as Create, which matches `CREATE_ALWAYS | GENERIC_WRITE` in the source. `WriteFile` has Length 20, exactly the length of the string `hello from watchme\r\n`. In Procmon, `CreateFile` is the generic operation for both opening and creating files and the Disposition tells them apart, so don't assume it always means a new file.

With Registry enabled on its own:

```
watchme.exe  RegOpenKey    HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion   SUCCESS
watchme.exe  RegQueryValue HKLM\SOFTWARE\...\CurrentVersion\ProductName        SUCCESS   Type: REG_SZ, Length: ..., Data: Windows 1x ...
```

The Data column of `RegQueryValue` shows the value that was read. This is the Windows ProductName, the same string the program prints. The operation is read-only, there is no `RegSetValue`, so the program changes nothing in the registry. If you saw an unfamiliar program do a `RegSetValue` into `...\CurrentVersion\Run`, that would be persistence, which is a very different thing from a plain read.

For the memory strings, while the program sleeps, open Process Hacker, double-click `watchme.exe`, go to the Memory tab and press the string search button (or right-click a Private region and choose to scan strings). Filter the results by `hello` and you see `hello from watchme` in memory even though it is also on disk. For a program that decrypts its strings at runtime, this is how you catch the decrypted strings that never exist on disk.

On Linux, `strace` shows lines like these:

```
openat(AT_FDCWD, "/tmp/watchme_marker.txt", O_WRONLY|O_CREAT|O_TRUNC, 0666) = 3
write(3, "hello from watchme\n", 19)   = 19
```

These are the exact system calls that open and write the file, with the `O_CREAT|O_TRUNC` flags equivalent to `CREATE_ALWAYS` on Windows. It is the Linux version of the same behavior Procmon captured, only at the rawer syscall level.

As for the questions: if `watchme` wrote the file and then executed it, the pattern of `CreateFile` and `WriteFile` into TEMP followed by a `Process Create` of the file it just wrote is the classic sign of a dropper, a component that drops a payload to disk and runs it. Seeing that chain in Procmon is a red flag even before you know what the payload contains. And filtering by process is the first step because Procmon records every process on the machine at once. Without a filter, your target's events are buried in tens of thousands of lines from system processes and are nearly unreadable, while a process name filter narrows things to exactly what you want to see.

</details>

## Key takeaways
Behavioral analysis tells you what a program does, often without reading assembly. In Procmon, filter by process name first, then by operation type (file/registry/network). Process Hacker lets you scan strings in live memory, view handles and mutexes, and dump unpacked regions.

API Monitor shows API calls with human-readable parameters, and unusual silence is also a clue. Use Autoruns to inspect persistence and Wireshark to inspect the network. On Linux, strace covers syscalls and ltrace covers library functions. Real malware always goes in an isolated VM.
