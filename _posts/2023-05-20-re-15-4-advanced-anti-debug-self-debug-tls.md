---
title: "Lesson 15.4: Advanced anti-debug, self-debug and TLS callbacks"
image:
  path: /assets/img/covers/re-15-4-advanced-anti-debug-self-debug-tls.webp
  alt: "Lesson 15.4: Advanced anti-debug, self-debug and TLS callbacks"
date: 2023-05-20 20:16:00 +0700
categories: ["Technique Reverse", "Part 15 · Anti-Reversing and Bypasses"]
tags: [reverse-engineering, anti-debug]
render_with_liquid: false
---
The previous three lessons covered checks you run into midway through a program, such as asking an API, reading the PEB, measuring time. This one covers a nastier group. These checks either don't give you time to attach, or take the debugger's seat so you can't get in. Beginners often get stuck here with "the program exits right as it starts and I have no idea why".

## Self-debugging: taking the debugger's seat

Windows has a simple rule that this whole family of techniques relies on, which is that a process can only have one debugger attached at a time. If the program sets up a debugger for itself, that slot is already taken, and your x64dbg will fail to attach.

There are two common variants. In the first, the program creates a child process and lets the child debug the parent. It calls `CreateProcess` on a copy of itself with a flag, and then the child calls `DebugActiveProcess` on the parent. From then on the parent already has a debugger (its own child), and you can't squeeze in. The second variant self-debugs through a separate thread, which is less common but works the same way.

You can recognize it when reading statically. You see `CreateProcess` creating its own path, together with `DebugActiveProcess`, `WaitForDebugEvent`, `ContinueDebugEvent`. A parent-child pair like this means a self-debugger.

Don't try to attach to a process that's already taken. Block the child-creation step instead (put a breakpoint at `CreateProcessW`, or patch it so it doesn't create the child), or analyze the logic in the child process to understand what it does and then neutralize the whole mechanism.

## Parent process check

A cheap but effective kind is one where the program asks itself who spawned it. When you run a file normally from Explorer, the parent is `explorer.exe`. When you run it from inside x64dbg, the parent is `x64dbg.exe`. From cmd it's `cmd.exe`.

The program gets the parent PID (through `NtQueryInformationProcess` with `ProcessBasicInformation`, then looks up the parent process name through `CreateToolhelp32Snapshot`) and compares it against a list of well-known debugger names. If it matches, it knows it's being watched.

You spot it by seeing name strings like "x64dbg", "ollydbg", "ida", "windbg" in the binary, along with code that enumerates processes. To get past it, run it from a "clean" parent, patch the name comparison, or use a plugin that hides the process name.

## Debug object

When a debugger attaches, the kernel creates a debug object tied to the debugged process. The program can ask about it through `NtQueryInformationProcess` with the information class `ProcessDebugObjectHandle` (value 0x1E), and if it returns a non-null handle, a debug object exists, meaning it's being debugged. This is one of the hardest checks to fake because it asks the kernel directly about the real state.

In practice I use ScyllaHide/TitanHide (lesson 15.9), which hook exactly this spot to give a fake answer. By hand, set a breakpoint at `NtQueryInformationProcess`, and when `ProcessInformationClass == 0x1E` change the return value to 0.

## Thread hiding, in more depth

Lesson 15.1 mentioned `NtSetInformationThread(ThreadHideFromDebugger)`. Here's what it does in more detail. When a thread gets the `ThreadHideFromDebugger` flag (value 0x11), the kernel stops sending that thread's debug events to the debugger. Breakpoints and exceptions in that thread are no longer reported to the debugger, and the program runs right past you.

Usually the program sets this flag for the main thread and only then runs the sensitive part. The sign is a call to `NtSetInformationThread` where the information class parameter is 0x11 and the thread handle is `(HANDLE)-2` (the pseudo-handle of the current thread). To get past it, patch that call into a no-op, or let ScyllaHide block it.

## TLS callbacks: running before main

Beginners get trapped by this one the most. As lesson 1.12 said, TLS callbacks are functions the PE loader calls before the entry point runs. The loader maps the image, calls the TLS callbacks, and only then jumps to the entry point.

Anti-debug authors take advantage of this by putting the check right in the TLS callback. When you open the file in a debugger and hit run, the debugger usually stops first at the entry point (or the system breakpoint). But the TLS callback has already finished running before that. So by the time you see anything, the program may already have detected the debugger and decided to exit, or quietly switched to another branch.

The flow:

```
PE loader maps the image into memory
   |
   v
calls TLS callback 1  <-- anti-debug lives here, runs BEFORE you can look
   |
   v
calls TLS callback 2 (if any)
   |
   v
jumps to the entry point  <-- the debugger usually only stops here, too late
   |
   v
the author's main()
```

To handle it, go to Options > Preferences > Events in x64dbg and turn on the option to stop at TLS Callbacks (and System Breakpoint, Entry Breakpoint). Then the debugger stops right when the first TLS callback is about to run, and you have time to set breakpoints and look. You can also find the TLS callbacks statically first. Open the file in PE-bear or CFF Explorer, look at the TLS Directory, and get the callback addresses, then set breakpoints there in advance in IDA/Ghidra. If the callback only does one thing, check and exit, patch it to return early.

A rule of thumb is that if a program "dies right after starting" in a debugger before the entry point is even reached, suspect a TLS callback right away.

## Looking at a TLS callback

A TLS callback has the fixed signature `VOID NTAPI cb(PVOID DllHandle, DWORD Reason, PVOID Reserved)`. In a binary it usually looks like a small function, called by the PE loader with `Reason == DLL_PROCESS_ATTACH` (value 1) at startup:

```asm
tls_callback:
    cmp  edx, 1            ; Reason == DLL_PROCESS_ATTACH ?
    jne  short done        ; only runs on process attach
    ; read PEB.BeingDebugged via gs:[0x60]
    mov  rax, gs:[60h]
    movzx eax, byte ptr [rax+2]
    test eax, eax
    je   short done        ; not debugged, return
    ; being debugged: exit or branch to a fake path
    xor  ecx, ecx
    call ExitProcess
done:
    ret
```

You can read it right away. This callback checks `BeingDebugged`, and if it sees a debugger it calls `ExitProcess`. Since it runs before main, you have to catch it from the TLS callback breakpoint, you can't wait until main.

## Lab

The goal is to see for yourself why a check placed in a TLS callback runs before `main`, and how to catch it with x64dbg. You need Windows (or a Windows VM, see Lesson 0.3), x64dbg, PE-bear or CFF Explorer, and a compiler, either MSVC (`cl`) or MinGW-w64 (`gcc`). The program is `tls_antidebug.c`, and you build it with one of these:

```
cl /GS- tls_antidebug.c                         :: MSVC
gcc tls_antidebug.c -o tls_antidebug.exe        :: MinGW
```

First run `tls_antidebug.exe` directly, with no debugger, and observe that it prints `main: running normally`. Then open it in PE-bear, find the TLS Directory and write down the RVA of the callback, which is where the check lives. Next open it in x64dbg with the default options and press Run. Watch whether the program detects the debugger (a MessageBox and then exit) or stops somewhere, and notice whether you ever see `main` run.

Now go to Options > Preferences > Events and turn on TLS Callbacks, then restart the debug session. This time the debugger stops just as the TLS callback is about to run, before the entry point. Work your way to the code that reads `gs:[0x60]` and checks the `BeingDebugged` byte, and set a breakpoint there. Get past it in one of three ways, namely set `BeingDebugged` to 0 in memory while stopped, patch the jump so it always goes on to `main`, or use the ScyllaHide plugin (Lesson 15.9). Confirm that after getting past it, the program runs to `main` and prints its message normally.

Three questions to reflect on. Why is enabling the TLS Callbacks breakpoint more important than just setting a breakpoint at main? If the program has several TLS callbacks, in what order are they called? And why might fixing `BeingDebugged` just once not be enough if the callback runs again?

<div class="lab-box">
<div class="lab-head"><b>LAB 15.4</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/15.4/src/tls_antidebug.c" download><i class="fa-solid fa-file-code"></i>src/tls_antidebug.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

The x64dbg steps below are the standard procedure for this tool and need a Windows machine. The source `tls_antidebug.c` follows how MSVC and MinGW register a TLS callback in the `.CRT$XLB` section.

Run directly, the TLS callback checks `BeingDebugged`, sees 0 and does nothing, so the program enters `main` and prints `main: running normally`.

To find the TLS Directory, look in PE-bear's Data Directories, where the TLS entry points to the `IMAGE_TLS_DIRECTORY`. Its `AddressOfCallBacks` field points to a null-terminated array of function pointers, and each element is a TLS callback. Note the RVA so you can set a breakpoint in x64dbg.

With the default configuration, x64dbg stops at the system breakpoint and then at the entry breakpoint. But the TLS callback runs before the entry point, so if you just press Run from the system breakpoint, the callback runs and detects the debugger (a MessageBox saying "Debugger detected in TLS callback", then `ExitProcess`). You never see `main`. This is the "it dies when I run it in a debugger" problem.

After ticking **TLS Callbacks** under Options > Preferences > Events and restarting, x64dbg stops right before the callback runs. You are standing in the callback, before even the entry point. Inside it, look for:

```asm
mov   rax, gs:[60h]        ; get the PEB
movzx eax, byte ptr [rax+2] ; BeingDebugged
test  eax, eax
jne   <exit branch>
```

Set a breakpoint on the `test` or `jne` instruction. There are three ways past it. You can edit the variable. When stopped at `test eax, eax`, set `eax = 0` (or edit the PEB+2 byte in the dump to 0 directly), and the exit branch won't run. You can patch the branch. Change `jne` to `nop` (or to a `jmp` toward the surviving path) and save the patch (Ctrl+P > Patch file). Or you can use ScyllaHide. Enable the plugin and it hides `BeingDebugged` for good, so the callback sees 0 naturally. That's the cleanest and most durable way, see Lesson 15.9. After getting past, keep running and the program reaches `main` and prints `main: running normally`.

On the questions, the TLS breakpoint matters more than one at main because the callback runs before main. A breakpoint at main is already too late, since the check has had time to kill the program before that. With several TLS callbacks, the PE loader calls them in the order they appear in the `AddressOfCallBacks` array, from top to bottom, until it meets a null pointer. And fixing it once may not be enough because if the callback runs again (for example with `DLL_THREAD_ATTACH` when a new thread is created) or several callbacks perform the same check, you have to handle every occurrence. ScyllaHide handles it more thoroughly because it hides the flag at the source instead of patching each point.

</details>

## Common pitfalls

If the entry point hasn't been reached and the program has already exited, it's almost certainly a TLS callback, so don't blame a broken debugger. A failed attach isn't always an error either, since self-debugging may have taken the slot. And if you disable one check (for example BeingDebugged) and it still dies, remember other checks run earlier, especially in TLS.

## Key takeaways
A process only has one debugger, so self-debugging takes the slot and you can't attach. Block it at the child-creation step. A parent process check compares the parent's name against a list of debuggers, so patch it or run from a clean parent.

`ProcessDebugObjectHandle` (0x1E) asks the kernel about the debug object and is very hard to fake, so use ScyllaHide. `ThreadHideFromDebugger` (0x11) makes the kernel stop sending debug events, so patch it to a no-op or use ScyllaHide.

TLS callbacks run before the entry point. Turn on stopping at TLS Callbacks in x64dbg and find the TLS Directory in PE-bear. If the program dies before main, suspect TLS right away.
