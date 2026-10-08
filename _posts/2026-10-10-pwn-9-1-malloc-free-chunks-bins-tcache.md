---
title: "Lesson 9.1: How malloc and free Work, Chunks, Bins, Tcache"
image:
  path: /assets/img/covers/pwn-9-1-malloc-free-chunks-bins-tcache.webp
  alt: "How malloc and free Work, Chunks, Bins, Tcache"
date: 2026-10-10 17:05:00 +0700
categories: ["Binary Exploitation", "Pwn · Heap Basics"]
tags: [pwn, heap, tcache, glibc]
render_with_liquid: false
---

Before exploiting the heap you have to be able to see it. This lesson dissects the layout of a chunk (the memory block glibc allocates), the bins (lists of freed chunks), the life cycle of malloc and free, and shows all of it with real numbers on glibc 2.39. This is the foundation for every technique in Lessons 9.2 through 9.4.

![A chunk header, its tcache entry, and safe-linking XOR](/assets/img/pwn/pwn-9-1-malloc-free-chunks-bins-tcache.svg)
_A freed chunk's first 16 bytes become a tcache entry: next (obfuscated by safe-linking) and a random key._

**Prerequisites:** Lesson 0.3 (process memory model), Lesson 2.2 (basic gdb). Know pointers and hex numbers.

**Tools:** gcc, gdb (this lesson uses plain gdb and also shows the pwndbg equivalents), a small observation program provided in the Lab section below.

## Goals

By the end you can read a chunk header: the size field, the PREV_INUSE bit, prev_size, understand what tcache, fastbin, unsorted/small/large bin are for, describe what happens during one malloc and one free, observe the real heap layout with gdb and with a self-written dump program, and understand safe-linking: how the `fd` pointer inside tcache gets obfuscated (needed for 9.3).

## Theory

glibc does not call the kernel on every `malloc`. It asks the kernel for one large region (via `brk` or `mmap`) and then splits and manages it itself. That region is the heap. The unit of management is the chunk: every `malloc` returns the data area inside a chunk, and glibc places metadata (management data) right next to that data area. Understanding this metadata is the key to understanding how to break it.

### Chunk layout

An in-use (allocated) chunk is laid out like this on x86-64:

```
        +----------------------+  <- chunk pointer (0x10 below mem)
 0x00   |  prev_size (8 bytes) |   only used when the PREVIOUS chunk is free
 0x08   |  size (8 bytes)      |   chunk size | 3 flag bits in the low bits
        +----------------------+  <- "mem" pointer, what malloc RETURNS to you
 0x10   |  user data           |
        |  ...                 |
        +----------------------+
```

The pointer `malloc` returns (called `mem`) sits 0x10 bytes after the header. The `size` field does not only store the size: the three lowest bits are flags. The most important one is PREV_INUSE (value 0x1): if set, the previous chunk is currently in use. The other two are IS_MMAPPED (0x2) and NON_MAIN_ARENA (0x4).

Because the three low bits are flags, the chunk size is always a multiple of 8 (in practice a multiple of 16, due to alignment). `malloc(n)` returns a chunk of size equal to rounding `n + 8` up to the next multiple of 16, with a minimum of 0x20. For example `malloc(0x30)` gives a chunk of 0x40: add the 8-byte header, round up to 16.

A space-saving trick: when the next chunk does not need to know our `prev_size` (because we are still in use), those 8 bytes actually get borrowed by the current chunk as extra data. So `malloc(0x18)` still fits in a 0x20 chunk. This detail is not needed for this lesson, but it explains why the size thresholds look slightly off.

### Where a chunk goes when freed

`free` does not return memory to the kernel right away. It puts the chunk into a list for reuse, called a bin (bucket). glibc has several kinds of bins, chosen by size and by priority order:

- tcache (thread cache, since glibc 2.26): the fastest, a separate set per thread. It has 64 bins, each for one small size (from 0x20 to 0x410), each holding up to 7 chunks. This is where small chunks go first. Since Lessons 9.2 through 9.4 all use small chunks, tcache is the main character.
- fastbin: also for small chunks, a singly linked list with no immediate coalescing. A chunk goes to fastbin once the tcache bin for that size already has 7 entries.
- unsorted bin: a waystation. Large chunks (or ones that do not fit tcache/fastbin) go here on free, before being sorted into small/large bins on the next malloc.
- small bin and large bin: doubly linked lists for medium and large chunks, which coalesce adjacent chunks to fight fragmentation.

The point to remember for basic pwn: a small chunk (for example from `malloc(0x30)`) goes into tcache when freed. And tcache has two security features you must deal with in Lesson 9.3: safe-linking and the key. We look at both with real numbers below.

### How tcache links freed chunks

When a chunk enters tcache, the first 0x10 bytes of its data area (what used to be `mem`) get overwritten as tcache entry metadata, laid out like this.

```
 mem + 0x00 : next  (pointer to the next freed chunk in the same bin)
 mem + 0x08 : key   (used to detect double free)
```

tcache is a singly linked LIFO list (last in, first out): the most recently freed chunk sits at the head of the bin, and its `next` points to the chunk freed before it.

#### Safe-linking: the next pointer is obfuscated

Since glibc 2.32, the `next` pointer in tcache and fastbin is not stored raw, it is stored as an obfuscated (XOR'd) value, called safe-linking, using this formula.

```
PROTECT(pos, ptr) = (pos >> 12) XOR ptr
```

where `pos` is the address of the `next` slot itself (that is, the `mem` address of the chunk), and `ptr` is the pointer to store (the address of the next chunk, or NULL at the end of the list). The reverse operation, to get the real pointer back, works like this.

```
REVEAL(stored) = (pos >> 12) XOR stored
```

The idea: shift the address right by 12 bits to get the chunk's page, then XOR it in. An attacker who wants to write a forged address into `next` (Lesson 9.3) has to compute `PROTECT` themselves; writing the raw address is wrong. That is why many older exploits (written for glibc < 2.32) fail on Ubuntu 24.04.

A convenient side effect for an attacker: when the first chunk enters an empty bin, `next = NULL`, so `stored = (mem >> 12) XOR 0 = mem >> 12`. Reading this value tells you `mem >> 12`, which is almost a leak of the heap base. We exploit exactly this in 9.3 and 9.4 to leak heap addresses.

#### key: defending against double free

Since glibc 2.29, every chunk in tcache carries an extra `key` field at `mem + 0x08`. On free, glibc checks whether the chunk's `key` matches the current `tcache_key`; if it does, it suspects a double free and scans the bin, and if the chunk is already found there, it aborts with this message.

```
free(): double free detected in tcache 2
```

On glibc 2.34 and later, `tcache_key` is a random 64-bit value generated once per process, not a guessable pointer. So to double free into the same tcache, you have to overwrite `key` to a different value (Lesson 9.3 does this through a UAF).

### Life cycle: malloc and free

Shortened to the path for small chunks:

- malloc(n): computes the chunk size. If the matching tcache bin still has chunks (count > 0), it takes one straight from the head of the bin and updates `next` to be the new head. If tcache is empty, it looks in fastbin, unsorted, small, large, or carves one from the top chunk (the unused tail of the heap).
- free(p): computes the bin. If the tcache bin still has room (under 7), the chunk is placed at the head of the bin and `key` is set. If full, it falls through to fastbin/unsorted depending on size.

A subtle point Lesson 9.3 relies on: malloc only pulls from tcache when `counts[idx] > 0`. Once everything has been taken, count goes back to 0, and the next malloc no longer touches tcache even if the list still has pointers in it. This affects how many chunks you need to free when poisoning, covered in detail in 9.3.

## Demo

Test environment: Ubuntu 24.04.4 LTS, glibc 2.39-0ubuntu8.9, gcc 13.3.0, gdb 15.1. All numbers in this lesson are real output.

The observation program (source in the Lab section below) reads the header bytes and `fd` itself and prints them, so you can see the numbers without installing pwndbg. Build and run with ASLR off for stable numbers while learning, since safe-linking is identical whether ASLR is on or off.

```bash
cd labs/9.1 && ./build.sh
setarch -R ./heapview
```

The real output looks like this.

```
== just allocated chunks ==
a    mem=0x4052a0  prev_size=0  size_field=0x41  (chunk_size=0x40 PREV_INUSE=1)
b    mem=0x4052e0  prev_size=0  size_field=0x41  (chunk_size=0x40 PREV_INUSE=1)
c    mem=0x405320  prev_size=0  size_field=0x41  (chunk_size=0x40 PREV_INUSE=1)
```

Reading this: `malloc(0x30)` gives a chunk of size 0x40 (add the header, round to 16). `size_field = 0x41` is 0x40 plus the PREV_INUSE bit. The three chunks are exactly 0x40 apart. The first chunk sits at `0x4052a0`, which is heap_base (`0x405000`) plus 0x2a0; the first 0x290 bytes of the heap are the `tcache_perthread_struct` (the structure that manages the thread's tcache).

Next comes freeing and watching tcache.

```
== free(a) -> goes into tcache[0x40] (empty bin) ==
a.fd (obfuscated) = 0x405
a>>12             = 0x405   (== fd since next=NULL: PROTECT(a,0)=a>>12)
a.key             = 0xd0bc08f26109c69f   (tcache_key, used to detect double free)

== free(b) -> b becomes bin head, b.fd points at a (obfuscated) ==
b.fd (stored)     = 0x4056a5
PROTECT(b,a)      = 0x4056a5   (= (b>>12) XOR a)
REVEAL(b.fd)      = 0x4052a0   (= (b>>12) XOR b.fd -> real address of a)
real a            = 0x4052a0
```

Safe-linking in real numbers:

- Freeing `a` into an empty bin: `next = NULL`, so `a.fd = a >> 12 = 0x405`. Reading `fd` leaks the heap's page.
- `a.key` is a random 64-bit value, not a heap pointer.
- Freeing `b` right after: `b` becomes the bin head, `b.fd = PROTECT(b, a) = (b >> 12) XOR a = 0x4056a5`. Using `REVEAL(b.fd) = (b >> 12) XOR 0x4056a5` recovers exactly `0x4052a0`, the address of `a`.

You can check this yourself: with `b = 0x4052e0`, `b >> 12 = 0x405`, and `0x405 XOR 0x4052a0 = 0x4056a5`, it matches. When doing poisoning in 9.3 you will compute this same kind of value in reverse.

### Watching with plain gdb (no pwndbg)

The demo machine has no pwndbg installed, so we look at this with plain gdb. The script (also in the Lab section below) stops after each free and prints the following.

```bash
gdb -q -nx -x look.gdb ./heapview
```

Here is an excerpt of the real output.

```
=== header + fd + key of chunk a (a-0x10) ===
0x405290:	0x0000000000000000	0x0000000000000041
0x4052a0:	0x0000000000000405	0xd0bc08f26109c69f
=== heap region ===
            0x404000           0x405000     0x1000     0x3000  rw-p   .../heapview
            0x405000           0x426000    0x21000        0x0  rw-p   [heap]
```

`0x405290` is the header of chunk `a`: prev_size 0, size 0x41. `0x4052a0` is `mem`: the first qword is `fd` after free (0x405), the next one is `key`. `[heap]` starts right after the binary's rw segment.

Here are some useful gdb commands to explore yourself.

```
x/4gx (char*)a-16      # 4 qwords: prev_size, size, fd, key
info proc mappings     # see the heap region, libc
```

### If you have pwndbg or GEF

They give a much nicer picture. Here are the equivalent commands, for when your machine has them installed.

```
vis_heap_chunks        # draw a colored diagram of the chunks, marking each region
heap                   # list chunks on the heap
bins                   # show all bins: tcache, fastbin, unsorted, small, large
tcache                 # show tcache specifically, count per bin, chain already REVEALed
```

pwndbg even REVEALs the safe-linking pointer for you when displaying tcache, so you do not have to compute the XOR by hand.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 9.1</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-pwn/9.1.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-pwn/9.1/build.sh" download><i class="fa-solid fa-file-code"></i>build.sh</a>
<a class="lab-file" href="/assets/labs-pwn/9.1/src.c" download><i class="fa-solid fa-file-code"></i>src.c</a>
</div>
</div>

- Source files: provided in the Lab section below (an observation demo, no exploitation).
- Task: build, run, and answer the following yourself.
- Exercises, in order:
  - Change `malloc(0x30)` to `malloc(0x18)`, then `malloc(0x40)`. How does the chunk size change? Explain it with the "add 8, round to 16" rule.
  - Free chunks a, b, c in that order and draw out the tcache list (which one is the head, where does `next` point). Verify it with REVEAL.
  - Turn ASLR back on (run `./heapview` without `setarch -R`) several times. The `fd` of the first freed chunk changes every time, but does the relation `fd == mem >> 12` still hold?
- Self-check: can you explain why reading the `fd` of the first freed chunk almost always leaks the heap base?

## Key takeaways

- `malloc(n)` gives a chunk of size equal to rounding `n + 8` up to 16, minimum 0x20.
- `size_field = chunk_size | flags`; bit 0 is PREV_INUSE.
- Small chunks go into tcache first; each tcache bin holds up to 7 chunks.
- A tcache entry is `mem+0x00 = next` (obfuscated), `mem+0x08 = key`.
- Safe-linking: `stored = (mem >> 12) XOR next`; an empty bin gives `stored = mem >> 12`.
- malloc only pulls from tcache when `count > 0`.

## Common pitfalls

- Assuming `fd` stores a raw address. On glibc 2.32+ it is XOR'd by safe-linking. Always REVEAL before reading, always PROTECT before writing.
- Taking numbers from a different glibc version. The `tcache_perthread_struct` offset (0x290), the first chunk's position (0x2a0), bin behavior, all depend on the version. This lesson measures glibc 2.39; a different version must be re-measured.
- Confusing `mem` with the chunk address. `mem = chunk + 0x10`. The header sits at `mem - 0x10`, the size at `mem - 0x08`.
- Forgetting that `pos` in PROTECT is the `mem` address, not the chunk address. In tcache, the `next` slot sits right at `mem`, so `pos == mem`.

## Further reading

- sploitfun and Azeria Labs: walkthroughs of glibc malloc internals, chunks, bins.
- how2heap (shellphish): the `tcache_poisoning` and `tcache_house_of_spirit` files, worth running yourself.
- glibc source: `malloc/malloc.c`, look for `PROTECT_PTR`, `REVEAL_PTR`, `tcache_get`, `tcache_put`.
- Lesson 9.2 (use-after-free) and Lesson 9.3 (double free, tcache poisoning) use everything from this lesson directly.
