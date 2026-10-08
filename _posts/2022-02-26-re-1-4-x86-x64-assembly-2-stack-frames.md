---
title: "Lesson 1.4: x86/x64 assembly (2), stack frames and calling conventions"
image:
  path: /assets/img/covers/re-1-4-x86-x64-assembly-2-stack-frames.webp
  alt: "Lesson 1.4: x86/x64 assembly (2), stack frames and calling conventions"
date: 2022-01-18 02:20:00 +0700
categories: ["Reverse Engineering", "Part 01 · Computer Fundamentals for RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Last lesson you read a simple function. Real functions take parameters, have local variables, and call other functions. All of that happens on the stack, following rules called a calling convention. Once you know them, a `call` tells you which parameters are passed, what the function returns, and where the locals live. Without them you'll be guessing all afternoon.

![Stack frame of a function call: parameters, return address, saved rbp, locals, shadow space](/assets/img/re/part-01/stack-frame.svg)

## What call and ret do

These two instructions look trivial but every function call depends on them.

When the CPU runs `call 0x401500`, it first pushes the address of the instruction right after the `call` onto the stack. This is the return address, so it knows the way back. Then it jumps to `0x401500`.

When the function finishes and hits `ret`, it pops the return address off the stack and jumps there.

That's why the stack is so tied to function calls. Remember from lesson 1.2 that the stack grows down, so `push` decreases rsp and `pop` increases rsp.

## Prologue and epilogue

Almost every function (compiled without optimization, `-O0`) opens with a few identical instructions. These are the prologue (builds the frame) and the epilogue (tears the frame down):

```asm
my_function:
    push rbp            ; prologue: save the old base pointer
    mov  rbp, rsp       ; new base pointer = current top of stack
    sub  rsp, 0x20      ; reserve space for locals (0x20 bytes)
    ...                 ; function body
    leave              ; epilogue: same as mov rsp,rbp; pop rbp
    ret
```

The `push rbp` / `mov rbp, rsp` pair at the top tells you a function is starting. `sub rsp, N` means the function reserves N bytes on the stack for locals. At the end `leave` cleans up that frame and `ret` goes back. Recognizing this lets you mark out a function even when IDA hasn't identified it correctly.

The block of stack a function uses (locals, the saved base pointer, the return address) is called a stack frame. Every running function has its own frame, stacked on top of the frame of its caller.

## Calling convention

A calling convention answers three questions, namely where parameters get passed (registers or stack), where the return value goes, and who cleans the parameters off the stack after the call (the caller or the callee).

The rules differ by architecture (32 or 64 bit) and by OS. You don't need to memorize all of them. Be solid on the two most used today, Win64 and System V, and know the old 32-bit ones in outline so old code doesn't confuse you.

### 64-bit (what you'll meet most)

On 64-bit, parameters go in registers first and only spill to the stack when registers run out. There are two sets of rules.

Microsoft x64 (Win64), used on Windows, passes the first 4 integer/pointer parameters in `rcx`, `rdx`, `r8`, `r9` (in this order). The 5th parameter onward is pushed on the stack, and the return value is in `rax`. There's also shadow space, which means the caller must reserve 32 bytes (0x20) on the stack right above the return address, even if the function has fewer than 4 parameters. The called function can use it to spill the 4 parameter registers. Seeing `sub rsp, 0x28` or a 0x20 plus something before a series of `call`s is a sign of shadow space. At first it confuses beginners ("why reserve space and not use it"), but once you know the name the question goes away.

System V AMD64, used on Linux and macOS, passes the first 6 integer/pointer parameters in `rdi`, `rsi`, `rdx`, `rcx`, `r8`, `r9`. The 7th parameter onward goes on the stack, and the return value is in `rax`. There's no shadow space, but there's a 128-byte "red zone" right below rsp that leaf functions can use freely.

The two lists differ. For the same function `f(a, b, c)`, on Windows `a` is in rcx and on Linux `a` is in rdi. Get the OS wrong and you read every parameter wrong, so when you open a binary, first check whether it's a Windows or a Linux file.

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

### 32-bit (old code, still around)

On 32-bit there aren't many registers to spare, so parameters mostly go on the stack, pushed right to left. Three conventions come up often.

With cdecl, parameters are pushed right-to-left and the caller cleans the stack after the call (you'll see `add esp, N` right after the `call`). It's the default for C on 32-bit. With stdcall, parameters are also pushed right-to-left, but the callee cleans up (ends with `ret N` instead of `ret`). Most Win32 APIs use it, and `ret 0xC` means the function cleans 12 bytes of parameters, so about 3 parameters. With fastcall, the first 2 parameters go in `ecx`, `edx` and the rest on the stack, which is slightly faster.

A quick way to tell them apart in 32-bit code is to look after the `call`. An `add esp, N` means cdecl (caller cleans). A function ending in `ret N` is stdcall (callee cleans). That gives you the number of parameters without reading the function body.

## Reading the stack frame in IDA

IDA does the heavy part for you. It analyzes the frame and gives the slots names. There are two kinds. `var_4`, `var_8`, `var_C`... are local variables, at negative offsets from rbp (`[rbp-4]`, `[rbp-8]`), and the number after `var_` is the offset, e.g. `var_4` is `[rbp-4]`. `arg_0`, `arg_4`, `arg_8`... are parameters passed on the stack (the spill, or on 32-bit), at positive offsets from rbp.

When you double-click `var_8` in IDA and rename it to `password_len`, every use of that slot changes with it. That's how you turn a function full of `var_x` into code you can read. When you figure out what a variable is, name it right away.

One easy mistake concerns 64-bit functions. Parameters arrive through registers (rcx, rdx...) and not the stack, so at the top of the function the compiler usually copies them into stack variables. You'll see things like `mov [rbp-18h], rcx` right after the prologue, which stores parameter 1 in a local slot. Knowing this pattern helps you trace which register the original parameter was in.

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

That's two things done, since you recognized three parameters from rcx/rdx/r8 (so it's Win64), and followed them being added into eax to return. Reading functions is mostly this.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 1.4</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/1.4.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/1.4/src/params.c" download><i class="fa-solid fa-download"></i>src/params.c</a>
</div>
</div>

The file `params.c` has three functions that differ in the number and type of their parameters. `sum3(a, b, c)` takes three parameters, which fit in registers under both conventions. `sum6(a..f)` takes six, enough to show Win64 spilling parameters 5 and 6 onto the stack. `mix(char, int, long, int*)` mixes types so you can see whether the compiler picks 32-bit or 64-bit registers. The goal is to check what this lesson says yourself, by building the same C file on both systems and comparing how parameters are passed.

Build without optimization so the stack frame stays readable. With optimization on, the compiler inlines everything and there's nothing left to look at. If `sum3` and `sum6` still get inlined at `-O0`, add `__attribute__((noinline))` (GCC) or move them into a separate file.

```
# Linux / macOS (System V AMD64)
gcc -O0 -g -o params params.c

# Windows, MSVC (Win64) in a Developer Command Prompt
cl /Od /Zi params.c

# Windows, MinGW
gcc -O0 -g -o params.exe params.c
```

Ideally you build on both systems and compare directly. With only one machine you can still do that system's half and check the other against the solution below. Open the binary in IDA or Ghidra, or go quick with the command line:

```
objdump -d -M intel params        # Linux
gdb -batch -ex "disassemble sum6" ./params
dumpbin /disasm params.exe        # Windows MSVC
```

For `sum3`, find which registers the parameters a, b and c are loaded from, comparing the Win64 list (`rcx, rdx, r8`) with System V (`rdi, rsi, rdx`), and where the local `total` sits relative to `rbp`. For `sum6`, find the registers of the first four parameters and where parameters 5 and 6 are read from on the stack, with the exact offsets. For `mix`, check whether `char x` goes through an 8-bit register or gets extended, and which 64-bit register holds the pointer `int *p`. In the Win64 build, look for the `sub rsp, 0x??` at the start of `main` before the run of calls, and identify the 0x20 part of it as the shadow space. Finally, after each `call` in `main`, note which register the return value is read from before it goes to `printf`. On Win64, don't worry when you see stack space reserved but apparently unused, that's the shadow space. Compare on your own first, then open the solution.

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Compare on your own first. What follows is the expected result for a `-O0` build. The exact offsets can drift a little with the compiler and its version, but the registers used for parameters are fixed by the convention.

### sum3(a, b, c)

On Win64 (MSVC/MinGW) the parameters arrive in `ecx` (a), `edx` (b) and `r8d` (c). Since they are 32-bit `int`s, the 32-bit names `ecx/edx/r8d` appear rather than `rcx/rdx/r8`. The prologue copies them into stack variables:

```asm
mov [rbp+10h], ecx     ; a  (MSVC often uses [rbp+x] for the saved parameters)
mov [rbp+18h], edx     ; b
mov [rbp+20h], r8d     ; c
```

On System V (gcc on Linux) the parameters arrive in `edi` (a), `esi` (b) and `edx` (c):

```asm
mov [rbp-14h], edi     ; a
mov [rbp-18h], esi     ; b
mov [rbp-1Ch], edx     ; c
```

The local `total` is its own `[rbp-x]` slot, where the three values are summed before being copied to `eax` for the return. The main difference in this lab is that the first parameter a sits in rcx on Windows but in rdi on Linux.

### sum6(a, b, c, d, e, f)

Win64 has only 4 parameter registers, so a, b, c and d go into `ecx, edx, r8d, r9d`, while e (parameter 5) and f (parameter 6) are read from the caller's stack. Inside `sum6` you see them read through positive offsets from rbp, like `[rbp+30h]` and `[rbp+38h]`, which sit above the return address and the shadow space.

System V has 6 parameter registers, so all six fit in `edi, esi, edx, ecx, r8d, r9d` and nothing goes on the stack. The same six-parameter function makes Win64 spill two parameters to the stack while System V does not, so you have to know which system you're on before reading the code.

### mix(char x, int y, long z, int *p)

The parameter order by convention is x->rcx, y->rdx, z->r8, p->r9 on Win64, and x->rdi, y->rsi, z->rdx, p->rcx on System V. As for types, `char x` is usually widened with `movzx`/`movsx` from 8 bits (cl/dil) to 32 or 64 bits before the arithmetic, because x is added to a `long`. You'll see something like `movsx eax, byte ptr [rbp-x]`. The `long z` is 64-bit and uses the full register name `r8`/`rdx`. The pointer `int *p` is 64-bit too and uses `r9`/`rcx` in full. Inside the function a `test`/`cmp` checks `p != NULL` before dereferencing, matching `if (p) r += *p;`, and the dereference itself is a `mov eax, [r??]` reading the value the pointer points to. Pointers and longs use full 64-bit registers while int and char use the 32-bit and 8-bit names, so the register name alone lets you guess the size of the type.

### Shadow space in main (Win64 only)

At the start of `main`, before the calls, you see an instruction like this:

```asm
sub rsp, 0x38      ; (example) shadow space 0x20 + room for spilled parameters + 16-byte alignment
```

The 0x20 (32 bytes) in that number is the shadow space, a mandatory gap left for the callee even when the called function takes fewer than 4 parameters. `sum6` needs extra room for parameters 5 and 6, so the caller reserves more. System V has no line dedicated to shadow space.

### Return value

After each `call sum3` / `call sum6` / `call mix`, the result is in `eax` (for the functions returning `int`) or `rax` (for `mix`, which returns `long`). You see it moved straight into a parameter for `printf`:

```asm
call sum3
mov  edx, eax      ; result -> 2nd parameter of printf (Win64: rdx)
lea  rcx, [format] ; format string -> 1st parameter
call printf
```

Parameters go in through rcx/rdx and so on, the result comes out through rax, and rax then becomes a parameter of the next call. Once you can read that flow, you can read how functions connect to each other.

To sum up, parameter 1 is in rcx on Win64 and rdi on System V, so check which system you're on before reading. Win64 has only 4 parameter registers and spills parameter 5 onward to the stack, while System V has 6. The register name (ecx vs rcx) shows the size of the data type. The 0x20 shadow space is Win64 only and isn't a local variable. The return value is always in rax/eax.

</details>

## Key takeaways
`call` pushes the return address on the stack then jumps, and `ret` pops it and goes back. The prologue `push rbp; mov rbp, rsp` marks the start of a function and `leave; ret` marks the end. On Win64, parameters 1-4 are in `rcx, rdx, r8, r9` with 32 bytes of shadow space and the return in `rax`. On System V (Linux/macOS), parameters 1-6 are in `rdi, rsi, rdx, rcx, r8, r9` and the return is in `rax`.

On 32-bit, parameters go on the stack, so `add esp, N` after a call means cdecl (caller cleans) and `ret N` means stdcall (callee cleans). In IDA, `var_x` is a local (`[rbp-x]`) and `arg_x` is a parameter passed on the stack, so rename as soon as you understand it.
