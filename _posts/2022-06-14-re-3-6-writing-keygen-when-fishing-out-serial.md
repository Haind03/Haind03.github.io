---
title: "Lesson 3.6: Writing a keygen, when fishing out the serial isn't enough"
image:
  path: /assets/img/covers/re-3-6-writing-keygen-when-fishing-out-serial.webp
  alt: "Lesson 3.6: Writing a keygen, when fishing out the serial isn't enough"
date: 2022-06-14 10:24:00 +0700
categories: ["Technique Reverse", "Part 03 · C"]
tags: [reverse-engineering, c]
render_with_liquid: false
---
In lesson 3.5 you found the password of a crackme by fishing it out of memory. That works for simple checks: the program keeps the correct serial somewhere and compares against it, and you just peek at it while it compares. But there's a more stubborn kind, and it's what separates beginners from people who really understand code: the keygenme.

A keygenme doesn't keep any serial ready-made. It computes the correct serial from the username right at runtime, then compares it with what you typed. Each username gets a different serial. Fishing out one serial only solves exactly one username, and often you're the one choosing the username anyway. To win this kind, you have to understand the algorithm deeply enough to generate a serial for any username yourself. What you write is called a keygen.

## Two kinds of crackme, two ways to attack

Before touching anything, classify the target. Misjudging the type is wasted effort.

The first kind compares against a fixed serial. The code has a constant string, or a serial built independently of the username, then `strcmp`s it with what you typed. The sign is that the validate function never reads the username, or reads it but doesn't use it to compute the serial. The way to attack is to fish the serial out of memory (lesson 3.5) or patch the jump to get past. Quick and neat.

The second kind is an algorithmic check (the keygenme). The validate function takes the username, runs it through a series of computations, gets the expected serial, then compares. Fishing out the serial still works but only for one username. Patching the jump "unlocks" the software on your machine but you have no general key. To make a keygen, you have to read and understand that computation and then rewrite it.

The deciding question when you open the validate function: does it use the username to compute what it compares against? If yes, it's the second kind, so get ready to write a keygen.

## The keygen workflow

There are four steps, every time. Locate the validate function by going from the "Correct"/"Wrong" strings via xref, as always. Then isolate the serial computation by reading how the username is transformed: accumulated, multiplied by weights, hashed, and how it's formatted into a string. Next, rewrite the algorithm in your own language, where Python is the natural choice because it's fast and needs no build. Finally, cross-check: run the keygen for a username, feed the serial into the keygenme, and you must see "Correct". If it's wrong, you misread a step, so go back to the second step.

## Dissecting the lab's keygenme

The lab's keygenme (`keygenme.c`) takes a `username` and a `serial`. Open it in Ghidra, go to `validate`, and you see its core is this loop (translated back to C so it's easier to look at):

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

Then those four 16-bit blocks are printed in hex: `"%04X%04X%04X%04X"`, which is the correct serial.

There are two clues you should catch right away in the disassembly. One is the four pretty seed constants `0x1337, 0xBEEF, 0xCAFE, 0x5A5A`. Literal constants like this jump out at you, and they're almost always parameters of the algorithm, so seeing them tells you you're in the right place. The other is a nested loop going through each username character with a multiplication by index. That's a clear sign of the second kind: the serial depends on both the content and the position of the characters.

This algorithm is deliberately symmetric, meaning if you can compute it forward you can compute it again, there's no one-way function blocking the way. The keygen just repeats the exact formula.

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

Run with the username `alice` it gives `193F-C6FA-D50C-666B`, feed it into the keygenme and it says "Correct". Try `bob`, `RE_Learner`, or any other string, and each gives a valid serial. That's the difference between "got through once" and "really understood": you just reproduced the program's licensing logic.

The full writeup, including the cross-check results actually run, is in the lab section at the end of this post.

## When a keygen is helpless

A keygen survives thanks to a symmetric algorithm. If validate uses a real one-way hash function (SHA-256, say): computing the hash from the username is easy, but finding a serial whose hash matches leaves only brute force, which is infeasible. Stronger still, commercial software often signs serials with an RSA digital signature: the binary contains only the public key for checking, while the private key for creating serials sits on the vendor's server. Even if you read the whole algorithm you can't generate a serial, because you lack the secret key. Then people go back to patching (disabling the signature check), and that's another game, belonging to Part 15 on anti-tamper.

Understanding this boundary matters more than the keygen itself: it tells you when to read the algorithm and when to switch to patching.

## Lab

The goal here goes beyond getting past one check: understand the algorithm well enough to generate a valid serial for any username. The lab consists of the target program `keygenme.c`, which takes a `username` and a `serial` and prints "Correct!" if the serial is valid, plus `keygen.py`, a reference keygen that is the solution, so don't open it early. Build the target like this:

```
# Linux
gcc -O0 -no-pie -fno-stack-protector -o keygenme keygenme.c

# Windows (MinGW)
x86_64-w64-mingw32-gcc -O0 -o keygenme.exe keygenme.c

# Windows (MSVC Developer Prompt)
cl /Od keygenme.c
```

Try it with `./keygenme alice 0000-0000-0000-0000`, which reports "Wrong serial".

Open `keygenme` in IDA or Ghidra and find the `validate` function by going from the "Correct!" or "Wrong serial" string through an xref. Decide what kind of crackme this is: a comparison against a fixed serial, or an algorithmic check that depends on the username, and why patching a single jump isn't enough if the goal is to generate serials. Work out how the right serial is computed from the username, including the formula, the seed constants and the string format. Then write your own keygen in any language that takes a username and prints a valid serial. To check it, run the keygen for your own username, paste the serial into `keygenme`, and you should see "Correct!".

Two questions are worth thinking about. If the algorithm used a real one-way hash such as SHA-256, could you still write a keygen, or would brute force be the only way? And why do real software vendors usually sign serials with a digital signature (RSA) instead of a symmetric formula like the one in this lab?

<div class="lab-box">
<div class="lab-head"><b>LAB 3.6</b>source files</div>
<div class="lab-files">
<a class="lab-file" href="/assets/labs/3.6/keygen.py" download><i class="fa-solid fa-file-code"></i>keygen.py</a>
<a class="lab-file" href="/assets/labs/3.6/src/keygenme.c" download><i class="fa-solid fa-file-code"></i>src/keygenme.c</a>
</div>
</div>

<details class="lab-solution" markdown="1">
<summary>Show solution</summary>

Going from the "Correct!" string by xref takes you to `validate`. The key point is that the serial is not compared against a fixed string. It is computed from the username and only then compared, which means every username has a different correct serial. Patching a jump only gets you through one run and gives you no general key. To generate a serial for any username, you have to understand and recompute the algorithm.

The `validate` algorithm has three parts. First, `compute_blocks(user, blk)` computes four 16-bit blocks:

```
blk[k] = ( SEED[k] + sum_i( (user[i] + 1) * (i + 1 + k) ) ) & 0xFFFF
```

with `SEED = {0x1337, 0xBEEF, 0xCAFE, 0x5A5A}`. In the disassembly these four seed constants are very easy to recognize (they are "pretty" literals), and the multiply-and-add loop walks through each username character. Second, the correct serial is formatted with `snprintf(..., "%04X%04X%04X%04X", blk0..blk3)`, that is, 16 uppercase hex digits. Third, `normalize_serial` strips all `-` and spaces, converts hex to uppercase, and then requires exactly 16 hex characters. That is why typing either `193F-C6FA-D50C-666B` or `193fc6fad50c666b` works.

The whole algorithm is symmetric and directly reversible: recompute the formula exactly and you get the serial, with no one-way function in the way. The keygen in `keygen.py` translates the formula directly:

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

Three lessons come out of this. Fishing the serial out of memory only solves crackmes with a fixed comparison, while a keygenme forces you to understand the algorithm. Pretty seed constants (0x1337, 0xBEEF and so on) are a glaring clue in the disassembly, so watch for them. And a symmetric algorithm can be keygenned. If validate uses a real one-way hash or an RSA signature (with only the public key in the binary), you can't generate a serial by reversing it, which is exactly why commercial software uses digital signatures.

</details>

## Key takeaways
Classify first: does validate use the username to compute what it compares against? If yes, it's a keygenme. Fishing out the serial and patching the jump only solve the fixed comparison type and give no general key.

To write a keygen, locate validate, isolate the serial computation, rewrite it, and cross-check by feeding in the generated serial. Pretty seed constants and a loop over each username character are signs of an algorithm that depends on the username. A symmetric algorithm can be keygenned, but a one-way hash or RSA signature can't, so switch to patching.
