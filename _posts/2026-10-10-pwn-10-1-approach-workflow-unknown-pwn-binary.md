---
title: "Lesson 10.1: The approach workflow for an unknown pwn binary, from triage to exploit"
image:
  path: /assets/img/covers/pwn-10-1-approach-workflow-unknown-pwn-binary.webp
  alt: "The approach workflow for an unknown pwn binary, from triage to exploit"
date: 2026-10-10 18:05:00 +0700
categories: ["Binary Exploitation", "Pwn · Real-World Practice"]
tags: [pwn, ctf, methodology, triage]
render_with_liquid: false
---

The previous nine parts each taught one technique in isolation. This lesson teaches something harder. When you are handed an unfamiliar file with no hints, what do you do first, what do you do next, and how do you decide which technique applies. This is a route map, not a new trick. Once the workflow is memorized, every later challenge is just filling in details in boxes you already know.

![Decision tree from mitigations to exploitation technique](/assets/img/pwn/pwn-10-1-approach-workflow-unknown-pwn-binary.svg)
_Triage answers four questions in order: where does input go, what is the bug, what primitive does it give, and which technique does the active mitigation set force._

**Part:** 10 · **Reading time:** ~60 minutes · **Difficulty:** medium (synthesis)

**Prerequisites:** Parts 3 through 9. This lesson teaches no new technique, it chains together everything already covered.

**Tools:** file, checksec, strings, nm, objdump, gdb + pwndbg, ROPgadget, a decompiler (Ghidra or IDA), pwntools.

## Goals

After this lesson you will have a fixed triage routine so you never freeze in front of an unknown binary, be able to read the active mitigations and immediately see which exploitation paths remain, use a decision tree that maps "which mitigation" to "which technique", and know the correct order of operations: find the input, find the bug, identify the primitive, pick the technique, leak, exploit, stabilize.

## Theory

### Pwn is the problem of "which doors are still open"

Modern exploitation is almost never a single step. It is a chain: you have a bug, the bug gives you a primitive (a primitive capability such as reading something, writing something, or hijacking control flow), and the mitigations that are active decide which road turns that primitive into a shell. Beginners look at a binary and get overwhelmed because they try to invent "the exploit" immediately. Experienced people work sequentially: answer each small question in order until the path reveals itself.

There are four backbone questions, answered strictly in this order:

1. Where does the program take input, and where does that input land in memory?
2. Is there a bug, and what kind? (stack overflow, format string, use-after-free, off-by-one...)
3. What primitive does the bug give me? (control flow hijack, arbitrary read, arbitrary write, leak)
4. Given the active mitigations, which technique does that primitive lead to in order to get a shell?

The entire workflow below is just a systematic way to answer these four questions.

### Stage 0: triage (fast identification)

Triage (quick sorting, borrowed from medicine) is the first five minutes, done mechanically, always the same:

```bash
file ./chall              # 64-bit or 32-bit, static or dynamic, stripped or not
checksec --file=./chall   # RELRO, canary, NX, PIE: the mitigation map
strings -n 6 ./chall      # hint strings: "/bin/sh", "flag", a format "%s", function names
nm ./chall | grep -i 'win\|flag\|system\|backdoor'   # is there a ready-made "win" function
./chall                   # run it: what does it ask, what does it print, what are the menu choices
```

`file` and `checksec` alone eliminate more than half the possibilities. 64-bit versus 32-bit changes the calling convention (how arguments are passed, see Lesson 1.2). Static (statically linked, libc embedded straight into the binary) means you do not need to leak libc but gives you more gadgets, which suits ret2syscall (Lesson 6.3). Dynamic usually means you must leak libc (Lesson 6.2). Stripped (symbols removed) means you have to name functions yourself in the decompiler.

`strings` is a cheap gold mine: seeing `/bin/sh` means a ready-made path to a shell exists; seeing a lone format like `"%s"` is sometimes a sign of a format string bug; seeing `flag.txt` means the goal is reading a file, not necessarily a shell.

### Stage 1: identify the input and its flow

Run the program a few times, type junk, type long strings, type `%p %p %p`. Observe:

- What function reads the input? `gets`, `scanf("%s")`, `read(0, buf, N)`, `fgets`? Each has its own behavior (Lesson 1.4): `gets` has no limit, `read` takes raw bytes including nulls, `scanf("%s")` stops at whitespace.
- How many entry points are there? A menu with several choices is usually a heap challenge (allocate, edit, delete a note).
- Does long input crash it? Typing `%p.%p.%p` and getting back strange hex numbers is nearly always a format string bug.

### Stage 2: find the bug by reading decompiler output

Open Ghidra/IDA, find `main`, trace through to the function that handles input. This is the step where you read, not guess. Things to check:

- Buffer size versus the number of bytes read. `char buf[64]` with `read(0, buf, 256)` is an obvious overflow.
- Dangerous functions: `gets`, `strcpy`, `sprintf`, an unbounded `scanf("%s")`.
- `printf(buf)` instead of `printf("%s", buf)`: a format string bug.
- For heap challenges: is a pointer reused after `free` (use-after-free), is there a missing check on a negative or out-of-range index, is there a double `free`.
- Off-by-one: a loop using `<=` instead of `<`, or a null byte written one byte past the end.

Write down exactly which function and which line the bug is in, and how far it lets you read or write.

### Stage 3: from bug to primitive

Every bug maps to one or a few primitives. This is the step that translates "programming mistake" into "attacker capability":

| Bug | Primitive gained |
|---|---|
| Stack overflow | Control flow hijack (overwrite saved RIP), usually also a linear write on the stack |
| Format string `%p`/`%s` | Arbitrary read + leak (canary, libc, PIE base, stack) |
| Format string `%n` | Arbitrary write (write to an arbitrary address) |
| UAF / double free | Read/write into a freed chunk, leading to overlapping allocations, arbitrary alloc |
| Off-by-one on the heap | Corrupt the next chunk's size field, leading to overlap |

Once you have the primitive, the only remaining question is which mitigation blocks my path and how to go around it.

### Stage 4: the decision tree from mitigation to technique

After reading `checksec`, follow this tree. Read top to bottom, stop at the matching branch.

```
Is there a ready-made "win"/"flag" function (nm, decompiler)?
├─ Yes, and it needs no argument    -> ret2win                 (Lesson 3.2)
└─ Yes, but it needs an argument     -> pop rdi + ret2win       (Lesson 3.3)

No win function -> you must call a shell/syscall yourself from libc or from the binary.

NX (stack not executable)?
├─ OFF  (stack is executable)       -> ret2shellcode / jmp rsp  (Lesson 4.1, 4.2)
└─ ON   -> can't drop code in, must reuse existing code (ROP/ret2libc)

    Binary STATIC?
    ├─ Yes  -> ret2syscall: call execve directly via gadgets    (Lesson 6.3)
    └─ No (dynamic, needs libc):

        PIE (binary addresses randomized)?
        ├─ Yes  -> must leak the PIE base first (format string / GOT) (Lesson 5.3)
        └─ No (No PIE): binary addresses are fixed, easier.

        ASLR enabled (libc randomized)?
        ├─ No (rare)  -> ret2libc directly, libc address is known   (Lesson 6.1)
        └─ Yes        -> MUST leak libc first:
              - has puts/printf/write + GOT  -> leak via GOT      (Lesson 6.2)
              - has a format string           -> leak via %s/%p   (Lesson 7.1)
              then compute the base, ret2libc into system("/bin/sh") (Lesson 6.1)

Canary (a guard value placed before saved RIP)?
├─ OFF  -> overflow straight to saved RIP, no extra worry
└─ ON   -> must keep the canary intact:
      - canary leaked (format string, reading enough bytes) -> write it back exactly (Lesson 5.2)
      - a forking process keeps the same canary              -> brute force it byte by byte (Lesson 5.2)

RELRO?
├─ Full          -> GOT is not writable (GOT overwrite is off the table)
└─ Partial/none  -> GOT is still writable -> GOT overwrite is viable   (Lesson 8.1)
      combined with an arbitrary write (format string %n, or a heap primitive)
```

Two things to remember about this tree. First, the branches are not mutually exclusive: a real challenge often forces you down several branches at once (for example Lesson 10.3: canary is on so you must leak the canary, ASLR is on so you must leak libc, then you ret2libc). Second, leaking always comes before exploiting: almost every modern challenge splits into two phases, one to gather information (leak), and only then does phase two strike.

### Stage 5: leak, then exploit, then stabilize

- Leak: pick what to leak according to the tree above (canary, libc base, PIE base). Each leak is a runtime address, subtract the offset to get the base (Lesson 5.3).
- Exploit: build the final-stage payload with every address now known. A common snag is 16-byte alignment before `system` (insert one `ret`, Lesson 6.1).
- Stabilize: make the exploit run reliably multiple times, and run against the real remote server, not only locally. Most "works local, fails remote" failures come from using the wrong libc version. Get the server's exact libc (given with the challenge, or identified with a libc-database) and compute offsets against it.

## Demo: triaging the `guestbook` binary from Lesson 10.2

We apply the exact workflow to the real `guestbook` binary from Lesson 10.2 (built with its `build.sh`). We do not yet know what the challenge is about, we just run the routine.

Stage 0, triage:

```bash
$ file guestbook
guestbook: ELF 64-bit LSB executable, x86-64, dynamically linked, not stripped
$ checksec --file=guestbook
RELRO: Partial | Stack: No canary | NX: enabled | PIE: No PIE (0x400000)
$ nm guestbook | grep -iE 'win|flag|system'
# no win function -> must call a shell ourselves from libc
$ strings guestbook | grep -iE 'bin/sh|%s'
# no /bin/sh string in the binary -> /bin/sh will come from libc
```

Reading the mitigations and walking the tree gives no win function, NX enabled (shellcode is out), dynamic (need libc), No PIE (binary addresses fixed, no need to leak PIE), No canary (overflow straight to saved RIP), ASLR enabled (must leak libc). The matching branch: leak libc then ret2libc. Is there a `puts` to leak through the GOT?

```bash
$ nm guestbook | grep ' U puts'     # puts is an external function -> present in the PLT/GOT
```

There is a `puts`. So the plan is already clear from triage alone: stage one calls `puts(puts@got)` to leak libc, returns to `main`, stage two is ret2libc. Only now do we open the decompiler to confirm the bug:

Stages 1 through 3, read the code: the function `sign()` has `char name[64]` but `read(0, name, 256)`, an obvious overflow, the primitive is control flow hijack. Measure the offset with cyclic (or read `lea -0x40(%rbp)` in objdump, giving 0x40 + 8 = 72).

Stages 4 through 5: exactly the plan drawn up during triage. The full solution lives in Lesson 10.2 and the `exploit.py` of that lesson's Lab section, running against the real target with ASLR enabled.

The takeaway is that once the workflow is a habit, you can map out almost the entire plan after five minutes of triage, before the decompiler is even open. The decompiler is only there to confirm the plan and measure offsets.

## Lab

No new binary for this lesson. The lab is building the muscle memory of the workflow itself:

- Pull back three binaries you already solved in Parts 3, 6, and 7 (or any three picoCTF challenges). Erase the old solution from your head.
- For each binary, write down on paper (do not type an exploit yet): the `file`/`checksec` output, where the bug is, what the primitive is, which branch of the decision tree applies, and the leak and exploit plan.
- Compare the plan on paper with your old solution. Wherever they differ is where your workflow is still weak.
- Self-check: can you guess the correct technique from `checksec` plus a single read of `main`? If you need several wrong tries, the workflow is not yet a reflex.

## Key takeaways

- [ ] Always run `file`, `checksec`, `strings`, `nm`, and run the binary once: a fixed five-minute triage
- [ ] Answer the four questions: where is the input, what is the bug, what primitive does it give, which technique does the mitigation set force
- [ ] Read the code in a decompiler to confirm the bug, never guess
- [ ] Walk the decision tree: NX, PIE, ASLR, canary, RELRO, static or dynamic
- [ ] Leak first, exploit second: most challenges are two phases
- [ ] Stabilize: use the exact libc of the server, compute offsets dynamically

## Common pitfalls

- Jumping straight into writing an exploit before triage is done. Skipping `checksec` and then fumbling with a technique that does not match the mitigations. Always triage first.
- Computing the offset by eyeballing the buffer size. Always measure with cyclic or by reading objdump output (Lesson 3.2).
- Forgetting that leaking comes first. Trying to pack both leak and exploit into one payload before the base is known, which almost always fails (Lesson 6.2).
- Hardcoding your own machine's libc offsets. Works locally, fails on the remote. Identify the server's exact libc (Lesson 6.2, the libc-database toolset).
- Forgetting the 16-byte alignment before `system` (a `movaps` abort). Insert one `ret` (Lesson 6.1).
- Panicking at a long list of mitigations. Just walk the decision tree, each mitigation only adds one more leak step, it does not change the fundamentals.

## Further reading

- A technique map, each technique with its applicability conditions, for quick lookup while walking the decision tree.
- A tool reference and a cheatsheet with the commands and templates used at each stage.
- A list of documentation and practice grounds to drill this workflow on hundreds of real binaries.
- Next: Lesson 10.2 turns this exact workflow into a complete writeup.
- Stage references: triage and memory (Lesson 0.3, Lesson 2.3), bugs (Lesson 1.4), leaks (Lesson 5.3), techniques (Lesson 6.1, Lesson 6.2, Lesson 6.3, Lesson 7.1, Lesson 8.1).
