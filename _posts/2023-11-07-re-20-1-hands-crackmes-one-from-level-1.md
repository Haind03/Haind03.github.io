---
title: "Lesson 20.1: Hands-on with crackmes.one, from level 1 to level 4"
image:
  path: /assets/img/covers/re-20-1-hands-crackmes-one-from-level-1.webp
  alt: "Lesson 20.1: Hands-on with crackmes.one, from level 1 to level 4"
date: 2023-11-07 09:28:00 +0700
categories: ["Technique Reverse", "Part 20 · Real-World Practice"]
tags: [reverse-engineering, ctf]
render_with_liquid: false
---
After 19 parts, you have the tools and the theory. Now it's time to sit down and take apart real binaries until your hands know the moves. There's no better place to practice than crackmes.one: thousands of challenges made by the community for learning, sorted by difficulty, language and platform, completely legal to pick apart. This lesson shows you how to make use of that collection and gives sample writeups for four levels, each using a crackme I built myself representing the kind of challenge you'll meet.

## How to use crackmes.one

Go to crackmes.one and create an account (you need one to download files, and the password for extracting archives is always `crackmes.one`). The filters are your friend. Difficulty runs from 1 to 6, so start at 1 and don't skip ahead. Pick a high Quality to avoid sloppy challenges. For Language / Platform, filter for what you're currently learning, and if you're new, pick C/C++ on Windows or Linux.

Read the author's description before downloading, it usually says clearly what the goal is (find the password, write a keygen, or unpack). Solve in a VM following [Lesson 0.3](/posts/re-0-3-set-up-safe-lab-before-touching/). Most crackmes are harmless, but building the isolation habit from the start is good.

And most important: apply the loop from [Lesson 0.4](/posts/re-0-4-reverse-engineering-workflow-not-get-lost/). Triage, static, dynamic, notes. No challenge was ever beaten by opening IDA and scrolling aimlessly.

## Level 1: static reading gives it away, or patch one byte

The typical shape is that the program reads input and calls `strcmp` against a fixed string sitting right in the binary. No encryption, nothing.

Take `level1.c` as the example. The first step is always triage. Run `strings` before anything else:

```
$ strings -n 6 level1 | grep -i flag
letmein123
Correct! Flag: FLAG{level1_strings_win}
```

Done. The password `letmein123` is exposed right in strings, no disassembly needed. This is why `strings` is always the first command: a lot of level 1 crackmes die right here.

If you want to practice patching instead of finding the password, open a decompiler and find the comparison. In this binary:

```asm
1270:  call   strcmp
1275:  test   eax, eax
1277:  jne    128a          ; bytes: 75 11, jumps to the "Nope." branch
1279:  lea    rax, [rip+...] ; the "Correct!" branch
```

The `test eax,eax` + `jne` pair is the statement `if (strcmp(...) == 0)`. `strcmp` returns 0 on a match, `test` sets ZF, and `jne` jumps to the "Nope" branch when it does not match. To make the program always report success, disable the `jne` by overwriting `75 11` with `90 90` (two `nop` instructions) at file offset `0x1277`. After patching, any password still gives "Correct!". This is exactly the technique from [Lesson 17.1](/posts/re-17-1-patching-binaries-changing-one-byte-change/), and it was actually run and verified in the lab.

There are two roads and either one is fine: finding the password is understanding the challenge, patching is getting past it. Level 1 authors usually accept both.

## Level 2: transformed serial, needs inverting

One step up, the author doesn't leave the password bare anymore. They transform each character and then compare against a constant array embedded in the binary. `strings` is useless because the password doesn't exist as a string.

`level2.c` does it like this: `enc[i] = (pw[i] ^ 0x2A) + 3`, then compares `enc` against the `TARGET` array. When you read the decompiler you'll see a loop over the input, an `xor 0x2A`, a `+3`, and a comparison against a byte array. That array can be read right in `.rodata`:

```
TARGET = 5C 1C 4C 5B 1C 61 21 1B
```

With the transform and the result in hand, what's left is inverting. The forward operation is `xor` then `+3`, so the inverse is subtract 3 then `xor` again (xor is its own inverse, see [Lesson 1.1](/posts/re-1-1-reading-hexdump-like-text/)):

```python
TARGET = [0x5C,0x1C,0x4C,0x5B,0x1C,0x61,0x21,0x1B]
pw = ''.join(chr(((b - 3) & 0xFF) ^ 0x2A) for b in TARGET)
print(pw)   # s3cr3t42
```

It outputs `s3cr3t42`, and entering it into the crackme gives "Correct!". The key of level 2 is recognizing the chain of operations and reversing it. Most of it is just xor, add, sub, rotate, exactly what's in [Lesson 16.2](/posts/re-16-2-xor-rc4-custom-base64-three-youll/).

## Level 3: write a keygen

Level 3 is the line between someone who imitates and someone who understands. The serial is no longer fixed but depends on the username through an algorithm. Patching works, but the task asks for a keygen: generate a valid serial for any username, which means you have to understand and correctly reproduce the algorithm.

`level3.c` computes the serial from the username with a linear hash and then prints hex:

```c
acc = 0x1337;
for each ch in name:  acc = acc*33 + ch;
acc ^= 0xC0FFEE;
serial = "%08X" % (acc & 0xFFFFFFFF);
```

When reversing, you recognize the init constant `0x1337`, the multiplication by 33 (often seen in djb2-style hashes), and the final `xor 0xC0FFEE`. Copy the logic straight to Python and you have a keygen. There's no inversion needed because the hash is one-way but we only need to compute forward to generate the right serial for a username of our choice:

```python
def gen(name):
    acc = 0x1337
    for ch in name.encode():
        acc = (acc*33 + ch) & 0xFFFFFFFF
    return "%08X" % (acc ^ 0xC0FFEE)
```

Real check: `gen("reverser")` gives `F10E026B`, and entering the pair `reverser` / `F10E026B` into the crackme gives "Correct!". Change to another username and the keygen still produces a valid serial. This is exactly the mindset of [Lesson 3.6](/posts/re-3-6-writing-keygen-when-fishing-out-serial/).

When the check algorithm gets so tangled that inverting by hand is too exhausting (many cross constraints between characters), don't try to solve it by hand. Throw it at Z3 as in [Lesson 16.4](/posts/re-16-4-rewriting-algorithm-python-letting-z3-solve/), or angr as in [Lesson 18.3](/posts/re-18-3-symbolic-execution-making-computer-solve-crackme/). The solver finds an input meeting the conditions for you.

## Level 4: has anti-reverse, needs dynamic

At level 4, the challenge starts fighting back: a light anti-debug layer, strings that are encrypted and decrypted at runtime, sometimes packed with UPX. Static reading no longer gives it away because what you need only appears in memory at runtime.

There's no fixed sample file for this level because it's a combination, but the process is fixed. Start with more careful triage: if DIE says packed, unpack first ([Lesson 14.2](/posts/re-14-2-unpacking-upx-automatic-manual/)), since high entropy and a poor import table are signs. Then prepare a debugger that can survive anti-debug by turning on ScyllaHide in x64dbg ([Lesson 15.9](/posts/re-15-9-bypassing-anti-debug-from-mouse-click/)) to get past `IsDebuggerPresent`, PEB checks and timing. If there's an anti-debug TLS callback, enable breaking at the TLS callback ([Lesson 15.4](/posts/re-15-4-advanced-anti-debug-self-debug-tls/)).

Next, let the program decrypt itself and catch it on the spot. For encrypted strings, set a breakpoint after the decryption function and read the result in memory instead of decrypting by hand. When the anti-debug is too thick, drop the debugger and emulate the decryption piece with Unicorn ([Lesson 18.2](/posts/re-18-2-emulation-running-piece-code-without-whole/)): without a real debugger the whole series of anti-debug checks becomes useless.

The overall strategy for multiple anti layers is in [Lesson 15.10](/posts/re-15-10-when-several-anti-layers-are-stacked/). The core point is to peel each layer from the outside in, and switch to dynamic as soon as static gets blocked.

## Advice for improving fast

Go in order of difficulty, because jumping into level 4 before you're solid on level 2 just discourages you. Write a writeup for every challenge you solve. Writing it up forces you to really understand, and later you can look things up very quickly, and posting it on crackmes.one helps others too.

Set a time limit as well. If you're stuck on one for more than two evenings, read someone else's writeup, learn how they think, then come back to a similar challenge. And after finishing each language part, find a crackme in that language and do it, since theory only sticks when you take it apart yourself.

## Lab

The goal is to practice on real challenges and apply everything you've learned. The main task has two parts. In Part A, go to crackmes.one and create an account (you need one to download, and the archive password is always `crackmes.one`). Filter for Difficulty = 1, high Quality, Language = C/C++ and a Platform that fits your machine. Solve at least 3 level-1 challenges, then 3 level-2 ones, inside a VM, and write a writeup for each: what triage showed, where the check function is, how you solved it, and what the password or serial is. When your hands are steady, move up to level 3 (keygen) and then level 4 (with anti-reverse). Apply the loop from Lesson 0.4: triage, static, dynamic, notes.

Part B is three crackmes that come with the lab: `level1.c`, `level2.c` and `level3.c`, representing levels 1 to 3. Build them on Linux (or with MinGW on Windows):

```
gcc -O0 -o level1 level1.c
gcc -O0 -o level2 level2.c
gcc -O0 -o level3 level3.c
```

For level1 (tier 1), find the password or patch it. Running `strings level1 | grep -i flag` exposes the password right away, or you can open a decompiler, find `strcmp`, and patch the `jne` after `test eax,eax` into `nop nop` so the check always passes. For level2 (tier 2), the serial is transformed. `strings` doesn't show the password, so open a decompiler and recognize the loop that compares `(c ^ 0x2A) + 3` against the `TARGET` array in `.rodata`, then reverse it by subtracting 3 and XORing back to get the serial. For level3 (tier 3), write a keygen. Reverse the function that computes the serial from the username (a linear hash: multiply by 33, XOR with a constant, print 8 hex characters), copy the algorithm to Python (`keygen_level3.py`), and generate a serial for any username. Run `python3 keygen_level3.py <username>` and then enter the username/serial pair into level3.

For an extra challenge, try Z3 or angr on level3 instead of writing the keygen by hand, to get used to solver thinking for more complex challenges. You can also add an XOR layer to the "Correct!" string of one level yourself and practice solving it dynamically in a debugger. Do it yourself before opening the solution.

<div class="lab-box">
<div class="lab-head"><b>LAB 20.1</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/20.1/src/keygen_level3.py" download><i class="fa-solid fa-file-code"></i>src/keygen_level3.py</a>
<a class="lab-file" href="/assets/labs/20.1/src/level1.c" download><i class="fa-solid fa-file-code"></i>src/level1.c</a>
<a class="lab-file" href="/assets/labs/20.1/src/level2.c" download><i class="fa-solid fa-file-code"></i>src/level2.c</a>
<a class="lab-file" href="/assets/labs/20.1/src/level3.c" download><i class="fa-solid fa-file-code"></i>src/level3.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Everything was built with gcc on Linux.

For level1, the password is `letmein123`. The static way:

```
$ strings -n 6 level1 | grep -i flag
letmein123
Correct! Flag: FLAG{level1_strings_win}
```

The patching way: the disassembly around the check is

```asm
1270:  call   strcmp
1275:  test   eax, eax
1277:  jne    128a       ; bytes: 75 11
```

Overwrite `75 11` with `90 90` at file offset `0x1277`. I checked this: the patched build still prints `Correct! Flag: FLAG{level1_strings_win}` even with a wrong password.

For level2, the correct serial is `s3cr3t42`. The forward algorithm is `enc[i] = (pw[i] ^ 0x2A) + 3`, compared against

```
TARGET = 5C 1C 4C 5B 1C 61 21 1B
```

Reversing it:

```python
TARGET = [0x5C,0x1C,0x4C,0x5B,0x1C,0x61,0x21,0x1B]
print(''.join(chr(((b-3)&0xFF)^0x2A) for b in TARGET))  # s3cr3t42
```

Entering `s3cr3t42` gives `Correct! Flag: FLAG{level2_serial_math}`.

For level3, the algorithm that computes the serial from the username is:

```
acc = 0x1337
for ch in name:  acc = (acc*33 + ch) & 0xFFFFFFFF
acc ^= 0xC0FFEE
serial = "%08X" % acc
```

The keygen (`keygen_level3.py`) reproduces it exactly. The real test results: `reverser` gives serial `F10E026B` and `Correct! Valid serial. Flag: FLAG{level3_keygen_done}`; `alice` gives a valid serial and `Correct!`; and `reverser` with `DEADBEEF` (a made-up serial) gives `Nope.`.

The x64dbg and ScyllaHide steps at level 4 describe the standard procedure for Windows, and the techniques match lessons 14.2, 15.9 and 17.1.

</details>

## Key takeaways

`strings` is the first command, and level 1 often dies there. A `test`/`cmp` + `j*` pair is the branch point, so patch it to get past a check quickly. For a transformed serial, recognize the chain of operations and invert it (xor is its own inverse). A keygen means understanding and reproducing the algorithm, and when it gets tangled you use Z3 or angr.

When you meet anti-reverse, unpack first, turn on ScyllaHide, and switch to dynamic or emulation. Solve in order of difficulty, write writeups, and set time limits.
