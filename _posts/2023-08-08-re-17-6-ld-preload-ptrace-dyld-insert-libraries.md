---
title: "Lesson 17.6: LD_PRELOAD, ptrace and DYLD_INSERT_LIBRARIES"
image:
  path: /assets/img/covers/re-17-6-ld-preload-ptrace-dyld-insert-libraries.webp
  alt: "Lesson 17.6: LD_PRELOAD, ptrace and DYLD_INSERT_LIBRARIES"
date: 2023-08-08 14:54:00 +0700
categories: ["Technique Reverse", "Part 17 · Patching, Hooking, Injection"]
tags: [reverse-engineering, frida, hooking]
render_with_liquid: false
---
On Windows you hook with Detours, IAT or inline hooks (lesson [17.3](/posts/re-17-3-hooking-windows-iat-hooks-inline-hooks/)). On Linux and macOS there's a simpler way built into the OS loader: you tell it to load your library before the standard library, and your function overrides the libc function. No overwriting bytes, no code cave, just an environment variable. This lesson uses it to expose the password of a crackme, and also covers ptrace, the mechanism behind every Linux debugger.

## LD_PRELOAD

When a Linux program calls `strcmp`, that call is resolved at runtime through the dynamic linker. The linker looks for the function in the list of libraries in order, and the first function whose name matches wins. `LD_PRELOAD` inserts a library of yours at the front of that list. If your library also defines `strcmp`, your version gets called instead of libc's.

This is a normal glibc feature, used for debugging, profiling and hot patching. For RE it lets you hook without touching the binary. Because it works at the library call boundary, it can only intercept functions called through the PLT (functions from dynamic libraries), not static or inlined ones. But `strcmp`, `malloc`, `fopen`, `getenv` can all be caught.

### Writing a hook

Your hook usually still wants to call the real function (so the program runs normally and you just observe). Get the real function pointer with `dlsym(RTLD_NEXT, "strcmp")`, meaning "find the next `strcmp` in the chain, skipping mine".

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

Every time the crackme compares strings, the hook prints both operands. If the crackme uses `strcmp(input, secret)` then the right password shows up on screen, no need to open IDA. The lab below does this, with real run results.

I log to `stderr` and not `stdout` so the hook's output doesn't mix into the program's output, which makes filtering easier.

## ptrace

`gdb`, `strace`, `ltrace` all stand on a single syscall: `ptrace`. A process calls `ptrace(PTRACE_ATTACH, pid, ...)` to attach to another process, then reads/writes registers and memory, sets breakpoints, steps. This explains two things.

First, `strace ./prog` shows every syscall the program makes (open, read, write, connect), and `ltrace ./prog` shows every library call (like LD_PRELOAD but seeing everything). These two commands are the fastest dynamic triage on Linux, and I run them before opening a disassembler.

Second, ptrace is where Linux anti-debug likes to set traps. A process can only be attached to by one tracer at a time. So the classic anti-debug trick is the program calling `ptrace(PTRACE_TRACEME, 0, 0, 0)` on itself. If it succeeds, nobody is debugging it. If gdb is already attached, this call fails (returns -1), and the program knows it's being watched, then exits or takes a fake branch.

```c
if (ptrace(PTRACE_TRACEME, 0, 0, 0) == -1) {
    // a debugger is already attached -> exit or misbehave
    exit(1);
}
```

When reversing, look for the `ptrace` call (syscall number 101 on x86-64) right at the start of the program. To get past it, use LD_PRELOAD to hook `ptrace` to return 0, or patch the branch, or run under a tool that doesn't use ptrace. The LD_PRELOAD from the section above is also a way to break the ptrace anti-debug.

```c
// hook that disables the ptrace anti-debug: always say "nobody is tracing"
long ptrace(int request, ...) { return 0; }
```

## DYLD_INSERT_LIBRARIES: the macOS version

macOS has an equivalent mechanism called `DYLD_INSERT_LIBRARIES` (dyld is macOS's dynamic linker). The idea is the same: insert a dylib that loads first to override functions. The overriding function has to be marked so dyld knows to replace it (interpose), through an `__interpose` section instead of just defining the same name.

The big difference is System Integrity Protection (SIP). Modern macOS blocks `DYLD_INSERT_LIBRARIES` for system processes and binaries with hardened runtime, so it only works on your own binaries or binaries that aren't hardened. That's why on macOS people often switch to Frida (lesson [17.2](/posts/re-17-2-frida-full-inspecting-modifying-program-while/)).

## When to use which

If you want a quick look at which files, network connections or syscalls a Linux program touches, use `strace` or `ltrace`, with nothing to write. If you want to hook a specific library function to read or change parameters, on your own binary or a lab sample, LD_PRELOAD is simple and clean. If you hit a ptrace anti-debug, LD_PRELOAD hook `ptrace` to return 0. On macOS, or when you need more flexibility, or the same script across platforms, use Frida.

LD_PRELOAD can't touch static functions, inlined functions, or direct syscalls that don't go through libc. Then go back to the debugger or Frida.

## Lab

This lab runs on Linux (or WSL) and should only be used on the crackme provided here. There are two files. `crackme.c` is a small crackme that reads a password from the keyboard and compares it with `strcmp` against a secret built in memory, so no obvious literal shows up in the strings. `hook.c` is an LD_PRELOAD library that overrides `strcmp`, prints both operands to stderr and then calls the real `strcmp`. Build both:

```sh
gcc -O0 -no-pie -o crackme crackme.c
gcc -shared -fPIC -o hook.so hook.c -ldl
```

Run the crackme without the hook, type something random and see that it says "Nope.". Then run it again with the hook and read the correct password in the log, without opening IDA:

```sh
echo "wrongpass" | LD_PRELOAD=./hook.so ./crackme
```

The line `[hook] strcmp("wrongpass", "...")` shows the second operand, which is the password. Enter the password you found to confirm it prints "Correct!".

Now think: if the crackme didn't use `strcmp` and instead wrote its own loop comparing byte by byte, would an LD_PRELOAD hook on `strcmp` still work? As an advanced step, write a `ptrace` hook that always returns 0 to see how to neutralize a ptrace-based anti-debug check on Linux. Keep in mind that a hook only catches functions called through the dynamic library (the PLT), not static or inline functions, and that the log goes to stderr so it doesn't mix with the program's output.

<div class="lab-box">
<div class="lab-head"><b>LAB 17.6</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/17.6/src/crackme.c" download><i class="fa-solid fa-file-code"></i>src/crackme.c</a>
<a class="lab-file" href="/assets/labs/17.6/src/hook.c" download><i class="fa-solid fa-file-code"></i>src/hook.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Try it yourself first. All the output below is real, produced with gcc on Linux (WSL2).

Running without the hook:

```
$ echo "wrongpass" | ./crackme
Enter password: Nope.
```

Running with LD_PRELOAD:

```
$ echo "wrongpass" | LD_PRELOAD=./hook.so ./crackme
[hook] strcmp("wrongpass", "R3v_Pr3l04d")
Enter password: Nope.
```

The second operand `R3v_Pr3l04d` is the correct password. The crackme calls `strcmp(input, secret)`, and our hook steps in and prints both parameters before passing them to the real `strcmp`, so the secret is exposed without reading any disassembly. To confirm:

```
$ echo "R3v_Pr3l04d" | ./crackme
Enter password: Correct! Flag: CTF{R3v_Pr3l04d}
```

The password is `R3v_Pr3l04d` and the flag is `CTF{R3v_Pr3l04d}`.

This works because the crackme compares the password with `strcmp`, a dynamic library function called through the PLT. `LD_PRELOAD=./hook.so` pushes `hook.so` to the front of the symbol resolution order, so the `strcmp` in `hook.so` overrides libc's `strcmp`. The hook gets the real function through `dlsym(RTLD_NEXT, "strcmp")`, logs the arguments and calls it back so the program still runs correctly.

On the thinking question, if the crackme wrote its own byte-by-byte loop instead of calling `strcmp`, an LD_PRELOAD hook on `strcmp` would be useless because there's no `strcmp` call to intercept. In that case you hook another function it does call (for example `fgets` or `memcmp`), or go back to gdb and set a breakpoint at the comparison loop, or use `ltrace` to see which library functions it really calls.

For the ptrace anti-debug bypass, the hook is:

```c
// ptrace_bypass.c
long ptrace(int request, ...) { return 0; }
```

```sh
gcc -shared -fPIC -o ptp.so ptrace_bypass.c
LD_PRELOAD=./ptp.so gdb ./target_with_anti_debug
```

Every `ptrace(PTRACE_TRACEME, ...)` call from the program now returns 0 (a fake success), so it believes nobody is tracing it and doesn't take the anti-debug branch.

The ptrace hook is a generic example and isn't tied to a specific anti-debug target.

</details>

## Key takeaways
LD_PRELOAD loads your library before libc, so your same-named function wins, and it only intercepts functions called through the PLT (dynamic libraries). In a hook, get the real function with `dlsym(RTLD_NEXT, "name")` and call it back so the program runs normally. Hooking `strcmp` exposes the password right away if the crackme compares strings with strcmp.

ptrace is the base of gdb/strace/ltrace, and a process can only have one tracer attached. Linux anti-debug often uses `ptrace(PTRACE_TRACEME)`, where failure means it's being debugged, and you get past it with an LD_PRELOAD hook of ptrace returning 0. macOS has `DYLD_INSERT_LIBRARIES` but SIP restricts it, so people usually switch to Frida.
