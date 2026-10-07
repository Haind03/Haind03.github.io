---
title: "Lesson 1.4: x86/x64 assembly (2), stack frames and calling conventions"
date: 2026-10-06 08:07:00 +0700
categories: ["Technique Reverse", "Part 01 · Computer Fundamentals for RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Last lesson you read a simple function. But real functions take parameters, have local variables, and call other functions. All of that happens on the stack following a set of rules called a calling convention. Once you know these rules, looking at a `call` tells you which parameters are being passed, what the function returns, and where the locals live. Without them, you'll be guessing all afternoon.

![Stack frame of a function call: parameters, return address, saved rbp, locals, shadow space](/assets/img/technique-reverse/assets/phan-01/stack-frame.svg)

## What call and ret really do

These two instructions sound trivial but they're the backbone of every function call, so understand each step.

When the CPU runs `call 0x401500`, it first pushes the address of the instruction right after the `call` onto the stack. This is the return address, so it knows the way back later. Then it jumps to `0x401500`.

When the function finishes and hits `ret`, it pops the return address off the stack and jumps there.

So the stack holds the return address, and that's exactly why the stack is so tied to function calls. Remember from lesson 1.2: the stack grows down, so `push` decreases rsp and `pop` increases rsp.

## Prologue and epilogue, the familiar opening and closing

Almost every function (when compiled without optimization, `-O0`) opens with a few identical instructions. These are called the prologue (builds the frame) and the epilogue (tears the frame down):

```asm
my_function:
    push rbp            ; prologue: save the old base pointer
    mov  rbp, rsp       ; new base pointer = current top of stack
    sub  rsp, 0x20      ; reserve space for locals (0x20 bytes)
    ...                 ; function body
    leave              ; epilogue: same as mov rsp,rbp; pop rbp
    ret
```

Seeing the `push rbp` / `mov rbp, rsp` pair at the top tells you for sure a function is starting. Then `sub rsp, N` means the function is reserving N bytes on the stack for locals. At the end `leave` cleans up that frame and `ret` goes back. Recognizing this skeleton lets you mark out a function even when IDA hasn't identified it correctly.

The block of stack a function uses (locals, the saved base pointer, the return address) is called a stack frame. Every running function has its own frame, stacked on top of the frame of the function that called it.

## Calling convention, the rules for passing parameters

This is the core part. A calling convention answers three questions: where parameters get passed (registers or stack), where the return value goes, and who is responsible for cleaning the parameters off the stack after the call (the caller or the callee).

The rules differ by architecture (32 or 64 bit) and by OS. You don't need to memorize all of them, just be solid on the two most used today, Win64 and System V, and know the old 32-bit ones in outline so you don't stand there confused when you meet old code.

### The 64-bit world (what you'll meet most)

On 64-bit, parameters are passed in registers first for speed, and only spill to the stack when registers run out. There are two sets of rules.

Microsoft x64 (Win64), used on Windows, passes the first 4 integer/pointer parameters in `rcx`, `rdx`, `r8`, `r9` (in exactly this order). The 5th parameter onward is pushed on the stack, and the return value is in `rax`. There's also a speciality called shadow space: the caller must reserve 32 bytes (0x20) on the stack right above the return address, even if the function has fewer than 4 parameters. This space gives the called function somewhere to spill the 4 parameter registers if it wants. Seeing `sub rsp, 0x28` or numbers like 0x20 plus something before a series of `call`s is a sign of shadow space. At first it confuses beginners ("why reserve space and not use it"), but once you know its name the question goes away.

System V AMD64, used on Linux and macOS, passes the first 6 integer/pointer parameters in `rdi`, `rsi`, `rdx`, `rcx`, `r8`, `r9`. The 7th parameter onward goes on the stack, and the return value is in `rax`. There's no shadow space, but there's a 128-byte "red zone" right below rsp that leaf functions can use freely.

Looking at the two lists, you can see right away they differ. For the same function `f(a, b, c)`, on Windows `a` is in rcx and on Linux `a` is in rdi. Get the OS wrong and you read every parameter wrong. When you open a binary, remember to ask: is this a Windows or a Linux file?

A real call sequence on Win64:

```asm
; call add3(10, 20, 30) on Windows x64
mov  r8d, 30        ; parameter 3 -> r8
mov  edx, 20        ; parameter 2 -> rdx
mov  ecx, 10        ; parameter 1 -> rcx
call add3
; the result is now in eax
```

The same function on Linux:

```asm
mov  edx, 30        ; parameter 3 -> rdx
mov  esi, 20        ; parameter 2 -> rsi
mov  edi, 10        ; parameter 1 -> rdi
call add3
```

### The 32-bit world (old code, still around)

On 32-bit there aren't many registers to spare, so parameters mostly go on the stack, pushed right to left. Three conventions whose names you'll hear often.

With cdecl, parameters are pushed on the stack right-to-left and the caller cleans the stack after the call (you'll see `add esp, N` right after the `call`). It's the default for C on 32-bit. With stdcall, parameters are also pushed right-to-left, but the callee cleans up (ends with `ret N` instead of `ret`). This is the convention of most Win32 APIs, and seeing `ret 0xC` tells you the function cleans 12 bytes of parameters, so about 3 parameters. With fastcall, the first 2 parameters go in `ecx`, `edx` and the rest on the stack, which is slightly faster.

A quick trick for telling them apart when reading 32-bit: look after the `call`. An `add esp, N` means cdecl (caller cleans). A function ending in `ret N` is stdcall (callee cleans). This is how you work out the number of parameters without reading the function body.

## Reading the stack frame in IDA

IDA does the heaviest part for you: it analyzes the frame and gives the slots proper names. You'll see two kinds of names. `var_4`, `var_8`, `var_C`... are local variables, at negative offsets from rbp (`[rbp-4]`, `[rbp-8]`), and the number after `var_` is the offset, e.g. `var_4` is `[rbp-4]`. `arg_0`, `arg_4`, `arg_8`... are parameters passed on the stack (the spill, or on 32-bit), at positive offsets from rbp.

When you double-click `var_8` in IDA and rename it to `password_len`, every use of that slot changes with it. This is how you turn a function full of unreadable `var_x` into code you can read like English. Whenever you figure out what a variable is, name it right away, don't save it for later.

One easy mistake: in a 64-bit function, parameters arrive through registers (rcx, rdx...) and not the stack, so at the top of the function the compiler usually copies them into stack variables for convenience. You'll see things like `mov [rbp-18h], rcx` right after the prologue, meaning "store parameter 1 in a local slot". Recognizing this pattern helps you trace which register the original parameter was in.

## Reading a function with parameters

```asm
; Win64, -O0
sum3:
    push rbp
    mov  rbp, rsp
    mov  [rbp-18h], ecx    ; store parameter 1 (a) in a local
    mov  [rbp-14h], edx    ; parameter 2 (b)
    mov  [rbp-10h], r8d    ; parameter 3 (c)
    mov  eax, [rbp-18h]    ; eax = a
    add  eax, [rbp-14h]    ; eax += b
    add  eax, [rbp-10h]    ; eax += c
    pop  rbp
    ret                    ; returns eax = a+b+c
```

Decompiled back:

```c
int sum3(int a, int b, int c) {   // a=rcx, b=rdx, c=r8 (Win64)
    return a + b + c;
}
```

You just did two things: recognized three parameters from rcx/rdx/r8 (so you know it's Win64), and followed them being accumulated into eax to return. That's the whole craft of reading functions.

## Lab

The folder [labs/1.4/](https://github.com/Haind03/Technique-Reverse/blob/main/../labs/1.4) has a C file with a few functions taking different numbers of parameters. The task: build with `-O0` on both Windows (or picture Win64) and Linux, then open it in IDA/Ghidra/objdump and confirm yourself which registers the parameters are in on each system, where the shadow space is, and which are the locals. The answer is in `solution.md`, but try comparing on your own first.

## Key takeaways
`call` pushes the return address on the stack then jumps, and `ret` pops it and goes back. The prologue `push rbp; mov rbp, rsp` marks the start of a function and `leave; ret` marks the end. On Win64, parameters 1-4 are in `rcx, rdx, r8, r9` with 32 bytes of shadow space and the return in `rax`. On System V (Linux/macOS), parameters 1-6 are in `rdi, rsi, rdx, rcx, r8, r9` and the return is in `rax`.

On 32-bit, parameters go on the stack: `add esp, N` after a call means cdecl (caller cleans) and `ret N` means stdcall (callee cleans). In IDA, `var_x` is a local (`[rbp-x]`) and `arg_x` is a parameter passed on the stack, so rename as soon as you understand it.
