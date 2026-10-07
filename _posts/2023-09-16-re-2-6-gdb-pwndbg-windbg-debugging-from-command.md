---
title: "Lesson 2.6: GDB, pwndbg and WinDbg, debugging from the command line"
date: 2023-09-16 20:38:00 +0700
categories: ["Technique Reverse", "Part 02 · The Toolkit"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
x64dbg in the last lesson is a nice GUI where you just click. But when you move to Linux, or need to debug the Windows kernel, or want to script a whole debugging session, you'll come back to the command line. GDB dominates the Linux world, WinDbg dominates the deepest corners of Windows. This lesson won't turn you into an expert in those two tools, it just gives you enough to sit down and get work done.

## Why still use a CLI debugger in the age of GUIs

A fair question. On a Linux server or inside a container there's usually no display, just a terminal. GDB can be scripted: write a command file, run it in bulk, extract values automatically, which a GUI doesn't handle neatly. And WinDbg is nearly the only tool for debugging the Windows kernel and for using Time Travel Debugging, which x64dbg doesn't have.

Don't see the CLI as a step backward. It's a different tool for a different problem.

## GDB, the skeleton

Bare GDB is unfriendly, but the core set of commands is very small. Starting up:

```
gdb ./program            # load the program
gdb -p 1234              # attach to the running process with PID 1234
```

The first thing to do, because GDB defaults to hard-to-read AT&T syntax:

```
set disassembly-flavor intel
```

Now disassembly shows in Intel syntax, like IDA and x64dbg, which saves a headache.

### Running and stopping

| Command | What it does |
|---|---|
| `b main` / `b *0x401136` | Set a breakpoint at a function or address (with `*` when it's an address) |
| `r` | Run, start from the beginning |
| `c` | Continue, keep running after a stop |
| `si` / `ni` | Step into / step over one instruction (s=instruction) |
| `finish` | Run until the current function returns |
| `info breakpoints` | List breakpoints |
| `d 1` | Delete breakpoint number 1 |

Note that `si`/`ni` step by one assembly instruction. If you type `s`/`n` without the `i`, GDB steps by one source line (only useful when there are debug symbols). People doing RE usually use `si`/`ni`.

### Viewing data

This is where GDB is strong. The `x` (examine) command reads memory in whatever format you want:

```
info registers          # view all registers
p $rax                  # print the value of rax
p/x $rax                # print in hex
x/20i $pc               # view 20 instructions (i) starting at the instruction pointer
x/16xg $rsp             # view 16 8-byte values (g=giant) in hex at the top of the stack
x/s 0x404040            # read a string (s) at an address
x/4xb $rdi              # view 4 bytes (b) in hex at the address rdi points to
```

The `x/` syntax reads as: the count, then the format (x hex, d decimal, i instruction, s string), then the size (b byte, h 2 bytes, w 4 bytes, g 8 bytes). Remember this formula and you can read anything in memory.

### Editing to change the flow

```
set $rax = 1            # assign a register
set {int}0x404040 = 5   # write the number 5 (as an int) to an address
```

Directly assigning a flag register or a return value is a quick way to force the program down the branch you want, for example forcing a check function to return 1.

### TUI mode

Type `Ctrl+X` then `A`, or run `gdb -tui`, and you get a split-pane interface showing source or disassembly alongside the command line. Much easier on the eyes than bare GDB.

## pwndbg and GEF, turning GDB into a tool for humans

Bare GDB doesn't show you the stack, heap, and registers right when it stops. Two extensions patch that hole: pwndbg and GEF. Install one of them (not both at once), and from then on every time GDB stops it prints the full context: registers, a few instructions around the pointer, the stack, the flags.

More useful commands:

| Command | What it does |
|---|---|
| `vmmap` | Memory map: which region has which addresses, and RWX permissions |
| `telescope $rsp` (pwndbg) | View the stack and auto-interpret where pointers point |
| `context` (pwndbg) | Reprint the whole current context |
| `heap` / `bins` | Inspect heap structures (handy for pwn) |

For people learning RE on Linux, installing pwndbg is nearly mandatory. It turns GDB from hard to use into pleasant.

## WinDbg, when you need to go deep into Windows

WinDbg (you should use the new WinDbg, formerly called WinDbg Preview) is Microsoft's official debugger. It's harder than x64dbg but does things x64dbg can't. It can debug kernel-mode, meaning the Windows kernel and drivers, while x64dbg can only play in user-mode. It also has Time Travel Debugging (TTD), which records a whole run into a trace file, and then you can scrub back and forth freely, even run backwards in time to find where a value got changed. This is a life-changing feature when chasing a hard bug or tracing a value back to its source.

A concept to grasp: WinDbg distinguishes user-mode (debugging one process) from kernel-mode (debugging the whole kernel, usually through two machines connected together or a virtual machine). Beginners start in user-mode.

The basic command set has a command-typing style like GDB but different notation:

| Command | What it does |
|---|---|
| `g` | Go, keep running (like GDB's `c`) |
| `p` / `t` | Step over / step into (p=step, t=trace) |
| `bp kernel32!CreateFileW` | Breakpoint by module!function name |
| `u rip` | Unassemble, disassemble at rip |
| `r` | View/edit registers (`r rax=1`) |
| `dd` / `dq` / `da` / `du` | Dump dword / qword / ASCII string / Unicode string |
| `k` | Call stack (backtrace) |
| `!peb` | Print the PEB structure, handy for anti-debug |
| `lm` | List loaded modules |

WinDbg's `module!function` syntax is very powerful: set a breakpoint by API function name without knowing the address, and WinDbg looks it up through symbols. Remember to configure Microsoft's symbol server to get full function names.

## CLI or GUI, which to choose

There's no general answer, so choose by the job. For learning basic RE on Windows and taking apart crackmes, just use x64dbg, an intuitive GUI that gets you to work fast. For Linux, CTF pwn, and ELF binaries, use GDB plus pwndbg. For debugging the Windows kernel or drivers, or when you need to rewind time, use WinDbg plus TTD. And when you need to automate a debugging session and extract lots of values, write a GDB script or WinDbg script.

People who've been at it a long time use all three and aren't loyal to any. Tools are just tools.

## Lab

The source and instructions are at [labs/2.6/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/2.6). In short: compile a small C program that has a password check function, load it into GDB + pwndbg, set a breakpoint at the compare function, read the arguments with `info registers` and `x`, then modify a register value to force the program to accept a wrong password. When you finish you'll see the static-then-dynamic rhythm of [Lesson 0.4](/posts/re-0-4-reverse-engineering-workflow-not-get-lost/) right in the command line. The full writeup is in [solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/2.6/solution.md), do it yourself before opening it.

## Key takeaways
In GDB, remember `set disassembly-flavor intel` right at the start for readability. The core command set is `b`, `r`, `c`, `si`/`ni`, `finish`, `info registers`, `x/`, and `set`. The formula is `x/<count><format><size>`, so `x/16xg $rsp` is 16 8-byte hex values at the stack.

Install pwndbg (or GEF) so GDB shows context automatically, and `vmmap` and `telescope` are well worth using. WinDbg is for kernel-mode and Time Travel Debugging, two things x64dbg doesn't have, and its breakpoints go by `module!function` once you turn on Microsoft's symbol server. Choose the tool by the problem: x64dbg for Windows user-mode, GDB for Linux, WinDbg for kernel/TTD.
