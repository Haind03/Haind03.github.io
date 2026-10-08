---
title: "Lesson 3.6: Writing a keygen"
image:
  path: /assets/img/covers/re-3-6-writing-keygen-when-fishing-out-serial.webp
  alt: "Lesson 3.6: Writing a keygen"
date: 2022-06-14 10:24:00 +0700
categories: ["Reverse Engineering", "Part 03 · C"]
tags: [reverse-engineering, c]
render_with_liquid: false
---
In lesson 3.5 you found the password of a crackme by fishing it out of memory. That works for simple checks, where the program keeps the correct serial somewhere and compares against it, and you peek at it during the comparison. A keygenme is harder.

A keygenme doesn't keep any serial ready-made. It computes the correct serial from the username at runtime, then compares it with what you typed. Each username gets a different serial. Fishing out one serial solves exactly one username, and often you're the one choosing the username anyway. To win this kind, you have to understand the algorithm well enough to generate a serial for any username yourself. What you write is called a keygen.

## Two kinds of crackme

Before touching anything, classify the target. Misjudging the type wastes time.

The first kind compares against a fixed serial. The code has a constant string, or a serial built independently of the username, then `strcmp`s it with what you typed. The validate function never reads the username, or reads it but doesn't use it to compute the serial. You attack it by fishing the serial out of memory (lesson 3.5) or patching the jump. Quick and easy.

The second kind is an algorithmic check (the keygenme). The validate function takes the username, runs it through some computation, gets the expected serial, then compares. Fishing out the serial still works but only for one username. Patching the jump unlocks the software on your machine but you have no general key. To make a keygen, you have to read that computation and rewrite it.

When you open the validate function, ask whether it uses the username to compute what it compares against. If yes, it's the second kind, and you'll be writing a keygen.

## The keygen workflow

Four steps, every time. First, locate the validate function by going from the "Correct"/"Wrong" strings via xref, as usual. Second, isolate the serial computation by reading how the username is transformed, whether accumulated, multiplied by weights, hashed, and how it's formatted into a string. Third, rewrite the algorithm in your own language. I use Python because it's fast and needs no build. Finally, cross-check. Run the keygen for a username, feed the serial into the keygenme, and you should see "Correct". If it's wrong, you misread a step, so go back to the second step.

## Dissecting the lab's keygenme

The lab's keygenme (`keygenme.c`) takes a `username` and a `serial`. Open it in Ghidra, go to `validate`, and the core is this loop (translated back to C so it's easier to read):

```c
static const uint16_t SEED[4] = { 0x1337, 0xBEEF, 0xCAFE, 0x5A5A };

for (int k = 0; k < 4; k++) {
    uint32_t acc = SEED[k];
    for (size_t i = 0; i < n; i++) {
        uint8_t c = user[i];
        acc += (c + 1) * (i + 1 + k);
    }
    blk[k] = acc & 0xFFFF;
}
```

Then those four 16-bit blocks are printed in hex with `"%04X%04X%04X%04X"`, which is the correct serial.

Two clues stand out in the disassembly. One is the four seed constants `0x1337, 0xBEEF, 0xCAFE, 0x5A5A`. Literal constants like these are almost always parameters of the algorithm, so seeing them tells you you're in the right place. The other is a nested loop going through each username character with a multiplication by index. That's the second kind, where the serial depends on both the content and the position of the characters.

This algorithm is symmetric on purpose. If you can compute it forward you can compute it again, there's no one-way function in the way. The keygen just repeats the formula.

## A keygen in under ten lines

```python
SEED = [0x1337, 0xBEEF, 0xCAFE, 0x5A5A]

def make_serial(user):
    blocks = []
    for k in range(4):
        acc = SEED[k]
        for i, ch in enumerate(user):
            acc += (ord(ch) + 1) * (i + 1 + k)
        blocks.append(acc & 0xFFFF)
    return "-".join(f"{b:04X}" for b in blocks)

print(make_serial("alice"))   # 193F-C6FA-D50C-666B
```

Run with the username `alice` it gives `193F-C6FA-D50C-666B`, and the keygenme says "Correct". Try `bob`, `RE_Learner`, or any other string and each gives a valid serial. You've reproduced the program's licensing logic.

The full writeup, including the cross-check results from actual runs, is in the lab section at the end of this post.

## When a keygen won't work

A keygen only works because the algorithm is symmetric. If validate uses a real one-way hash (SHA-256, say), computing the hash from the username is easy, but finding a serial whose hash matches leaves only brute force, which is infeasible. Commercial software often goes further and signs serials with an RSA digital signature. The binary contains only the public key for checking, while the private key for creating serials sits on the vendor's server. Even if you read the whole algorithm you can't generate a serial, because you don't have the secret key. Then you go back to patching (disabling the signature check), which is a different topic and belongs to Part 15 on anti-tamper.

Knowing this boundary matters more than the keygen itself. It tells you when to read the algorithm and when to switch to patching.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 3.6</b>Download the source files for this lab</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs/3.6.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs/3.6/keygen.py" download><i class="fa-solid fa-download"></i>keygen.py</a>
<a class="lab-file" href="/assets/labs/3.6/src/keygenme.c" download><i class="fa-solid fa-download"></i>src/keygenme.c</a>
</div>
</div>

The goal here goes beyond getting past one check, which is to understand the algorithm well enough to generate a valid serial for any username. The lab has the target program `keygenme.c`, which takes a `username` and a `serial` and prints "Correct!" if the serial is valid, plus `keygen.py`, a reference keygen that is the solution, so don't open it early. Build the target like this:

```
# Linux
gcc -O0 -no-pie -fno-stack-protector -o keygenme keygenme.c

# Windows (MinGW)
x86_64-w64-mingw32-gcc -O0 -o keygenme.exe keygenme.c

# Windows (MSVC Developer Prompt)
cl /Od keygenme.c
```

Try it with `./keygenme alice 0000-0000-0000-0000`, which reports "Wrong serial".

Open `keygenme` in IDA or Ghidra and find the `validate` function by going from the "Correct!" or "Wrong serial" string through an xref. Decide what kind of crackme this is, either a comparison against a fixed serial, or an algorithmic check that depends on the username, and why patching a single jump isn't enough if the goal is to generate serials. Work out how the right serial is computed from the username, including the formula, the seed constants and the string format. Then write your own keygen in any language that takes a username and prints a valid serial. To check it, run the keygen for your own username, paste the serial into `keygenme`, and you should see "Correct!".

Two questions to think about. If the algorithm used a real one-way hash such as SHA-256, could you still write a keygen, or would brute force be the only way? And why do real software vendors usually sign serials with a digital signature (RSA) instead of a symmetric formula like the one in this lab?

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Going from the "Correct!" string by xref takes you to `validate`. The serial is not compared against a fixed string. It's computed from the username and only then compared, so every username has a different correct serial. Patching a jump only gets you through one run and gives you no general key. To generate a serial for any username, you have to understand and recompute the algorithm.

The `validate` algorithm has three parts. First, `compute_blocks(user, blk)` computes four 16-bit blocks:

```
blk[k] = ( SEED[k] + sum_i( (user[i] + 1) * (i + 1 + k) ) ) & 0xFFFF
```

with `SEED = {0x1337, 0xBEEF, 0xCAFE, 0x5A5A}`. In the disassembly these four seed constants are easy to recognize, and the multiply-and-add loop walks through each username character. Second, the correct serial is formatted with `snprintf(..., "%04X%04X%04X%04X", blk0..blk3)`, that is, 16 uppercase hex digits. Third, `normalize_serial` strips all `-` and spaces, converts hex to uppercase, and then requires exactly 16 hex characters. That's why typing either `193F-C6FA-D50C-666B` or `193fc6fad50c666b` works.

The whole algorithm is symmetric and directly reversible. Recompute the formula and you get the serial, with no one-way function in the way. The keygen in `keygen.py` translates the formula directly:

```python
SEED = [0x1337, 0xBEEF, 0xCAFE, 0x5A5A]

def make_serial(user):
    blocks = []
    for k in range(4):
        acc = SEED[k]
        for i, ch in enumerate(user):
            acc += (ord(ch) + 1) * (i + 1 + k)
        blocks.append(acc & 0xFFFF)
    return "-".join(f"{b:04X}" for b in blocks)
```

I built it with `gcc -O0 -no-pie -fno-stack-protector`, generated serials and fed them back in, and these results come from real runs:

```
user=alice        serial=193F-C6FA-D50C-666B -> Correct! Valid serial for user 'alice'.
user=bob          serial=15A3-C291-CFD6-6068 -> Correct! Valid serial for user 'bob'.
user=RE_Learner   serial=2965-D8E6-E8BE-7BE3 -> Correct! Valid serial for user 'RE_Learner'.
user=x            serial=13B0-BFE1-CC69-5C3E -> Correct! Valid serial for user 'x'.

wrong serial check:
./keygenme alice 1111-2222-3333-4444 -> Wrong serial. Try again.
```

The keygen is valid for every username, and a made-up serial is rejected.

What to take from this is that fishing the serial out of memory only solves crackmes with a fixed comparison, while a keygenme forces you to understand the algorithm. Obvious seed constants (0x1337, 0xBEEF and so on) are a clear clue in the disassembly, so watch for them. A symmetric algorithm can be keygenned. If validate uses a real one-way hash or an RSA signature (with only the public key in the binary), you can't generate a serial by reversing it, which is why commercial software uses digital signatures.

</details>

## Key takeaways
Classify first by asking whether validate uses the username to compute what it compares against. If yes, it's a keygenme. Fishing out the serial and patching the jump only solve the fixed comparison type and give no general key.

To write a keygen, locate validate, isolate the serial computation, rewrite it, and cross-check by feeding in the generated serial. Obvious seed constants and a loop over each username character point to an algorithm that depends on the username. A symmetric algorithm can be keygenned, but a one-way hash or RSA signature can't, so switch to patching.
