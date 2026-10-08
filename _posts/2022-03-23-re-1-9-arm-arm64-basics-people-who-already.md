---
title: "Lesson 1.9: ARM/ARM64 basics for people who know x86"
image:
  path: /assets/img/covers/re-1-9-arm-arm64-basics-people-who-already.webp
  alt: "Lesson 1.9: ARM/ARM64 basics for people who know x86"
date: 2022-03-23 15:20:00 +0700
categories: ["Reverse Engineering", "Part 01 · Computer Fundamentals for RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
If you plan to reverse Android apps, iOS apps, or firmware for routers and cameras, you'll hit ARM sooner or later. If you already know x86, ARM64 isn't starting from zero. Registers, stack, call/ret, parameters and return values all work the same way, only the syntax and a few habits differ. This lesson covers only the differences.

## RISC vs CISC

x86 is CISC (Complex Instruction Set), so one instruction can do a lot, for example `add eax, [rbx+rcx*4]` computes an address, reads memory, and adds, all in one instruction.

ARM is RISC (Reduced Instruction Set), so each instruction does one simple thing, instructions have a fixed length (4 bytes on ARM64), and arithmetic instructions only work on registers, they don't touch memory directly. To add a value in memory, you load it into a register, add, then store it back. Three instructions instead of one.

So ARM64 code is usually longer than x86 in instruction count, but each instruction is simple to read. You'll see lots of `ldr`/`str` pairs around the computation.

## ARM64 registers

ARM64 (also called AArch64) has 31 general purpose registers, much more than x86:

```
x0  x1  x2  ... x30     (64 bit)
w0  w1  w2  ... w30     (low 32 bits of the matching x)
```

Same idea as `rax`/`eax` on x86. `x0` is 64 bits, `w0` is the low 32 bits of the same register. If `w0` and `x0` both appear in one function, it's the same register at a different width.

A few registers have conventional roles worth remembering:

| Register | Role |
|---|---|
| `x0` to `x7` | First 8 function parameters. Far more than x86 (x86-64 has only 4 or 6) |
| `x0` | Also holds the return value, just like rax |
| `x29` (fp) | Frame pointer, the base pointer of the stack frame, plays the role of rbp |
| `x30` (lr) | Link register, this one is new, see below |
| `sp` | Stack pointer, like rsp |
| `pc` | Program counter, like rip |

x86 people usually trip on this first. Parameters are in `x0..x7`, not `rcx rdx` or whatever, and the return value is in `x0`, not rax. To read an ARM64 function call, look at `x0, x1, x2...` for the parameters.

## lr, the biggest difference

On x86, the `call` instruction pushes the return address onto the stack, and `ret` pops it off. ARM does it differently. The call instruction `bl` (branch with link) saves the return address into the lr register (x30), without touching the stack.

For a leaf function (one that doesn't call other functions), the return address stays in lr and no stack is needed. `ret` simply jumps to the address in lr.

But if function A calls function B, the lr holding A's return address gets overwritten by `bl` when calling B. So a non-leaf function has to save lr onto the stack at the start (prologue) and restore it before ret (epilogue). You'll see this pattern all the time:

```asm
stp  x29, x30, [sp, #-16]!   ; save fp(x29) and lr(x30) to the stack, and subtract 16 from sp
mov  x29, sp                 ; set up the frame pointer
... function body, may bl to other functions ...
ldp  x29, x30, [sp], #16     ; restore fp and lr, add 16 back to sp
ret                          ; jump to lr
```

`stp`/`ldp` are "store pair"/"load pair", saving/loading two registers at once, which ARM uses a lot to save instructions. The `!` means update sp as well (pre-index). `stp x29, x30` at the start of a function means it's a prologue and the function calls other functions.

## Common instructions

Mapped against x86 so it's easier to remember:

```asm
mov  x0, #5          ; x0 = 5           (immediate numbers have a #)
mov  x1, x2          ; x1 = x2
add  x0, x1, x2      ; x0 = x1 + x2     (three operands: dest, source1, source2)
sub  x0, x1, #8      ; x0 = x1 - 8
cmp  x0, #10         ; compare, set flags  (same as x86)
```

ARM uses three operands, so `add x0, x1, x2` is `x0 = x1 + x2`, and the destination is separate from the sources. On x86 `add eax, ebx` is `eax += ebx`, so the destination is also a source.

Memory access is separate, through `ldr`/`str`:

```asm
ldr  x0, [x1]        ; x0 = *(x1)        load from the address in x1
ldr  x0, [x1, #8]    ; x0 = *(x1 + 8)    usually reading a struct field
str  x0, [x1]        ; *(x1) = x0        write to memory
```

This load/store pair replaces `mov eax, [rbx]` on x86. Every memory access goes through `ldr`/`str`.

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

`cbz`/`cbnz` only exist on ARM and compare with 0 and jump in one instruction. Read `cbz x0, somewhere` as "if x0 equals 0, jump", there's no cmp before it.

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

The logic is the same as the x86 version. The differences are `w0` instead of `eax` as the return value, `ldr` instead of `mov` for reading memory, and `b.ne` instead of `jne`. After a while you read it without thinking.

## 32-bit ARM and Thumb mode

On older devices and a lot of firmware, you'll meet 32-bit ARM (AArch32), where the registers are `r0..r15` (r13=sp, r14=lr, r15=pc). It also has two instruction encoding modes, ARM (4-byte instructions) and Thumb (2 or 4-byte instructions, more compact, often used to save memory). One binary can mix both, and the mode switches via the lowest bit of the function address (odd = Thumb). Disassemblers often guess wrong here, so if ARM32 code decodes into garbage, try forcing Thumb, or the other way around. Details are in the firmware lessons in Part 18.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 1.9</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/1.9.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/1.9/src/arm_demo.c" download><i class="fa-solid fa-download"></i>src/arm_demo.c</a>
</div>
</div>

The goal is to see the ideas from this lesson in real assembly, such as parameters arriving in `x0..x7`, the result leaving in `x0`, and the `stp x29, x30` pattern in the prologue of a function that calls another function. I'd build `arm_demo.c` yourself. On Ubuntu or WSL you need an ARM64 cross-compiler, then you compile statically and disassemble:

```
sudo apt install gcc-aarch64-linux-gnu binutils-aarch64-linux-gnu
aarch64-linux-gnu-gcc -O0 -o arm_demo arm_demo.c -static
aarch64-linux-gnu-objdump -d arm_demo | less
```

If you also want to run it, install `qemu-user` and start it with `qemu-aarch64 ./arm_demo 12345678`.

Once you have the disassembly, find `add3` and confirm that the three parameters come in through `x0/w0`, `x1/w1` and `x2/w2` and that the final result sits in `w0`. Then find `is_eight`, locate the `cmp` against 8 and the jump after it, and decide whether it is `b.ne` or `cbz`/`cbnz`, and why the compiler picked that one. Next look at `check` and confirm it opens with `stp x29, x30, [sp, ...]` to save lr because it calls `strlen` and `is_eight`, while `add3` and `is_eight` are leaf functions and do not need to. Finally count the `ldr`/`str` instructions and ask yourself why ARM needs them when x86 folds the memory access into the arithmetic instruction.

If you cannot install the toolchain, there is a second route, which is to translate this ARM64 snippet back into C. As a hint, 0x61 is `'a'`, 0x7a is `'z'`, and 0x20 is the distance between upper and lower case in ASCII.

```asm
0000000000000730 <mystery>:
  730:  cmp   w0, #0x61
  734:  b.lt  744 <mystery+0x14>
  738:  cmp   w0, #0x7a
  73c:  b.gt  744 <mystery+0x14>
  740:  sub   w0, w0, #0x20
  744:  ret
```

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Route 1 is going through the functions one by one. The exact output changes with the gcc version, but at `-O0` you will see these patterns.

`add3` is a leaf function:

```asm
<add3>:
    sub   sp, sp, #0x10        ; reserve stack space for the parameters (-O0 spills them to the stack)
    str   w0, [sp, #0xc]       ; a (parameter 1, arrives in w0) is saved to the stack
    str   w1, [sp, #0x8]       ; b (parameter 2, w1)
    str   w2, [sp, #0x4]       ; c (parameter 3, w2)
    ldr   w1, [sp, #0xc]
    ldr   w0, [sp, #0x8]
    add   w1, w1, w0           ; a + b
    ldr   w0, [sp, #0x4]
    add   w0, w1, w0           ; (a+b) + c
    add   sp, sp, #0x10
    ret                        ; the result is in w0
```

The three parameters enter in `w0, w1, w2`, which are just `x0, x1, x2` seen as 32 bits, so this is the `x0..x7` convention. The final result is in `w0`, which is the return value. There is no `stp x29, x30` because this is a leaf function that calls nothing, so it never has to save `lr`. The many `ldr`/`str` instructions come from `-O0` pushing everything to the stack and loading it back. With `-O2` they vanish and the math happens directly in registers.

`is_eight` is also a leaf function:

```asm
<is_eight>:
    ...
    cmp   w0, #0x8
    b.eq  <branch returning 1>   ; or cmp + b.ne to the branch returning 0
    mov   w0, #0x0
    ...
    mov   w0, #0x1
    ret
```

There is a `cmp w0, #8`, matching `n != 8` in the source. The jump is usually `b.ne` (or `b.eq`), not `cbz`, because we compare against 8 and not against 0. `cbz`/`cbnz` can only be fused with a comparison against 0, so you would see `cbnz` mostly if the source said `if (n != 0)`. It is still a leaf, so there is no lr save.

`check` is not a leaf:

```asm
<check>:
    stp   x29, x30, [sp, #-0x20]!   ; save fp (x29) and lr (x30), since we are about to bl into other functions
    mov   x29, sp
    ...
    bl    <strlen>                  ; bl overwrites lr, so saving lr beforehand was necessary
    ...
    bl    <is_eight>
    ...
    ldp   x29, x30, [sp], #0x20     ; restore fp and lr
    ret
```

This shows the rule from the lesson, which is that any function that calls another (`bl`) gets its `lr` overwritten, so it must save `lr` on the stack in the prologue and restore it in the epilogue. `add3` and `is_eight` have no `stp x29, x30` line at all.

As for `ldr`/`str`, ARM is RISC, so arithmetic instructions only work on registers. To add a value that lives in memory you first `ldr` it into a register, add, and `str` it back if you need to store it. x86 (CISC) lets you write `add eax, [mem]` and do it all in one instruction, which is why x86 code is shorter in instruction count.

Route 2 is translating `mystery`.

```asm
  cmp   w0, #0x61        ; compare w0 with 'a' (0x61)
  b.lt  ret              ; if w0 < 'a', skip and return it unchanged
  cmp   w0, #0x7a        ; compare with 'z' (0x7a)
  b.gt  ret              ; if w0 > 'z', skip
  sub   w0, w0, #0x20    ; if it is in 'a'..'z', subtract 0x20 -> uppercase
  ret
```

In C:

```c
int mystery(int c) {
    if (c >= 'a' && c <= 'z')   // cmp 'a' + b.lt, cmp 'z' + b.gt
        c -= 0x20;              // sub 0x20: lower case to upper case
    return c;
}
```

This is a hand-written `toupper`. If the character is lower case it becomes upper case (the 0x20 difference in ASCII), otherwise it is left alone. You recognize it from three landmarks. 0x61 is `'a'`, 0x7a is `'z'`, and subtracting 0x20 is the upper/lower case flip from Lesson 1.1.

</details>

## Key takeaways
ARM is RISC, with simple fixed-length instructions, arithmetic only on registers, and memory access has to go through `ldr`/`str`. The registers are `x0..x30` (64 bit) and `w0..w30` (low 32 bits), with parameters in `x0..x7` and the return in `x0`.

`bl` saves the return address into `lr` (x30) instead of pushing to the stack like `call`, so non-leaf functions must save lr to the stack in the prologue (`stp x29, x30, [sp,...]`). For a quick mapping, `mov`/`ldr`/`str` handle data, `add`/`sub`/`cmp` handle arithmetic, and `b`/`b.eq`/`cbz`/`bl`/`ret` handle branching and calls. ARM32 has ARM and Thumb modes mixed together, so watch out for the disassembler guessing the wrong mode.
