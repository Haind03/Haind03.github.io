---
title: "Lesson 20.1: Hands-on with crackmes.one, from level 1 to level 4"
date: 2026-10-06 09:59:00 +0700
categories: ["Technique Reverse", "Part 20 · Real-World Practice"]
tags: [reverse-engineering, ctf]
render_with_liquid: false
---
After 19 parts, you have the tools and the theory. Now it's time to sit down and take apart real binaries until your hands know the moves. There's no better place to practice than crackmes.one: thousands of challenges made by the community for learning, sorted by difficulty, language and platform, completely legal to pick apart. This lesson shows you how to make use of that collection and gives sample writeups for four levels, each using a crackme I built myself (in `labs/20.1/`) representing the kind of challenge you'll meet.

## How to use crackmes.one

Go to crackmes.one and create an account (you need one to download files, and the password for extracting archives is always `crackmes.one`). The filters are your friend:

- **Difficulty** from 1 to 6. Start at 1, don't skip ahead.
- **Quality**: pick high to avoid sloppy challenges.
- **Language / Platform**: filter for what you're currently learning. If you're new, pick C/C++ on Windows or Linux.

Read the author's description before downloading, it usually says clearly what the goal is (find the password, write a keygen, or unpack). Solve in a VM following [Lesson 0.3](/posts/tr-0-3-dung-lab-an-toan/). Most crackmes are harmless, but building the isolation habit from the start is good.

And most important: apply the loop from [Lesson 0.4](/posts/tr-0-4-quy-trinh-reverse/). Triage, static, dynamic, notes. No challenge was ever beaten by opening IDA and scrolling aimlessly.

## Level 1: static reading gives it away, or patch one byte

Typical shape: the program reads input and calls `strcmp` against a fixed string sitting right in the binary. No encryption, nothing.

Take `labs/20.1/src/level1.c` as the example. The first step is always triage. Run `strings` before anything else:

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

The `test eax,eax` + `jne` pair is the statement `if (strcmp(...) == 0)`. `strcmp` returns 0 on a match, `test` sets ZF, and `jne` jumps to the "Nope" branch when it does NOT match. To make the program always report success, disable the `jne` by overwriting `75 11` with `90 90` (two `nop` instructions) at file offset `0x1277`. After patching, any password still gives "Correct!". This is exactly the technique from [Lesson 17.1](/posts/tr-17-1-patch-binary-jump-nop-codecave/), and it was actually run and verified in the lab.

Two roads, either one is fine: finding the password is understanding the challenge, patching is getting past it. Level 1 authors usually accept both.

## Level 2: transformed serial, needs inverting

One step up, the author doesn't leave the password bare anymore. They transform each character and then compare against a constant array embedded in the binary. `strings` is useless because the password doesn't exist as a string.

`labs/20.1/src/level2.c` does it like this: `enc[i] = (pw[i] ^ 0x2A) + 3`, then compares `enc` against the `TARGET` array. When you read the decompiler you'll see a loop over the input, an `xor 0x2A`, a `+3`, and a comparison against a byte array. That array can be read right in `.rodata`:

```
TARGET = 5C 1C 4C 5B 1C 61 21 1B
```

With the transform and the result in hand, what's left is inverting. The forward operation is `xor` then `+3`, so the inverse is subtract 3 then `xor` again (xor is its own inverse, see [Lesson 1.1](/posts/tr-1-1-hex-endian-bitwise/)):

```python
TARGET = [0x5C,0x1C,0x4C,0x5B,0x1C,0x61,0x21,0x1B]
pw = ''.join(chr(((b - 3) & 0xFF) ^ 0x2A) for b in TARGET)
print(pw)   # s3cr3t42
```

It outputs `s3cr3t42`, and entering it into the crackme gives "Correct!". The key of level 2 is recognizing the chain of operations and reversing it. Most of it is just xor, add, sub, rotate, exactly what's in [Lesson 16.2](/posts/tr-16-2-xor-rc4-base64-custom/).

## Level 3: write a keygen

Level 3 is the line between someone who imitates and someone who understands. The serial is no longer fixed but depends on the username through an algorithm. Patching works, but the task asks for a keygen: generate a valid serial for any username, which means you have to understand and correctly reproduce the algorithm.

`labs/20.1/src/level3.c` computes the serial from the username with a linear hash and then prints hex:

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

Real check: `gen("reverser")` gives `F10E026B`, and entering the pair `reverser` / `F10E026B` into the crackme gives "Correct!". Change to another username and the keygen still produces a valid serial. This is exactly the mindset of [Lesson 3.6](/posts/tr-3-6-lab-viet-keygen/).

When the check algorithm gets so tangled that inverting by hand is too exhausting (many cross constraints between characters), don't try to solve it by hand: throw it at **Z3** as in [Lesson 16.4](/posts/tr-16-4-viet-lai-python-z3/), or **angr** as in [Lesson 18.3](/posts/tr-18-3-symbolic-execution-angr-triton/). The solver finds an input meeting the conditions for you.

## Level 4: has anti-reverse, needs dynamic

At level 4, the challenge starts fighting back: a light anti-debug layer, strings that are encrypted and decrypted at runtime, sometimes packed with UPX. Static reading no longer gives it away because what you need only appears in memory at runtime.

There's no fixed sample file for this level because it's a combination, but the process is fixed:

1. **Triage more carefully.** If DIE says packed, unpack first ([Lesson 14.2](/posts/tr-14-2-unpack-upx-oep/)). High entropy and a poor import table are signs.
2. **Prepare a debugger that can survive anti-debug.** Turn on ScyllaHide in x64dbg ([Lesson 15.9](/posts/tr-15-9-bypass-scyllahide-titanhide/)) to get past `IsDebuggerPresent`, PEB checks, timing. If there's an anti-debug TLS callback, enable breaking at the TLS callback ([Lesson 15.4](/posts/tr-15-4-anti-debug-selfdebug-tls/)).
3. **Let the program decrypt itself and catch it on the spot.** For encrypted strings, set a breakpoint after the decryption function and read the result in memory instead of decrypting by hand.
4. **When the anti-debug is too thick, drop the debugger.** Emulate the decryption piece with Unicorn ([Lesson 18.2](/posts/tr-18-2-emulation-unicorn-qiling/)): without a real debugger the whole series of anti-debug checks becomes useless.

The overall strategy for multiple anti layers is in [Lesson 15.10](/posts/tr-15-10-chien-luoc-nhieu-lop-anti/). The core point: peel each layer from the outside in, and switch to dynamic as soon as static gets blocked.

## Advice for improving fast

- **Go in order of difficulty.** Jumping into level 4 before you're solid on level 2 just discourages you.
- **Write a writeup for every challenge you solve.** Writing it up forces you to really understand, and later you can look things up very quickly. Posting it on crackmes.one helps others too.
- **Set a time limit.** If you're stuck on one for more than two evenings, read someone else's writeup, learn how they think, then come back to a similar challenge.
- **After finishing each language part, find a crackme in that language and do it.** Theory only sticks when you take it apart yourself.

## Lab

In `labs/20.1/`:

- `src/level1.c`, `level2.c`, `level3.c`: three crackmes representing levels 1 to 3, build with gcc. The answers and solutions are in `solution.md`, but try on your own first.
- `src/keygen_level3.py`: a reference keygen for level3.
- Main task: create a crackmes.one account, solve in order starting from difficulty 1, and write a writeup for each.

Details in [labs/20.1/README.md](https://github.com/Haind03/Technique-Reverse/blob/main/labs/20.1/README.md).

## Key takeaways

- `strings` is the first command, level 1 often dies there.
- A `test`/`cmp` + `j*` pair is the branch point, patch it to get past a check quickly.
- For a transformed serial, recognize the chain of operations and invert it (xor is its own inverse).
- A keygen means understanding and reproducing the algorithm, and when it gets tangled use Z3/angr.
- When you meet anti-reverse, unpack first, turn on ScyllaHide, switch to dynamic or emulation.
- Solve in order of difficulty, write writeups, set time limits.
