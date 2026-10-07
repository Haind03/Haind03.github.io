---
title: "Lesson 17.6: LD_PRELOAD, ptrace and DYLD_INSERT_LIBRARIES"
date: 2023-08-08 14:54:00 +0700
categories: ["Technique Reverse", "Part 17 · Patching, Hooking, Injection"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
On Windows you hook with Detours, IAT or inline hooks (lesson [17.3](/posts/re-17-3-hooking-windows-iat-hooks-inline-hooks/)). On Linux and macOS there's a much cleaner way, built into the OS loader itself: you tell it to load your library before the standard library, and your function overrides the libc function. No overwriting bytes, no code cave, just an environment variable. This lesson uses it to expose the password of a crackme, and also covers ptrace, the mechanism behind every Linux debugger.

## LD_PRELOAD: cutting your library to the front of the line

When a Linux program calls `strcmp`, that call is resolved at runtime through the dynamic linker. The linker looks for the function in the list of libraries in order, and the first function whose name matches wins. `LD_PRELOAD` inserts a library of yours at the front of that list. If your library also defines `strcmp`, your version gets called instead of libc's.

This is a legitimate glibc feature, used for debugging, profiling, hot patching, and for RE folks it's for hooking without touching the binary. Because it works at the library call boundary, it can only intercept functions called through the PLT (functions from dynamic libraries), not static or inlined ones. But `strcmp`, `malloc`, `fopen`, `getenv` can all be caught.

### Writing a hook

An important trick: your hook usually still wants to call the real function (so the program runs normally and you just step in to observe). Get the real function pointer with `dlsym(RTLD_NEXT, "strcmp")`, meaning "find the next `strcmp` in the chain, skipping mine".

```c
#define _GNU_SOURCE
#include <stdio.h>
#include <dlfcn.h>

static int (*real_strcmp)(const char *, const char *) = NULL;

int strcmp(const char *a, const char *b) {
    if (!real_strcmp)
        real_strcmp = dlsym(RTLD_NEXT, "strcmp");
    fprintf(stderr, "[hook] strcmp(\"%s\", \"%s\")\n", a, b);
    return real_strcmp(a, b);   // call the real function, the program runs as usual
}
```

Build it into a shared object and load it:

```sh
gcc -shared -fPIC -o hook.so hook.c -ldl
LD_PRELOAD=./hook.so ./crackme
```

Every time the crackme compares strings, the hook prints both operands. If the crackme uses `strcmp(input, secret)` then the right password shows up right on screen, no need to open IDA. The lab below does exactly this, with real run results.

Why log to `stderr` and not `stdout`: so the hook's output doesn't mix into the program's output, which makes filtering easier.

## ptrace: the foundation of every Linux debugger

`gdb`, `strace`, `ltrace` all stand on a single syscall: `ptrace`. A process calls `ptrace(PTRACE_ATTACH, pid, ...)` to attach to another process, then reads/writes registers and memory, sets breakpoints, steps. Understanding this explains two things.

First, `strace ./prog` shows you every syscall the program makes (open, read, write, connect), and `ltrace ./prog` shows every library call (like LD_PRELOAD but seeing everything). These two commands are the fastest dynamic triage on Linux, run them before opening a disassembler.

Second, ptrace is where Linux anti-debug likes to set traps. A process can only be attached to by one tracer at a time. So the classic anti-debug trick is the program calling `ptrace(PTRACE_TRACEME, 0, 0, 0)` on itself: if it succeeds, it knows nobody is debugging it; if gdb is already attached, this call fails (returns -1), and the program knows it's being watched, then exits or takes a fake branch.

```c
if (ptrace(PTRACE_TRACEME, 0, 0, 0) == -1) {
    // a debugger is already attached -> exit or misbehave
    exit(1);
}
```

How to recognize it when reversing: look for the `ptrace` call (syscall number 101 on x86-64) right at the start of the program. How to get past it: use LD_PRELOAD to hook `ptrace` to return 0, or patch the branch, or run under a tool that doesn't use ptrace. A nice full circle: the LD_PRELOAD from the section above is itself the way to break the ptrace anti-debug.

```c
// hook that disables the ptrace anti-debug: always say "nobody is tracing"
long ptrace(int request, ...) { return 0; }
```

## DYLD_INSERT_LIBRARIES: the macOS version

macOS has an equivalent mechanism called `DYLD_INSERT_LIBRARIES` (dyld is macOS's dynamic linker). The idea is the same: insert a dylib that loads first to override functions. The overriding function has to be marked so dyld knows to replace it (interpose), through an `__interpose` section instead of just defining the same name.

The big difference is System Integrity Protection (SIP): modern macOS blocks `DYLD_INSERT_LIBRARIES` for system processes and binaries with hardened runtime, so it only works on your own binaries or binaries that aren't hardened. That's why on macOS people often switch to Frida (lesson [17.2](/posts/re-17-2-frida-full-inspecting-modifying-program-while/)) for convenience.

## When to use which

If you want a quick look at which files, network connections or syscalls a Linux program touches, use `strace` or `ltrace`, with nothing to write. If you want to hook a specific library function to read or change parameters, on your own binary or a lab sample, LD_PRELOAD is neat and clean. If you hit a ptrace anti-debug, LD_PRELOAD hook `ptrace` to return 0. On macOS, or when you need much more flexibility, or the same script across platforms, use Frida.

LD_PRELOAD is not a cure-all. It can't touch static functions, inlined functions, or direct syscalls that don't go through libc. Then go back to the debugger or Frida.

## Lab

The folder `labs/17.6/` has a crackme that calls `strcmp` to compare the password, and a `hook.c` library that overrides `strcmp` to log. The task: build both, run the crackme with `LD_PRELOAD` and read the correct password falling out of the log, without disassembling. Then try writing a `ptrace` hook yourself to understand how to disable the anti-debug.

The reference result (actually run with gcc on Linux) is in `labs/17.6/solution.md`.

## Key takeaways
LD_PRELOAD loads your library before libc, so your same-named function wins, and it only intercepts functions called through the PLT (dynamic libraries). In a hook, get the real function with `dlsym(RTLD_NEXT, "name")` and call it back so the program runs normally. Hooking `strcmp` exposes the password right away if the crackme compares strings with strcmp.

ptrace is the base of gdb/strace/ltrace, and a process can only have one tracer attached. Linux anti-debug often uses `ptrace(PTRACE_TRACEME)`, where failure means it's being debugged, and you get past it with an LD_PRELOAD hook of ptrace returning 0. macOS has `DYLD_INSERT_LIBRARIES` but SIP restricts it, so people usually switch to Frida.
