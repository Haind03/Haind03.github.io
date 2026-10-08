---
title: "Lesson 1.3: x86/x64 Assembly (1), registers and common instructions"
image:
  path: /assets/img/covers/re-1-3-x86-x64-assembly-1-registers-instructions.webp
  alt: "Lesson 1.3: x86/x64 Assembly (1), registers and common instructions"
date: 2022-02-22 09:00:00 +0700
categories: ["Reverse Engineering", "Part 01 · Computer Fundamentals for RE"]
tags: [reverse-engineering, assembly, windows-internals]
render_with_liquid: false
---
Many people are scared of assembly because they think they have to memorize hundreds of instructions. You don't. Most of the time you only run into about twenty of them over and over. Learn those and you can read most code. This lesson covers them.

## Registers

The CPU doesn't compute directly on RAM. It copies data into small, very fast memory cells inside itself called registers, works on it there, then writes it back. So understanding registers is half of assembly.

On x64 there are 16 general purpose registers, each 64 bits:

```
rax rbx rcx rdx rsi rdi rbp rsp
r8  r9  r10 r11 r12 r13 r14 r15
```

One thing that confuses beginners is that the same register has several names depending on the size you use. Take rax as an example:

```
rax  = 64 bit (the whole thing)
eax  = low 32 bits of rax
ax   = low 16 bits
al   = lowest 8 bits
```

So if you see `eax` and `rax` in the same function, it's one register, just a different number of bits. Same for `rbx/ebx/bx/bl`, `rcx/ecx/cx/cl`, and so on. For r8 to r15 it's `r8/r8d/r8w/r8b`.

A few registers have conventional roles. Remember them, reading code gets a lot faster:

| Register | Usual role |
|---|---|
| `rax` | A function's return value lives here. After a `call`, look at rax to see what the function returned |
| `rsp` | The top of the stack pointer (stack pointer). Don't overwrite it carelessly |
| `rbp` | The base pointer of the stack frame, used to reference local variables |
| `rip` | The instruction pointer, points to the next instruction to run. Can't be assigned directly |
| `rcx rdx r8 r9` | First 4 function parameters on Windows x64 |
| `rdi rsi rdx rcx r8 r9` | First 6 parameters on Linux/macOS x64 |

Parameter passing is covered in lesson [1.4](/posts/re-1-4-x86-x64-assembly-2-stack-frames/). For now just know that the return value is in rax and the parameters are in the registers above.

There's also the flags register (RFLAGS). You don't read it directly, you see it through the jump instructions. The important flags are ZF (zero flag, set when the result is 0), SF (sign flag, negative), CF (carry) and OF (overflow).

## Syntax: Intel vs AT&T

There are two ways to write assembly and you can tell them apart quickly. Intel (IDA, x64dbg, Windows) writes `mov eax, 5` to mean eax = 5, destination first. AT&T (GDB default, Linux) writes `mov $5, %eax`, with `%` before registers, `$` before numbers, and the destination last.

This series uses Intel because it's close to the Windows tools we use a lot. In GDB, type `set disassembly-flavor intel` to switch and save yourself a headache.

## The instructions you must know

### mov, lea: moving data

```asm
mov eax, 5          ; eax = 5
mov eax, ebx        ; eax = ebx
mov eax, [rbx]      ; eax = the value at address rbx (square brackets = memory access)
mov [rbx], eax      ; write eax to address rbx
```

The square brackets `[...]` matter. With brackets it's a memory access at that address, without brackets it's the value itself. If you mix these up you'll misread the whole function.

`lea` (load effective address) also confuses beginners:

```asm
lea rax, [rbx+rcx*4+8]   ; rax = rbx + rcx*4 + 8, does NOT access memory
```

`lea` computes an address and puts it in a register, but it doesn't read memory there. Compilers also use `lea` for plain math (multiply, add) because it's compact. So when you see `lea`, don't assume it's an address, often it's just arithmetic.

### add, sub, inc, dec: arithmetic

```asm
add eax, 10     ; eax += 10
sub eax, ebx    ; eax -= ebx
inc eax         ; eax++
dec eax         ; eax--
imul eax, 3     ; eax *= 3 (signed)
```

### xor, and, or, shl, shr: bits

```asm
xor eax, eax    ; eax = 0  (classic trick: xor with itself = 0, shorter than mov eax,0)
and eax, 0xFF   ; keep the lowest byte
or  eax, 1      ; set bit 0
shl eax, 2      ; shift left 2 = multiply by 4
shr eax, 1      ; shift right 1 = divide by 2
```

`xor eax, eax` just means "set to 0". You'll see it at the start of functions all the time. If you don't recognize it, you might think something is being encrypted.

### cmp, test, and the jumps: this is if/else

This group matters most for reading logic. The CPU has no "if" instruction. It does two steps. First it compares and sets flags. `cmp a, b` computes a minus b only to set the flags (the result is not stored), so if a == b then ZF is set. `test a, b` ANDs a with b and sets the flags, and `test eax, eax` is how you check "is eax equal to 0". Second, it does a conditional jump based on the flags:

```asm
cmp eax, 10
je  somewhere      ; jump if eax == 10 (jump if equal)
jne somewhere      ; jump if eax != 10
jg  somewhere      ; jump if eax > 10 (signed)
jl  somewhere      ; jump if eax < 10 (signed)
ja  / jb           ; above / below (unsigned)
```

Remember that a `cmp`/`test` pair plus the `j*` right after it is one `if` statement in the source. Wherever you find the pair, you've found a branch. In a crackme, the `cmp` right before "Wrong password" gets printed is usually where the serial is compared.

`jmp` (unconditional) always jumps, like `goto`.

### call, ret: calling functions

```asm
call 0x401500   ; call the function at 0x401500
ret             ; return to the caller
```

`call` pushes the return address onto the stack and then jumps to the function. `ret` pops that address and goes back. After `call`, the return value is in rax.

### nop: does nothing

`nop` (no operation) does nothing at all. It sounds useless, but it's the first tool for patching. When you want to "delete" an annoying check without shifting other addresses, you overwrite it with `nop`. Lesson [17.1](/posts/re-17-1-patching-binaries-changing-one-byte-change/) uses it a lot.

## Reading a real snippet

Here's a simple check function, the kind you'd see in a crackme:

```asm
check_password:
    push rbp
    mov  rbp, rsp
    mov  eax, [rbp-4]      ; load a local variable (the length of the input string) into eax
    cmp  eax, 8            ; compare with 8
    jne  fail             ; if not 8, jump to fail
    mov  eax, 1            ; eax = 1 (correct)
    jmp  done
fail:
    xor  eax, eax         ; eax = 0 (wrong)
done:
    pop  rbp
    ret
```

Translating it back to C in your head:

```c
int check_password() {
    int len = ...;       // local variable at [rbp-4]
    if (len != 8)        // cmp + jne
        return 0;        // the fail branch
    return 1;
}
```

This function only checks whether the input string is exactly 8 characters. You just read assembly and turned it into logic. That's reversing. Get used to the `cmp`/`jne` pair and remember that rax is the return value, and that's most of it.

## Key takeaways
One register has several names by size, and `rax`(64)/`eax`(32)/`ax`(16)/`al`(8) are the same thing. rax is the return value and rsp is the top of the stack, with the first parameters in `rcx rdx r8 r9` on Windows and `rdi rsi rdx rcx r8 r9` on Linux. `[...]` means memory access while no brackets means the value itself, and `lea` computes an address or does arithmetic without reading memory. `xor eax, eax` means set to 0. A `cmp`/`test` pair plus `j*` is one `if` statement, which is how you read logic.
