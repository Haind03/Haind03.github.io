---
title: "Lesson 9.2: Recovering MT19937 State and Breaking LCG"
image:
  path: /assets/img/covers/crypto-9-2-recovering-mt19937-state-breaking-lcg.webp
  alt: "Recovering MT19937 State and Breaking LCG"
date: 2023-11-06 09:51:00 +0700
categories: ["Cryptography", "Crypto · Randomness"]
tags: [cryptography, mt19937, lcg, prng]
render_with_liquid: false
---

Lesson 9.1 said MT19937 is unsafe because "with enough output you can predict the rest". This lesson does exactly that, from start to finish. We invert the MT19937 temper step so that 624 consecutive outputs rebuild the full state, then clone the generator and predict every future number. After that we move to the LCG, a simpler generator, and recover all three secret parameters `a`, `c` and `m` from a sequence of outputs. All of it is working code, and none of it uses the victim's seed.

![Untemper 624 outputs and clone the generator](/assets/img/crypto/crypto-9-2-recovering-mt19937-state-breaking-lcg.svg)
_Untemper turns 624 outputs back into the state, and the LCG parameters fall out of differences between outputs._

Part 9 (Randomness) | Time: about 45 minutes | Difficulty: hard

**Prerequisites:** Lesson 9.1 (PRNG, MT19937, seed). Lesson 1.1 (modular inverse, for the LCG part). Bit operations (shift, xor, mask).

**Tools:** Python 3 (`random`, `math`, `functools` from the standard library).

## Goals

By the end of this lesson you understand the MT19937 temper step and why it is reversible. You can write an untemper function that inverts all four steps and rebuild the state from 624 outputs. You can clone the generator and predict the next number. You can recover the `a`, `c` and `m` of an LCG from its outputs. You can recognize challenge setups that give you enough output to recover the state.

## 1. Theory

### How MT19937 produces a number: the temper step

MT19937 keeps 624 words of 32 bits as its state. To produce an output it takes one state word `x` and passes it through a chain of four operations called temper, which mixes the bits so the output looks more even:

```
y = x
y = y ^ (y >> 11)
y = y ^ ((y << 7)  & 0x9D2C5680)
y = y ^ ((y << 15) & 0xEFC60000)
y = y ^ (y >> 18)
output = y
```

The key point for an attacker is that each of these operations is reversible. Every step has the form `y = y ^ (y shifted and masked)`, and it can be inverted by repeating the same expression enough times. So from `output` we can compute back to `x`, the original state word. This inversion is called untemper.

### Why `y = y ^ (y >> s)` is invertible

Take the right shift `y = y ^ (y >> s)`. The top bits are not affected by a right shift of themselves, so we can recover them first and then use them to recover the lower bits step by step. A compact way in code is to iterate `r = y ^ (r >> s)` a few times until it converges. For 32 bits, `32 // s + 1` iterations is always enough. A masked left shift works the same way in the other direction: `r = y ^ ((r << s) & mask)`.

The order of inversion must be the reverse of the temper order. Temper does `>>11`, `<<7`, `<<15`, `>>18`, so untemper does `>>18`, `<<15`, `<<7`, `>>11`.

### From untemper to clone

With 624 consecutive outputs, we untemper each one and get 624 state words. We load them into a fresh MT19937 as its state and set the read index to 624, so that the next call triggers the twist step that refreshes the array, exactly as the original did after using all 624 words. From then on the clone runs in lockstep with the victim, and every future output matches. We do not need the seed, only enough output.

In Python the state of a `random.Random` is read and written with `getstate`/`setstate`, in the format `(3, tuple of 624 state words + (index,), None)`.

### LCG: simpler, and also broken

An LCG (linear congruential generator) produces numbers with the formula:

```
X_{n+1} = (a * X_n + c) mod m
```

where `a` (multiplier), `c` (increment) and `m` (modulus) are the parameters and `X_0` is the seed. LCGs appear everywhere (glibc `rand()`, `java.util.Random`, and others). If the output is returned directly (no high bits cut off), we can recover all three parameters from a sequence of outputs, even knowing nothing in advance:

1. Find `m`. Let `t_i = s_{i+1} - s_i`. Then every expression `u_i = t_{i+1} * t_{i-1} - t_i^2` is a multiple of `m` (a short proof: expand with the LCG formula and every term is divisible by `m`). Take the `gcd` of a few `u_i` to get `m` (it may be off by a small factor, but with enough samples it usually gives exactly `m`).
2. Find `a`. From `s_2 - s_1 = a (s_1 - s_0) mod m` we get `a = (s_2 - s_1) * (s_1 - s_0)^{-1} mod m`, using the modular inverse from Lesson 1.1.
3. Find `c`. Substitute: `c = (s_1 - a * s_0) mod m`.

With all three, we can predict every following number.

## 2. Demo

The script below has two parts. The MT19937 part takes 624 outputs from a generator (system seed, which we never touch), untempers them, clones the generator, then predicts the next five numbers and compares. The LCG part takes a sequence from an LCG with secret parameters, recovers `a`, `c` and `m`, and predicts the next number.

```python
# mt_lcg.py: recover MT19937 from 624 outputs then predict, and break an LCG
import random
from math import gcd
from functools import reduce

# ---------- MT19937 ----------
def undo_rshift(y, s):
    r = y
    for _ in range(32 // s + 1):
        r = y ^ (r >> s)
    return r & 0xFFFFFFFF

def undo_lshift(y, s, mask):
    r = y
    for _ in range(32 // s + 1):
        r = y ^ ((r << s) & mask)
    return r & 0xFFFFFFFF

def untemper(y):                      # invert the 4 temper steps of MT19937
    y = undo_rshift(y, 18)
    y = undo_lshift(y, 15, 0xEFC60000)
    y = undo_lshift(y, 7, 0x9D2C5680)
    y = undo_rshift(y, 11)
    return y

victim = random.Random()              # system seed, which we do NOT know
outs = [victim.getrandbits(32) for _ in range(624)]   # observe 624 outputs
state = tuple(untemper(o) for o in outs)
clone = random.Random()
clone.setstate((3, state + (624,), None))             # load the state back

pred = [clone.getrandbits(32) for _ in range(5)]
real = [victim.getrandbits(32) for _ in range(5)]
print("MT19937 predicted:", pred)
print("MT19937 real     :", real)
print("match?", pred == real)

# ---------- LCG: X_{n+1} = (a*X_n + c) mod m ----------
def lcg(seed, a, c, m, n):
    x = seed; out = []
    for _ in range(n):
        x = (a * x + c) % m; out.append(x)
    return out

A, C, M, SEED = 1103515245, 12345, 2**31, 987654321   # secret
seq = lcg(SEED, A, C, M, 12)                           # we only have this sequence

diffs = [seq[i+1] - seq[i] for i in range(len(seq)-1)]
mults = [diffs[i+2]*diffs[i] - diffs[i+1]**2 for i in range(len(diffs)-2)]
m = reduce(gcd, [abs(x) for x in mults])               # m = gcd of the multiples of m
a = ((seq[2]-seq[1]) * pow(seq[1]-seq[0], -1, m)) % m   # a from the ratio of differences
c = (seq[1] - a*seq[0]) % m                             # c follows
print()
print("LCG recover (a,c,m):", (a, c, m))
print("LCG real    (a,c,m):", (A, C, M), "| match?", (a,c,m)==(A,C,M))
print("predicted next number:", (a*seq[-1]+c) % m, "| real:", lcg(SEED,A,C,M,13)[-1])
```

Running it gives this output (the MT part changes on every run because of the system seed, the LCG part is fixed because its parameters are fixed):

```
MT19937 predicted: [3669146054, 19416189, 2308367118, 2047324767, 3202878535]
MT19937 real     : [3669146054, 19416189, 2308367118, 2047324767, 3202878535]
match? True

LCG recover (a,c,m): (1103515245, 12345, 2147483648)
LCG real    (a,c,m): (1103515245, 12345, 2147483648) | match? True
predicted next number: 840622714 | real: 840622714
```

Reading the output: in the MT19937 part, the five predicted numbers match the five numbers the victim really produced, although we never knew the seed. 624 outputs are enough to rebuild the state. In the LCG part, we recover all three parameters correctly, `a = 1103515245`, `c = 12345` and `m = 2147483648` (these are glibc-style parameters), from only twelve numbers, and then predict the next number `840622714` correctly. The full lab with step-by-step comments and strict checks is in the Lab section below.

## 3. Lab

- Task: A service issues "lucky codes" using consecutive `random.getrandbits(32)` calls. It shows you some codes (at least 624) through a public API, and the next code is the winning code. Predict the winning code. Variant: the service uses an LCG and only shows a few outputs. Recover the parameters and predict.
- Files: a self-contained `solve.py` (`untemper`, `clone_mt`, `recover_lcg`) and `transcript.txt` with real output.
- Hints, step by step:
  1. Write `undo_rshift` and `undo_lshift` first and test each one: tempering and then untempering must give back the original number.
  2. Combine them into `untemper`, and remember to use the reverse order. Untemper 624 outputs into 624 state words.
  3. Load the state with `setstate` and set the index to 624. Predict and compare with the real output in a test environment.
  4. For the LCG: if the `gcd` gives a multiple of `m` instead of `m`, collect more output so the `gcd` converges. Be careful when `m` is not a power of 2.
- Done when: you predict the next MT19937 number from 624 outputs, and recover the LCG parameters from a sequence of outputs.

## 4. Key takeaways

- The MT19937 temper has four steps, all reversible, so it can be untempered.
- 624 consecutive outputs are enough to rebuild the full state and clone the generator.
- Invert `y = y ^ (y >> s)` by repeating the expression `32 // s + 1` times.
- Untemper must run in the reverse order of temper.
- An LCG leaks `a`, `c` and `m` from its outputs: `m` through the gcd of multiples, `a` through a ratio of differences, `c` by substitution.
- Defense: use a CSPRNG. Never let someone collect enough raw PRNG output and then trust the next output.

## 5. Common pitfalls

- Inverting the temper steps in the wrong order. It must be fully reversed, with `>>18` first and `>>11` last. A wrong order produces a garbage state.
- Forgetting the `& 0xFFFFFFFF` mask after each step, which lets numbers grow past 32 bits. Always cut to 32 bits.
- Not iterating enough times when inverting a shift. `32 // s + 1` is safe. Fewer iterations leave the low bits unconverged.
- For an LCG, assuming the output is the state. Many LCGs drop the low or high bits before returning (for example `java.util.Random` returns high bits). Then the simple gcd method fails and you need a lattice technique, which is harder.
- A `gcd` that gives a multiple of `m` instead of `m`. Collect a few more outputs so the gcd converges, or try dividing out small factors.
- Having fewer than 624 outputs for MT19937. Each missing word is a missing piece of the state, so you cannot clone. You need 624 consecutive outputs with no bits cut off.
- Outputs that are not `getrandbits(32)` but have been processed (for example by modulo, or turned into floats). Then each output is no longer a whole state word, and recovery has to be done differently.

## 6. Further reading

- Cryptopals Set 3, Challenge 23 (Clone an MT19937 RNG from its output), the standard exercise for the MT part.
- Cryptopals Set 3, Challenge 22 (Crack an MT19937 seed), to practice brute-forcing a time-based seed.
- "Reconstructing truncated integer variables satisfying linear congruences" (Frieze et al.), for the case of an LCG with truncated bits, using lattices.
- Lesson 10.2 (Z3 and SAT/SMT), if you want to solve more complex PRNG constraints with a solver.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 9.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/9.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/9.2/solve.py" download><i class="fa-solid fa-file-code"></i>solve.py</a>
</div>
</div>
