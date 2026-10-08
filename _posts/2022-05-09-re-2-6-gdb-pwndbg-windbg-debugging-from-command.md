---
title: "Lesson 2.6: GDB, pwndbg and WinDbg"
image:
  path: /assets/img/covers/re-2-6-gdb-pwndbg-windbg-debugging-from-command.webp
  alt: "Lesson 2.6: GDB, pwndbg and WinDbg"
date: 2022-02-20 18:56:00 +0700
categories: ["Reverse Engineering", "Part 02 · The Toolkit"]
tags: [reverse-engineering, tools]
render_with_liquid: false
---
x64dbg in the last lesson is a GUI where you just click. But when you move to Linux, or need to debug the Windows kernel, or want to script a whole debugging session, you go back to the command line. GDB is the standard on Linux, WinDbg on the deep end of Windows. This lesson won't make you an expert in either, it just gives you enough to sit down and get work done.

![GDB session flow](/assets/img/re/re-2-6-gdb-pwndbg-windbg-debugging-from-command.svg)
_A typical GDB session from loading the program to inspecting memory._

## Why use a CLI debugger at all

On a Linux server or inside a container there's usually no display, just a terminal. GDB can be scripted, so you write a command file, run it in bulk, and extract values automatically, which a GUI doesn't handle well. And WinDbg is nearly the only tool for debugging the Windows kernel and for Time Travel Debugging, which x64dbg doesn't have.

The CLI isn't a step backward. It's a different tool for a different problem.

## GDB basics

Bare GDB is unfriendly, but the core set of commands is small. Starting up:

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

`si`/`ni` step by one assembly instruction. If you type `s`/`n` without the `i`, GDB steps by one source line, which only helps when there are debug symbols. For RE I use `si`/`ni`.

### Viewing data

The `x` (examine) command reads memory in whatever format you want:

```
info registers          # view all registers
p $rax                  # print the value of rax
p/x $rax                # print in hex
x/20i $pc               # view 20 instructions (i) starting at the instruction pointer
x/16xg $rsp             # view 16 8-byte values (g=giant) in hex at the top of the stack
x/s 0x404040            # read a string (s) at an address
x/4xb $rdi              # view 4 bytes (b) in hex at the address rdi points to
```

The `x/` syntax reads as the count, then the format (x hex, d decimal, i instruction, s string), then the size (b byte, h 2 bytes, w 4 bytes, g 8 bytes). Remember that and you can read anything in memory.

### Editing to change the flow

```
set $rax = 1            # assign a register
set {int}0x404040 = 5   # write the number 5 (as an int) to an address
```

Assigning a flag register or a return value directly is a quick way to force the program down the branch you want, for example making a check function return 1.

### TUI mode

Type `Ctrl+X` then `A`, or run `gdb -tui`, and you get a split-pane interface showing source or disassembly alongside the command line. Easier on the eyes than bare GDB.

## pwndbg and GEF

Bare GDB doesn't show you the stack, heap and registers when it stops. Two extensions fix that, pwndbg and GEF. Install one of them (not both), and from then on every time GDB stops it prints the full context, which is registers, a few instructions around the pointer, the stack, the flags.

More useful commands:

| Command | What it does |
|---|---|
| `vmmap` | Memory map: which region has which addresses, and RWX permissions |
| `telescope $rsp` (pwndbg) | View the stack and auto-interpret where pointers point |
| `context` (pwndbg) | Reprint the whole current context |
| `heap` / `bins` | Inspect heap structures (handy for pwn) |

If you learn RE on Linux, I'd say install pwndbg. It makes GDB much nicer to use.

## WinDbg

WinDbg (use the new WinDbg, formerly called WinDbg Preview) is Microsoft's official debugger. It's harder than x64dbg but does things x64dbg can't. It can debug kernel-mode, meaning the Windows kernel and drivers, while x64dbg stays in user-mode. It also has Time Travel Debugging (TTD), which records a whole run into a trace file. Then you can move back and forth freely, even run backwards to find where a value got changed. That's very handy when chasing a hard bug or tracing a value back to its source.

WinDbg separates user-mode (debugging one process) from kernel-mode (debugging the whole kernel, usually through two connected machines or a virtual machine). Beginners start in user-mode.

The command style is like GDB but the notation is different:

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

The `module!function` syntax is handy, since you can set a breakpoint by API function name without knowing the address, and WinDbg looks it up through symbols. Remember to configure Microsoft's symbol server to get full function names.

## CLI or GUI

It depends on the job. For learning basic RE on Windows and taking apart crackmes, use x64dbg. For Linux, CTF pwn and ELF binaries, use GDB plus pwndbg. For the Windows kernel or drivers, or when you need to rewind time, use WinDbg plus TTD. When you need to automate a debugging session and extract lots of values, write a GDB script or WinDbg script.

People who've been at it a long time use all three. Tools are just tools.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 2.6</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/2.6.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/2.6/src/login.c" download><i class="fa-solid fa-download"></i>src/login.c</a>
</div>
</div>

The file `login.c` is a small, harmless C program with a password check function, and it runs fine on an ordinary Linux machine. The goal is to get used to the rhythm of setting breakpoints, reading arguments through registers, and changing state at runtime to alter the flow, all from the command line. You need Linux (or WSL), gcc, gdb, and ideally pwndbg installed.

Build it and try one run to see the behavior:

```
gcc -g -O0 -no-pie -o login login.c
./login
Enter password: abc
Wrong password.
```

The rules are simple. Don't open `login.c`, and don't guess the password by eye. Use only GDB. Load the program into GDB and set the Intel syntax with `set disassembly-flavor intel`. Set a breakpoint at the function `check_password`, run, type any password, and let the program stop at the start of the function. The function receives the string you typed, so work out which register holds the first parameter on Linux x86-64 and read it with the `x` command. Inside the function there's a call to `strcmp`. Set a breakpoint there, run to it, and read both arguments of `strcmp`. One of them is the correct password, so write it down. Then quit and run again, this time typing a wrong password, but use GDB to change the return value of `check_password` (which register holds it?) so the program still prints "Correct!". For an extra challenge, rebuild without `-no-pie`, watch the addresses change on each run (ASLR), and use `vmmap` to see the real base.

Some hints. For the first parameter on System V x86-64, see [Lesson 1.4](/posts/re-1-4-x86-x64-assembly-2-stack-frames/). To read a string at the address in a register, use `x/s $reg`. The return value is in `rax`, and to change it at the right moment, break where the function is about to `ret`, or use `finish` and then `set $rax=1` before `main` checks it. Try it yourself before opening the solution.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Try it yourself before reading. The correct password is `r3v3rs3_m3`, but what matters is how to find it without opening the source. Start with:

```
gcc -g -O0 -no-pie -o login login.c
gdb ./login
(gdb) set disassembly-flavor intel
```

### Tasks 2 and 3: breakpoint at check_password, reading the parameter

```
(gdb) b check_password
Breakpoint 1 at 0x401156
(gdb) r
Enter password: hello
Breakpoint 1, check_password (input=...) at login.c:...
```

On System V x86-64 the first parameter is in `rdi`. Read the string it points to:

```
(gdb) x/s $rdi
0x7fffffffe3a0: "hello"
```

That's the string we just typed, so `check_password` receives the string pointer in `rdi`.

### Task 4: reading both arguments of strcmp

The call is `strcmp(input, secret)`. When `strcmp` is called, the first argument is in `rdi` and the second in `rsi`.

```
(gdb) b strcmp
(gdb) c
Breakpoint 2, __strcmp_avx2 ()
(gdb) x/s $rdi
0x7fffffffe3a0: "hello"          <- what we typed
(gdb) x/s $rsi
0x402004:       "r3v3rs3_m3"     <- the correct password, exposed
```

The correct password is `r3v3rs3_m3`. No need to read the source, you only look at the second argument of `strcmp`. It's an old trick, since a comparison function almost always has the secret value right next to the user's input. If GDB stops inside libc's optimized strcmp (`__strcmp_avx2`) and it looks confusing, just read `rdi` and `rsi` as above, the two strings are still there.

Another way is to read the secret variable directly. Because the build has `-g`, you can print it:

```
(gdb) b check_password
(gdb) r
(gdb) p secret
$1 = 0x402004 "r3v3rs3_m3"
```

The `strcmp` argument trick still works on a stripped binary with no symbols, so it's the one I'd keep.

### Task 5: forcing a correct return despite a wrong input

Type a wrong password, then force `check_password` to return 1. The return value is in `rax`. Run to the end of the function body and change it before it returns to `main`:

```
(gdb) delete
(gdb) b check_password
(gdb) r
Enter password: totally_wrong
Breakpoint 1, check_password ...
(gdb) finish                 # run to the end of the function, stop right after return
Run till exit from ...
0x... in main ()
Value returned is $1 = 0
(gdb) set $rax = 1           # overwrite the return value
(gdb) c
Correct! Welcome.
```

The program prints "Correct!" even though we typed the wrong password, because `main` only looks at `rax`. This is runtime patching. You don't change the password, you change the result of the check.

### Task 6: ASLR

Rebuild without `-no-pie`:

```
gcc -g -O0 -o login_pie login.c
gdb ./login_pie
(gdb) b check_password
(gdb) r
(gdb) vmmap           # (pwndbg) see the real module base, it changes on each run
```

Run `r` several times and the real breakpoint address differs because of ASLR. The offset relative to the module base stays fixed, as [Lesson 1.2](/posts/re-1-2-process-memory-map-where-everything-happens/) said. GDB rebases breakpoints by function name on its own, so you rarely have to compute by hand. That's an advantage of setting breakpoints by name rather than by hard-coded address.

In summary, arguments are read in System V register order, `rdi, rsi, rdx, rcx, r8, r9`. The return value is in `rax` and can be changed at runtime to alter the flow. Comparison functions often leak the secret in the neighboring argument, and this needs no symbols. Breakpoints by function name handle ASLR better than hard-coded addresses.

</details>

## Key takeaways
In GDB, remember `set disassembly-flavor intel` right at the start. The core command set is `b`, `r`, `c`, `si`/`ni`, `finish`, `info registers`, `x/`, and `set`. The formula is `x/<count><format><size>`, so `x/16xg $rsp` is 16 8-byte hex values at the stack.

Install pwndbg (or GEF) so GDB shows context automatically, and use `vmmap` and `telescope`. WinDbg is for kernel-mode and Time Travel Debugging, two things x64dbg doesn't have, and its breakpoints go by `module!function` once you turn on Microsoft's symbol server. Pick the tool by the problem, x64dbg for Windows user-mode, GDB for Linux, WinDbg for kernel/TTD.
