---
title: "Lesson 1.3: ELF, GOT, PLT, and Lazy Binding"
image:
  path: /assets/img/covers/pwn-1-3-elf-got-plt-lazy-binding.webp
  alt: "ELF, GOT, PLT, and Lazy Binding"
date: 2022-10-25 20:37:00 +0700
categories: ["Binary Exploitation", "Pwn · Foundations"]
tags: [pwn, elf, got, plt]
render_with_liquid: false
---

This lesson takes the ELF file apart just far enough for pwn. You will learn the difference between a section and a segment, how dynamic linking works, and above all how the GOT and PLT work together. You will use both tables later, to leak libc addresses and as overwrite targets.

![ELF, GOT, PLT, and Lazy Binding](/assets/img/pwn/pwn-1-3-elf-got-plt-lazy-binding.svg)
_A libc call goes through the PLT stub and the GOT entry; the first call is resolved by ld.so._

**Prerequisites:** Lesson 1.2, and Lesson 0.3 (memory layout, section vs segment already mentioned briefly).

**Tools:** gcc, readelf, objdump, gdb + pwndbg, pwntools (ELF class).

## Goals

After this lesson you can tell a section (the linker's view) from a segment (the loader's view), explain why the binary does not contain the address of printf, describe how the PLT and GOT cooperate to call a libc function, and explain why the GOT is the classic target for both leaks (part 6) and overwrites (part 8).

## 1. Theory

### What ELF is

ELF (Executable and Linkable Format) is the format of executables, shared libraries, and object files on Linux. When you run `gcc -o a.out`, the `a.out` is an ELF file. It has a header that describes the file, then two parallel ways of organizing the content, by section and by segment.

### Section vs segment: two views of one file

Lesson 0.3 hinted at this. Here it is stated clearly.

A section is a unit for the linker and for build time. Each section groups one kind of content: `.text` (code), `.data` (initialized globals), `.bss` (zero-initialized globals), `.rodata` (constants), `.plt`, `.got`, `.symtab` (the symbol table), and so on. The section table is needed for linking and debugging, but it is not required at run time. A stripped binary still runs fine.

A segment (also called a program header) is a unit for the loader at run time. The loader does not care about section names. It only reads the program headers to learn which part of the file to take, which virtual address to map it to, and with which rwx permissions. Several sections with the same permissions are merged into one segment. For example `.text` and `.rodata`, which are both non-writable, can share a read-only or read-execute segment.

To remember it, a section belongs to build time (linker) and a segment belongs to run time (loader). Use `readelf -S` to see sections and `readelf -l` to see segments.

### Dynamic linking: why the binary does not contain printf

Your C program calls `printf`, but the code of `printf` lives in `libc.so.6`, not in your binary. That is the point of a shared library, since many programs share one copy of libc, which saves memory and makes updates easy. So at build time the compiler does not know where `printf` will be at run time, because libc is loaded into the mmap region at a randomized address (ASLR, Lesson 0.3).

The problem is how your code can call a function whose address is unknown at build time. The solution is a layer of indirection made of two tables, the PLT and the GOT. You will hear these two names throughout your pwn career, so it is worth understanding them well.

### GOT: the table of real function addresses

The GOT (Global Offset Table) is a table of pointers in the data area of the binary (sections `.got` and `.got.plt`, writable). Every external library function the binary uses has one entry in the GOT. Once resolved, that entry holds the real address of the function in libc.

The key point for pwn is that the GOT is writable. If you have an arbitrary write, you can change a GOT entry so that a call to `printf` jumps into `system` instead. That is a GOT overwrite (part 8). Because the GOT also holds real libc addresses, reading one entry leaks a libc address from which you compute the libc base (part 6). The GOT is both a door for reading and a door for writing.

### PLT: the bridge that calls through the GOT

The PLT (Procedure Linkage Table) sits in the code area (`.plt`, executable). Each external function has a small stub in the PLT. When your code calls `printf`, it actually executes `call printf@plt`, which jumps into the PLT stub of printf. The stub jumps indirectly through the matching GOT entry. In essence `printf@plt` is `jmp [printf@got]`.

The general flow when calling a libc function:

```
  your code                   PLT (.plt, r-x)          GOT (.got.plt, rw-)
  --------------              -----------------         ------------------
  call printf@plt  --------->  printf@plt:
                               jmp [printf@got]  ----->  [GOT entry of printf]
                                                          |
                                                          +--> real address
                                                               of printf in
                                                               libc (after resolve)
```

### Lazy binding: resolve on first use, not before

Resolving every function at startup would be slow, especially when the program only uses part of them. So by default Linux uses lazy binding. The real address of a function is looked up and written into the GOT on the FIRST CALL.

At first, the GOT entry of `printf` does not hold the real address of printf. It holds an address that points back into the PLT (a resolver stub). On the first call this happens:

```
  FIRST call of printf:
  call printf@plt
     -> jmp [printf@got]          ; GOT still points back to the PLT resolver stub
     -> push index of printf      ; the stub pushes the info
     -> jmp PLT[0] -> calls _dl_runtime_resolve (in ld.so)
     -> ld.so finds the real printf in libc, WRITES that address into [printf@got]
     -> then jumps into the real printf

  SECOND call onwards:
  call printf@plt
     -> jmp [printf@got]          ; GOT now holds the real printf address
     -> jumps straight into printf ; fast, no resolving again
```

Two practical consequences for pwn.

First, before the first call, the GOT entry of a function does not contain a libc address (it points back into the PLT). If you plan to leak libc by reading a GOT entry, read the entry of a function that HAS BEEN CALLED at least once (for example `puts` has usually been called already to print a banner). Reading an unresolved entry gives an address inside the binary, not libc, and the leak is useless.

Second, lazy binding can be turned off with Full RELRO (a mitigation, part 5). Then every GOT entry is resolved at startup and the GOT becomes read-only, which blocks GOT overwrite. When `checksec` reports `Full RELRO`, drop the idea of overwriting the GOT and change approach.

### Symbols: names attached to addresses

A symbol is a mapping between a name (`main`, `printf`, `win`) and an address or offset. The `.symtab` section holds the full symbols (removed when stripped), and `.dynsym` holds the dynamic symbols needed for dynamic linking (not stripped, because the loader needs them). For pwn, symbols let you look up a function address quickly.

- In pwntools, `elf.sym['win']` gives the address of the function `win`, `elf.got['puts']` gives the address of the GOT entry of puts, and `elf.plt['puts']` gives the PLT stub. You will type these three every day.
- If a binary is stripped of `.symtab`, you only have `.dynsym` (the external functions) and you must locate internal functions by reading the code.

## 2. Demo

### Sample program

```c
#include <stdio.h>
int main(void) {
    printf("call 1\n");
    printf("call 2\n");   // second call of printf
    return 0;
}
```

```bash
gcc -no-pie -o elfdemo elfdemo.c
```

I use `-no-pie` for fixed addresses that are easier to read. With a PIE binary everything is the same, you only add a base.

### Sections and segments

```bash
readelf -S elfdemo | grep -E "text|data|bss|got|plt|rodata"
# -> shows the sections: .text .rodata .plt .got .got.plt .data .bss ...
readelf -l elfdemo
# -> shows the segments (LOAD) with the Flg column: R E (read+execute), RW (read+write)
#    and the "Section to Segment mapping" lines show which section belongs to which segment
```

Look at the mapping at the end of `readelf -l` to see several sections merged into one segment by permission. That is the bridge between sections and segments, from theory to practice.

### Inspecting the PLT and GOT

```bash
objdump -d -M intel -j .plt elfdemo        # view the PLT stubs
objdump -R elfdemo                           # relocation table: each external function + its GOT entry
# example line: 0000000000404018 R_X86_64_JUMP_SLOT  printf@GLIBC_2.2.5
#               ^GOT entry address of printf  ^function
```

In the disassembly of `main` you will see the call is `call printf@plt` (an address inside `.plt`), not a direct call to printf. That is the indirection layer showing up.

### Watching lazy binding fill the GOT

This is the most valuable demo of the lesson. Watch the GOT entry of printf change value after the first call.

```bash
gdb -q ./elfdemo
pwndbg> break main
pwndbg> run
# Find the GOT entry address of printf (from objdump -R above, for example 0x404018):
pwndbg> x/gx 0x404018
#   BEFORE the first call: the value is an address inside .plt (pointing back to the resolver)
#   example: 0x404018: 0x0000000000401030   <- inside the binary, NOT libc yet
pwndbg> break printf
pwndbg> continue          # run to the first call of printf
pwndbg> finish            # run printf to the end so ld.so has time to resolve
pwndbg> x/gx 0x404018
#   AFTER the first call: the value is now the REAL printf address in libc
#   example: 0x404018: 0x00007ffff7e1cf00   <- inside the libc area (0x7fff...)
```

You just watched lazy binding. The GOT entry first points into the PLT, and after the first call it holds the real libc address. The number `0x7ffff7e1cf00` is what a libc-leak exploit goes looking for. With it, subtracting the offset of printf in libc gives the libc base.

### Reading the ELF with pwntools

```python
from pwn import *
e = ELF('./elfdemo')
print(hex(e.sym['main']))       # address of main
print(hex(e.plt['printf']))     # PLT stub of printf
print(hex(e.got['printf']))     # GOT entry of printf (leak target / overwrite target)
print(e.checksec)               # shows RELRO: Partial or Full
```

These three, `sym`, `plt`, and `got`, are the trio you use every day. `sym` gets a target function (like `win`), `got` is for leaking or overwriting, and `plt` is for calling an existing function again.

## 3. Lab

- Task: with `elfdemo`, locate the GOT entry of `printf` yourself, observe its value before and after the first call, and work out the offset of printf in libc.
- Goal: understand the PLT/GOT flow and lazy binding well enough to explain it to someone else.
- Hints, in steps:
  - Hint 1: use `objdump -R elfdemo` to get the GOT entry address of printf. In gdb, run `x/gx <address>` before and after `finish` of the first call.
  - Hint 2: after you have the real printf address (the GOT value afterwards), run `vmmap` to find the libc base, then compute `printf_real - libc_base`. Compare that number with the offset of printf in libc (use `readelf -s libc.so.6 | grep printf` or `nm -D`). Do they match?
  - Hint 3: rebuild with `-Wl,-z,relro,-z,now` (Full RELRO) and run `checksec`. Repeat the demo. Now the GOT entry of printf already holds the libc address at `break main` (early resolve), and the GOT area is read-only. Understand why Full RELRO kills GOT overwrite.
- Self-check, can you answer these three?
  - Which permissions do the PLT and the GOT have? (hint: PLT r-x, GOT rw- with Partial RELRO)
  - Why leak the GOT of a function that has been called, not one that has not?
  - How does Full RELRO block GOT overwrite?

## 4. Key takeaways

- A section is the linker's view at build time, and a segment is the loader's view at run time (merged by permission).
- libc functions are not inside the binary. They are called through the PLT + GOT indirection.
- The PLT (r-x) is a stub that jumps through the GOT, and the GOT (rw-) holds the real function address.
- Lazy binding fills a GOT entry with the real libc address only on the first call.
- The GOT is a LEAK target (read it to get a libc address) and an OVERWRITE target (write it to redirect a call).
- Full RELRO resolves early and makes the GOT read-only, which blocks GOT overwrite.
- In pwntools, `e.sym`, `e.plt`, and `e.got` are the daily trio.

## 5. Common pitfalls

- Leaking the GOT entry of a function that was never called and taking it for a libc address. Before the first call the entry points into the PLT (inside the binary), not libc. Leak a function that has run at least once.
- Mixing up the PLT address with the libc function address. `elf.plt['puts']` is a stub in the binary, while the real address of puts in libc must come from the GOT at run time. They are different things.
- Forgetting to check RELRO and wasting time building a GOT overwrite on a Full RELRO binary (the GOT is read-only, so writing crashes). Always run `checksec` first.
- Confusing sections with segments in tool output. `readelf -S` shows sections and `-l` shows segments. A stripped binary loses many sections but still runs thanks to its segments.
- Computing the libc base with the wrong offset (taking the offset from a different glibc version). As in Lesson 0.2, offsets depend on the libc version, so it must be the exact build.
- With a PIE binary, forgetting to add the base to addresses taken from `objdump` (those are offsets, not final addresses). pwntools handles this if you set `elf.address` after the leak.

## 6. Further reading

- "How the GNU C Library dynamic linker works", or Eli Bendersky's series "Position Independent Code (PIC)" and "Load-time relocation". They explain the PLT/GOT with diagrams and are well worth reading.
- `man ld.so` covers environment variables such as `LD_BIND_NOW=1` (force early resolve) and `LD_DEBUG=bindings` (print the resolve process, which is very clear when you run it).
- The ELF spec (System V ABI, ELF chapter), to look up section header and program header details.
- The pwntools ELF docs. Read `sym`, `got`, `plt`, and `address` carefully to prepare for parts 6 and 8.
