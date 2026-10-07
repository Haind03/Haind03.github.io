---
title: "Lesson 3.1: Hello world under the microscope, finding the real main"
date: 2026-10-06 08:25:00 +0700
categories: ["Technique Reverse", "Part 03 · C"]
tags: [reverse-engineering, c]
render_with_liquid: false
---
You write exactly three lines of C, compile, and open it in Ghidra. You should see `main` right away, but what hits you is a function with a weird name like `entry`, `start`, or `__scrt_common_main_seh`, which calls a dozen functions that have nothing to do with "hello world". Welcome to the first truth of native reversing: **the entry point is not your main.** This lesson teaches how to squeeze past all that init code to the exact lines the author wrote.

## Why there's a pile of code before main

![From entry point through CRT startup to the real main](/assets/img/technique-reverse/assets/phan-03/crt-to-main.svg)

When the operating system loads the program, it doesn't jump straight into `main`. It jumps to the entry point recorded in the header (the `AddressOfEntryPoint` field of the PE, or `e_entry` of the ELF). This entry point points at the C runtime (CRT) init code, not code you wrote.

CRT startup has a bunch of groundwork to do before `main` can run. It sets up the C environment by initializing the heap, threads and locale, and it gets `argc`, `argv` and the `envp` environment variables to pass to `main`. It runs the global constructors: global variables needing initialization, functions marked `__attribute__((constructor))`, and in C++ the constructors of every global object. Then it calls `main`, and afterwards takes the value `main` returns and passes it to `exit` to finish cleanly.

In other words, `main` is just a function the CRT calls in the middle, not the real starting point. Once you get this, you don't panic at a forest of strange code, you know you just need to skim past it to reach `main`.

## On Linux: follow __libc_start_main

Dynamic ELF binaries on Linux follow a very recognizable mold. The entry point `_start` does a few small things and then calls `__libc_start_main`, and here's the nice part: the pointer to main is passed as the first parameter.

Look at a typical `_start` on x86-64 (Intel syntax):

```asm
_start:
    xor  ebp, ebp
    mov  r9, rdx            ; rtld_fini
    pop  rsi                ; argc
    mov  rdx, rsp           ; argv
    and  rsp, 0FFFFFFFFFFFFFFF0h
    push rax
    push rsp
    lea  r8,  [init]        ; __libc_csu_init (or equivalent)
    lea  rcx, [fini]        ; __libc_csu_fini
    lea  rdi, [main]        ; <-- HERE: the first parameter of __libc_start_main is main
    call __libc_start_main
```

Golden rule: find the call to `__libc_start_main`, then look at **rdi** (the first parameter on Linux x64). The value loaded into rdi right before, usually a `lea rdi, [sub_xxxx]`, is the address of `main`. Jump there and you're home.

With newer libc (glibc uses `__libc_start_call_main`) the details change a bit, but the principle "main is a parameter passed to libc's start function" still holds. Ghidra and IDA usually recognize it and name `main` for you, but when they guess wrong or the binary is stripped of symbols, you trace it by hand as above.

## On Windows: main is the function taking 3 parameters

PE binaries compiled by MSVC are messier. The entry point is usually `mainCRTStartup` (for console apps) or `wWinMainCRTStartup` (for GUI apps), which calls a wrapper like `__scrt_common_main_seh` that does all sorts of init, sets up SEH, runs constructors, and only then calls `main`.

There's no nicely named function like `__libc_start_main` to latch onto, so you use a few signs instead, in order of convenience. The fastest is to start from strings. Your "Hello, world" string sits in `.rdata`, so open the Strings window, click it, and look at the xrefs. The place that uses that string is almost surely `main` (or a function `main` calls directly). For hello world, the xref from the string takes you straight to where `printf`/`puts` is called, i.e. the body of `main`.

The second way is to find the function taking 3 parameters argc/argv/envp. Among the forest of CRT functions, `main` stands out in that it's called with three parameters (rcx=argc, rdx=argv, r8=envp under Win64), and its return value is used as the exit code. The last wrapper function that calls a function with that shape is where `main` gets called.

The third way is to follow calls to CRT I/O. `printf`, `puts` and `std::cout` only show up in user code, not in the CRT cleanup part, so finding them narrows down the real code region.

## Reading it: the main of hello world

Once you've traced to the spot, the body of `main` in a minimal hello world looks about like this (MSVC, shortened):

```asm
main:
    sub  rsp, 28h              ; set up stack frame + shadow space
    lea  rcx, aHelloWorld      ; rcx = pointer to "Hello, world\n"
    call printf                ; printf("Hello, world\n")
    xor  eax, eax              ; eax = 0  (return 0)
    add  rsp, 28h
    ret
```

Translated back to C:

```c
int main(void) {
    printf("Hello, world\n");   // lea rcx, string; call printf
    return 0;                   // xor eax, eax
}
```

Exactly the three lines you wrote. Everything else in the file is CRT, and once you know it's CRT you skim past without reading. That's the core skill: not reading everything, but knowing what to skip.

## Quick recognition tips

IDA Pro has FLIRT signature libraries that recognize CRT and standard library functions and name them automatically, so your code stands out in the middle of the labeled pile. Lesson 3.4 covers this in detail. Static binaries make the CRT bloat: compiling with `-static` or linking statically puts all of libc in the file, and the function count shoots up, but don't be scared, the technique for finding main is the same. Stripped binaries lose all function names, but the entry point and the start structure aren't lost, so tracing by parameter still works.

## Lab

Source code and instructions: [labs/3.1/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/3.1).

The task is to build the same `hello.c` with `gcc` (Linux) and MSVC (Windows), then open it in Ghidra or IDA and start from the entry point. Trace to the real `main` yourself in two ways, following `__libc_start_main` or the 3-parameter function, and working backwards from the string. Finally, compare the amount of CRT code before main between the two compilers.

The detailed solution is in [labs/3.1/solution.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/3.1/solution.md), but do it yourself first.

## Key takeaways
The entry point in the header points to CRT startup, not your `main`. The CRT sets up the environment, gets argc/argv/envp, runs global constructors, and only then calls `main`. On Linux, find `call __libc_start_main` and `main` is the parameter in **rdi**. On Windows there's no nicely named function, so start from strings (xref) or find the function taking 3 parameters argc/argv/envp.

`printf`/`puts`/`cout` only exist in user code, so latch onto them to narrow down the region. Recognizing the CRT so you can skip it is the skill, not reading everything.

---
Previous: [Toolkit](/posts/tr-2-8-giam-sat-he-thong/) · [Back to index](/technique-reverse/) · Next: 3.2 Variables, pointers, arrays, strings in assembly
