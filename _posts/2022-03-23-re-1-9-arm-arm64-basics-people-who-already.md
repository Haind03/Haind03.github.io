---
title: "Lesson 1.9: ARM/ARM64 basics for people who already know x86"
date: 2022-03-23 15:20:00 +0700
categories: ["Technique Reverse", "Part 01 · Computer Fundamentals for RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
If you plan to reverse Android apps, iOS apps, or firmware for routers and cameras, sooner or later you'll hit ARM. Good news: once you're used to x86, learning ARM64 isn't starting from scratch. The concepts (registers, stack, call/ret, parameters, return values) are the same, only the syntax and a few habits differ. This lesson focuses only on the differences, so you don't waste time relearning what you already know.

## RISC vs CISC, why ARM code is longer

x86 is CISC (Complex Instruction Set): one instruction can do a lot, for example `add eax, [rbx+rcx*4]` computes an address, reads memory, and adds, all in one instruction.

ARM is RISC (Reduced Instruction Set): each instruction does one simple thing, instructions have a fixed length (4 bytes on ARM64), and most importantly arithmetic instructions only work on registers, they don't touch memory directly. To add a value in memory, you have to load it into a register, add, then store it back. Three instructions instead of one.

The practical consequence when reading: ARM64 code is usually longer than x86 in instruction count, but each instruction is easier to understand because it's simple. You'll see lots of `ldr`/`str` pairs surrounding the computation.

## ARM64 registers

ARM64 (also called AArch64) has 31 general purpose registers, much roomier than x86:

```
x0  x1  x2  ... x30     (64 bit)
w0  w1  w2  ... w30     (low 32 bits of the matching x)
```

Exactly like `rax`/`eax` on x86: `x0` is 64 bits, `w0` is the low 32 bits of the same register. Seeing `w0` and `x0` in the same function means the same register, just a different width.

A few registers have conventional roles you must remember, because they help you read fast:

| Register | Role |
|---|---|
| `x0` to `x7` | First 8 function parameters. Far more than x86 (x86-64 has only 4 or 6) |
| `x0` | Also holds the return value, just like rax |
| `x29` (fp) | Frame pointer, the base pointer of the stack frame, plays the role of rbp |
| `x30` (lr) | Link register, this one is new, see below |
| `sp` | Stack pointer, like rsp |
| `pc` | Program counter, like rip |

The number one thing x86 people trip over is that parameters are in `x0..x7`, not `rcx rdx` or whatever. The return value is in `x0`, not rax. To read an ARM64 function call, look at `x0, x1, x2...` for the parameters.

## lr, the biggest difference

On x86, the `call` instruction pushes the return address onto the stack, and `ret` pops it off. ARM does it differently: the call instruction `bl` (branch with link) saves the return address into the lr register (x30), without touching the stack.

That means for a leaf function (a function that doesn't call other functions), the return address sits entirely in lr, no stack needed. `ret` simply jumps to the address in lr.

But if function A calls function B, then the lr holding A's return address gets overwritten by `bl` when calling B. So a non-leaf function has to save lr onto the stack at the start (prologue) and restore it before ret (epilogue). You'll see this pattern constantly:

```asm
stp  x29, x30, [sp, #-16]!   ; save fp(x29) and lr(x30) to the stack, and subtract 16 from sp
mov  x29, sp                 ; set up the frame pointer
... function body, may bl to other functions ...
ldp  x29, x30, [sp], #16     ; restore fp and lr, add 16 back to sp
ret                          ; jump to lr
```

`stp`/`ldp` are "store pair"/"load pair", saving/loading two registers at once, which ARM uses a lot to save instructions. The `!` means update sp as well (pre-index). Seeing `stp x29, x30` at the start of a function tells you right away: this is a prologue, and this function calls other functions.

## Common instructions

Mapped directly against x86 so it's easier to remember:

```asm
mov  x0, #5          ; x0 = 5           (immediate numbers have a #)
mov  x1, x2          ; x1 = x2
add  x0, x1, x2      ; x0 = x1 + x2     (three operands: dest, source1, source2)
sub  x0, x1, #8      ; x0 = x1 - 8
cmp  x0, #10         ; compare, set flags  (same as x86)
```

Note that ARM uses three operands, `add x0, x1, x2` is `x0 = x1 + x2`, the destination is separate from the sources. Different from x86 where `add eax, ebx` is `eax += ebx` (the destination is also a source).

Memory access is separated out with `ldr`/`str`:

```asm
ldr  x0, [x1]        ; x0 = *(x1)        load from the address in x1
ldr  x0, [x1, #8]    ; x0 = *(x1 + 8)    usually reading a struct field
str  x0, [x1]        ; *(x1) = x0        write to memory
```

This load/store pair is what replaces `mov eax, [rbx]` on x86. Every memory access goes through `ldr`/`str`, remember that and you can read it.

Branching and calling:

```asm
b    label           ; unconditional jump    (like jmp)
b.eq label           ; jump if equal        (like je, after cmp)
b.ne label           ; jump if not equal    (like jne)
b.gt / b.lt / ...    ; greater than / less than
cbz  x0, label       ; jump if x0 == 0     (compare and branch if zero, merges cmp+je)
cbnz x0, label       ; jump if x0 != 0
bl   func            ; call a function, save the return address in lr  (like call)
blr  x8              ; call the function at the address in x8 (indirect call)
ret                  ; return (jump to lr)
```

`cbz`/`cbnz` is a convenience unique to ARM: compare with 0 and jump in one instruction. When you see `cbz x0, somewhere`, read it as "if x0 equals 0, jump", no need to look for a cmp before it.

## Reading a real snippet

The same kind of length-check function as in lesson 1.3, but in ARM64:

```asm
check_password:
    ldr  w0, [sp, #12]      ; load a local variable (the string length) into w0
    cmp  w0, #8             ; compare with 8
    b.ne fail              ; if not 8, jump to fail
    mov  w0, #1            ; w0 = 1 (correct)
    ret
fail:
    mov  w0, #0            ; w0 = 0 (wrong)
    ret
```

Translated to C:

```c
int check_password() {
    int len = ...;        // local variable at [sp+12]
    if (len != 8)         // cmp + b.ne
        return 0;
    return 1;
}
```

Logically identical to the x86 version. The only differences: `w0` instead of `eax` as the return value, `ldr` instead of `mov` for reading memory, `b.ne` instead of `jne`. Once you're used to it you read it smoothly.

## 32-bit ARM and Thumb mode, a short reminder

On older devices and lots of firmware, you'll meet 32-bit ARM (AArch32), where the registers are `r0..r15` (r13=sp, r14=lr, r15=pc). It also has two instruction encoding modes: ARM (4-byte instructions) and Thumb (2 or 4-byte instructions, more compact, often used to save memory). One binary can mix both, and the mode switches via the lowest bit of the function address (odd = Thumb). This often makes disassemblers guess wrong, so if ARM32 code decodes into garbage, try forcing Thumb or the other way around. The details are saved for the firmware lessons in Part 18.

## Lab

See [labs/1.9/](https://github.com/Haind03/Technique-Reverse/tree/main/labs/1.9). You'll cross-compile a small C file to ARM64 and compare the assembly with the source yourself, or if you can't install the toolchain, read the given ARM64 snippet and translate it back to C. The solution is in `labs/1.9/solution.md`, do it yourself before opening it.

## Key takeaways
ARM is RISC: simple fixed-length instructions, arithmetic only on registers, and memory access has to go through `ldr`/`str`. The registers are `x0..x30` (64 bit) and `w0..w30` (low 32 bits), with parameters in `x0..x7` and the return in `x0`.

`bl` saves the return address into `lr` (x30) instead of pushing to the stack like `call`, so non-leaf functions must save lr to the stack in the prologue (`stp x29, x30, [sp,...]`). For a quick mapping, `mov`/`ldr`/`str` handle data, `add`/`sub`/`cmp` handle arithmetic, and `b`/`b.eq`/`cbz`/`bl`/`ret` handle branching and calls. ARM32 has ARM and Thumb modes mixed together, so watch out for the disassembler guessing the wrong mode.
