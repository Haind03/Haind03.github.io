---
title: "Lesson 10.2: Z3 and SMT for Crypto"
image:
  path: /assets/img/covers/crypto-10-2-z3-smt-crypto.webp
  alt: "Z3 and SMT for Crypto"
date: 2023-11-23 12:34:00 +0700
categories: ["Cryptography", "Crypto · Crypto in Practice"]
tags: [cryptography, z3, smt, prng]
render_with_liquid: false
---

Many crypto challenges do not need advanced math. They are a pile of constraints on bits and numbers, such as "find the seed so that the first three keystream bytes equal these values" or "find x and y satisfying this modular system". Z3 is an SMT solver. You describe the constraints in Python and it finds a solution. After this lesson you can model a custom cipher and a modular system in Z3, and use it to recover the seed of a home-made PRNG and get the flag.

![Recovering an xorshift seed with Z3](/assets/img/crypto/crypto-10-2-z3-smt-crypto.svg)
_Known plaintext gives keystream bytes, each byte becomes a Z3 constraint on the symbolic xorshift, and the model returns the seed._

Part 10 (Crypto in Practice) | Time: about 60 minutes | Difficulty: medium

**Prerequisites:** Lesson 1.1 (modular arithmetic), Lesson 3.1 (XOR), and Lessons 9.1 and 9.2 (PRNG, state recovery) are strongly recommended, since this lesson is another way to break a PRNG.

**Tools:** Python 3 + `z3-solver` (`pip install z3-solver`). This lesson ran on z3 4.13.

## Goals

By the end of this lesson you understand what an SMT solver is and when it is worth using instead of designing an algorithm yourself. You can choose the right variable type: `BitVec` for bit constraints, `Int` for integers and modular arithmetic. You can model a bit shift, an XOR and a modular system in Z3. You can use Z3 to recover the seed of a custom xorshift PRNG from known plaintext and solve for the flag.

## 1. Theory

### 1.1. SAT, SMT and Z3

A SAT solver decides whether there is an assignment of true/false to the boolean variables that makes a logical formula true. SMT (Satisfiability Modulo Theories) extends SAT. Instead of only boolean variables, it works directly with theories such as integers, reals, arrays and bit-vectors (fixed-length bit vectors). You write constraints in the language of the problem and the solver finds the solution.

Z3 is Microsoft Research's SMT solver, and it has a compact Python binding. The workflow is always three steps: create variables, add constraints (`add`), call `check()`. If it returns `sat` (satisfiable), read the solution from `model()`. If it returns `unsat`, there is no solution.

When does Z3 pay off in crypto CTFs? When the problem is "satisfy a pile of constraints" and not "invert a smooth function". Typical cases: recovering PRNG state from output, breaking a custom cipher made only of bit operations, solving modular systems, and finding an input that satisfies an odd constraint that is messy to write by hand.

Know one limit up front. Z3 does not break strong crypto. Do not throw RSA-2048 or AES at it. It is strong when the solution space is tightly constrained by linear or simple bit operations, and weak against heavy non-linearity such as large multiplication or well-diffusing S-boxes.

### 1.2. BitVec or Int, choosing correctly is half the work

Two variable types are used most:

- `BitVec("x", n)`: an n-bit integer. Operations wrap around modulo 2^n automatically, just like machine integers. Use it for anything involving bits: XOR, AND, left and right shifts, overflow. This is the type to use when modeling a PRNG or a cipher built from bit operations.
- `Int("x")`: a mathematical integer with no size limit. Use it for modular equations, inequalities and ordinary arithmetic.

Remember one trap right away. On a `BitVec`, Python's right shift `>>` is not a logical right shift. In Z3, `>>` on a BitVec is an arithmetic shift (it keeps the sign). To get an unsigned logical right shift, as `>>` does on unsigned numbers in C, you must use the function `LShR`. Mixing these up is the number one source of bugs when modeling a PRNG.

### 1.3. Modeling a custom cipher

The core idea is to rewrite the challenge's algorithm, replacing concrete values with Z3 variables. The original algorithm uses ordinary Python numbers, and the symbolic version uses BitVec. Then we feed in everything we know (for example, we know the plaintext starts with `flag{`, so we know the first keystream bytes) and ask Z3 to find the secret (the seed).

The key is known plaintext. If `ct = pt XOR keystream` and we know `pt` at some positions, we know the `keystream` there. The keystream is generated from the seed by a formula, so this gives constraints tight enough to pin down the seed.

## 2. Demo

### 2.1. Warm-up: solving a modular system

Before breaking a PRNG, get used to the syntax with a two-unknown system modulo a prime. Given the system (p = 1000003):

```
7x + 3y ≡ 346631 (mod p)
2x + 5y ≡ 274794 (mod p)
```

```python
# modeq.py - solve a modular system of equations with Z3
from z3 import Int, Solver, sat

p = 1000003
s = Solver()
x, y = Int("x"), Int("y")
s.add(x >= 0, x < p, y >= 0, y < p)      # bound the solution domain
s.add((7*x + 3*y) % p == 346631)
s.add((2*x + 5*y) % p == 274794)
print(s.check())
if s.check() == sat:
    m = s.model()
    print("x =", m[x], " y =", m[y])
```

Output:

```
sat
x = 31337  y = 42424
```

This system can be solved by hand too (invert a 2x2 matrix mod p), but the point is that we do not need to. Describe the constraints correctly and Z3 does the rest. When the system gets larger or has extra constraints such as "x lies in the printable byte range", solving by hand gets hard and Z3 shows its value.

### 2.2. Main lab: breaking a custom xorshift PRNG

This is a very common kind of challenge. The task gives a home-made stream cipher whose keystream comes from a 32-bit xorshift PRNG with a secret seed. The flag is XORed with the keystream. We only know that the flag starts with `flag{`. The job is to recover the seed and decrypt everything.

The PRNG and cipher (this is the challenge, used to generate the ciphertext):

```python
# gen.py - generate the custom-PRNG stream cipher challenge
MASK = 0xFFFFFFFF

def xorshift32(x):
    x ^= (x << 13) & MASK
    x ^= (x >> 17)
    x ^= (x << 5) & MASK
    return x & MASK

def encrypt(pt, seed):
    state = seed
    out = bytearray()
    for b in pt:
        state = xorshift32(state)
        ks = (state >> 24) & 0xFF      # take the high byte of state as the keystream byte
        out.append(b ^ ks)
    return bytes(out)
```

Running with `seed = 0xC0FFEE42` gives this ciphertext (hex):

```
fd15bc05ba11cf45476d6fd97c0b8c73c800eb2fea47975deac898e478b7d783f432f07befca0f
```

Now the interesting part. We do not have the seed. But we know the first 5 plaintext bytes are `flag{`, so we know the first 5 keystream bytes. Each keystream byte is the high byte of `state` after one xorshift step. We write a symbolic version of xorshift and let Z3 find the seed:

```python
# solve.py - use Z3 to recover the seed, then decrypt everything
from z3 import BitVec, BitVecVal, LShR, Solver, sat

MASK = 0xFFFFFFFF

def xorshift32(x):                         # real version, to rebuild the keystream once we have the seed
    x ^= (x << 13) & MASK
    x ^= (x >> 17)
    x ^= (x << 5) & MASK
    return x & MASK

def decrypt(ct, seed):
    state = seed
    out = bytearray()
    for b in ct:
        state = xorshift32(state)
        out.append(b ^ ((state >> 24) & 0xFF))
    return bytes(out)

def xorshift32_sym(x):                     # symbolic version: identical, but uses LShR for the right shift
    x = x ^ (x << 13)
    x = x ^ LShR(x, 17)                     # do NOT use >> (arithmetic shift) here
    x = x ^ (x << 5)
    return x

def recover_seed(ct, known_prefix):
    s = Solver()
    seed = BitVec("seed", 32)
    state = seed
    for i, pt_byte in enumerate(known_prefix):
        state = xorshift32_sym(state)
        ks = pt_byte ^ ct[i]               # keystream byte derived from the known plaintext
        s.add(LShR(state, 24) == BitVecVal(ks, 32))
    assert s.check() == sat, "seed not found"
    return s.model()[seed].as_long()

ct = bytes.fromhex("fd15bc05ba11cf45476d6fd97c0b8c73c800eb2fea47975deac898e478b7d783f432f07befca0f")
seed = recover_seed(ct, b"flag{")
print("seed found    :", hex(seed))
print("flag          :", decrypt(ct, seed).decode())
```

Output:

```
seed found    : 0xc0ffee42
flag          : flag{z3_cr4ck5_cu5t0m_prng_1n_0ne_sh0t}
```

With only 5 bytes of known plaintext, which is 40 bits of information constraining a 32-bit seed, Z3 pins down the exact seed `0xC0FFEE42` almost instantly. Then we rebuild the keystream and decrypt the part of the flag we did not know. We never had to invert xorshift by hand (that can be done but is messy). We only had to describe each step correctly.

Two points to take from this. First, the symbolic version must follow the original operation by operation, especially `LShR` for the unsigned right shift. Second, you need enough constraints for the solution to be unique. If you give only 1 byte of known plaintext (8 bits) for a 32-bit seed, Z3 may return a different seed that also satisfies the constraints, and the decrypted flag will be wrong. Give enough leading bytes to fix the solution.

## 3. Lab

- Task: `gen.py` generates the ciphertext (already provided in `ct.hex`), and `solve.py` is the Z3 solver. Run `python3 solve.py` from the lab directory. You should see the seed `0xc0ffee42` and the flag `flag{z3_cr4ck5_cu5t0m_prng_1n_0ne_sh0t}`.
- Variant to practice: change `gen.py` so that the keystream is the low byte `state & 0xFF` instead of the high byte, change the seed, and then edit `solve.py` to match. The goal is to understand which line of the model corresponds to which line of the real PRNG.
- Harder challenge: reduce the known plaintext to 1 byte, observe whether Z3 returns a different seed, and whether the decrypted flag is still correct. Then add the constraint "every plaintext byte must be printable" (`0x20 <= b < 0x7f`) to pin the correct solution again.
- Hints: (1) write the symbolic function by copying the real function and replacing `>>` with `LShR`; (2) remember that `(x << k)` on a BitVec wraps modulo 2^n by itself, so `& MASK` is not needed; (3) each known plaintext byte is a constraint `LShR(state, 24) == ks`.
- Done when: it prints the correct seed and a readable flag.

## 4. Key takeaways

- Z3 in three steps: create variables, `add` constraints, `check()`, then read `model()`.
- `BitVec` for bits (XOR, shifts, overflow), `Int` for modular and ordinary arithmetic.
- An unsigned right shift on a BitVec must use `LShR`, not `>>`.
- Breaking a PRNG with Z3: copy the algorithm, make the variables symbolic, and add known plaintext as constraints.
- Give enough constraints for a unique solution. With too few, Z3 returns a wrong solution and still says `sat`.
- Z3 is strong on bits and linear constraints, and cannot handle strong crypto (RSA, AES with all rounds).

## 5. Common pitfalls

- Using `>>` for a right shift on a BitVec and modeling it wrong without any warning. Z3 still runs and still says `sat`, but gives a wrong seed. Always use `LShR` for unsigned values.
- Forgetting to bound the domain with `Int`. A modular equation has many solutions, and without `0 <= x < p` Z3 returns a solution outside the range you want.
- Giving too few constraints. `sat` does not mean correct, only that a solution exists. That solution may not be the real seed if the problem is not tightly pinned.
- Throwing a problem that is too heavy at Z3 and waiting forever. If there is a multiplication of two large variables or a strongly diffusing S-box, Z3 will hang. That is a sign the problem does not suit Z3 and you should change approach.
- Calling `check()` many times wastes time. Each `s.check()` runs the solver again. Call it once, store the result, and then take the model.
- Forgetting `BitVecVal` when comparing a BitVec with a Python constant in some contexts. Z3 usually coerces the type, but write `BitVecVal(k, n)` explicitly to be safe when comparing against an n-bit BitVec.

## 6. Further reading

- The official Z3 Python tutorial on the Z3 site (the ericpony z3py-tutorial), especially the BitVec and solver parts.
- Lesson 9.2 in this series (recovering MT19937 and LCG): compare breaking a PRNG with algebra against breaking it with Z3, two routes to the same goal.
- The CryptoHack "Symmetric" section and some "Misc" challenges have custom cipher problems suited to practicing Z3.
- CTF writeups tagged "z3": search for "z3 ctf crypto writeup" to see many modeling styles, from breaking checksums to solving keygens.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 10.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/10.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/10.2/gen.py" download><i class="fa-solid fa-file-code"></i>gen.py</a>
<a class="lab-file" href="/assets/labs-crypto/10.2/modeq.py" download><i class="fa-solid fa-file-code"></i>modeq.py</a>
<a class="lab-file" href="/assets/labs-crypto/10.2/solve.py" download><i class="fa-solid fa-file-code"></i>solve.py</a>
</div>
</div>
