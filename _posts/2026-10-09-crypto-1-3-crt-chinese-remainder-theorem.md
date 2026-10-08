---
title: "Lesson 1.3: CRT and the Chinese Remainder Theorem"
image:
  path: /assets/img/covers/crypto-1-3-crt-chinese-remainder-theorem.webp
  alt: "CRT and the Chinese Remainder Theorem"
date: 2026-10-09 09:15:00 +0700
categories: ["Cryptography", "Crypto · Math Foundations"]
tags: [cryptography, crt, rsa, hastad]
render_with_liquid: false
---

This lesson combines the solutions of several congruences into one, and uses the same technique to break RSA with a small exponent through the Hastad broadcast attack. After it you can apply CRT by hand, and you will see why a message sent to enough recipients with a small e is fully exposed.

![CRT and Hastad broadcast on RSA with e = 3](/assets/img/crypto/crypto-1-3-crt-chinese-remainder-theorem.svg)
_Three ciphertexts of the same m are merged by CRT into m^3, and an integer cube root returns m._

Part: 1 (Math Foundations) | Time: about 35 minutes | Difficulty: medium

**Prerequisites:** Lesson 1.1 (modular arithmetic, extended Euclid), Lesson 1.2 (primes, Euler).

**Tools:** Python 3, optionally SageMath (`CRT_list`), gmpy2, sympy.

## Goals

By the end of this lesson you can state CRT and its condition (pairwise coprime moduli), combine congruences both by substitution and with Gauss's formula, build the Hastad broadcast attack on RSA with e = 3, and avoid the integer cube root trap (never use floats).

## 1. Theory

### An old puzzle

There is an old puzzle: find x such that x leaves remainder 2 when divided by 3, remainder 3 when divided by 5, and remainder 2 when divided by 7. In congruence notation:

```
x ≡ 2 (mod 3)
x ≡ 3 (mod 5)
x ≡ 2 (mod 7)
```

The answer is x = 23. Check: 23 mod 3 = 2, 23 mod 5 = 3, 23 mod 7 = 2. All three hold. Every number of the form 23 + 105k also works (105 = 3*5*7). The solution is unique modulo 105.

### The CRT statement

The Chinese Remainder Theorem (CRT) says that if the moduli m1, m2, ..., mk are pairwise coprime (any two of them have gcd 1), then the system

```
x ≡ a1 (mod m1)
...
x ≡ ak (mod mk)
```

has a solution, and the solution is unique modulo M = m1 * m2 * ... * mk.

A deeper view is that Z_M is isomorphic to the product Z_m1 x Z_m2 x ... x Z_mk. A number in Z_M maps one-to-one to the tuple of its remainders modulo each mi. From the remainders you can rebuild the original number, and the other way around. This lets you split one large problem mod M into several small problems mod mi and then combine the answers.

### Combining by hand

I go slowly with two equations first, then extend. Combine `x ≡ 2 (mod 3)` and `x ≡ 3 (mod 5)`.

From the first equation every solution has the form `x = 2 + 3t`. Substitute into the second:

```
2 + 3t ≡ 3 (mod 5)
3t ≡ 1 (mod 5)
```

We need the inverse of 3 mod 5, and `3^{-1} mod 5 = 2` (because 3*2 = 6 ≡ 1). Multiply both sides by 2:

```
t ≡ 2 (mod 5)
```

Take t = 2 (the smallest solution), so `x = 2 + 3*2 = 8`. Check: 8 mod 3 = 2, 8 mod 5 = 3. Correct. The first two equations merge into `x ≡ 8 (mod 15)`.

Now combine with `x ≡ 2 (mod 7)`. Every solution has the form `x = 8 + 15s`, so:

```
8 + 15s ≡ 2 (mod 7)
15s ≡ -6 ≡ 1 (mod 7)
```

Since 15 ≡ 1 (mod 7), we get `s ≡ 1 (mod 7)`, and we take s = 1. Then `x = 8 + 15 = 23`, the original answer, and the solution is `x ≡ 23 (mod 105)`.

### Gauss's formula

Substitution is clear but long. Gauss gave a closed formula. Let M be the product of all mi. For each i let `Mi = M / mi` (the product of all moduli except mi) and `yi = Mi^{-1} mod mi`. Then:

```
x = (sum over i of ai * Mi * yi) mod M
```

Applied to the example: M = 105. For m1 = 3: M1 = 35, 35 mod 3 = 2, y1 = 2^{-1} mod 3 = 2. For m2 = 5: M2 = 21, 21 mod 5 = 1, y2 = 1. For m3 = 7: M3 = 15, 15 mod 7 = 1, y3 = 1. So:

```
x = (2*35*2 + 3*21*1 + 2*15*1) mod 105 = (140 + 63 + 30) mod 105 = 233 mod 105 = 23
```

We get 23 again. The formula needs modular inverses, which we covered in Lesson 1.1. Each term `ai * Mi * yi` is built to equal ai modulo mi and 0 modulo every other modulus, so after adding them each equation is satisfied on its own.

A note for moduli that are NOT coprime. The system can still have a solution, but only when the remainders are compatible (their difference is divisible by the gcd of the moduli involved). Then you combine with a more general extended Euclid, and the combined modulus is the lcm, not the product. This is rare in basic CTFs, so I do not go deeper. Just remember to check the coprime condition before using the formula above.

### Attack application: Hastad broadcast

Here CRT becomes an attack tool. The Hastad broadcast attack targets RSA with a small public exponent e, typically e = 3, when the same message m is sent to several recipients.

Suppose Alice sends the same message m (no padding, or fixed padding) to three people. Each has their own public key with different, pairwise coprime moduli n1, n2, n3, and all use e = 3. An eavesdropper captures three ciphertexts:

```
c1 = m^3 mod n1
c2 = m^3 mod n2
c3 = m^3 mod n3
```

Now treat `X = m^3` as the unknown. We have three congruences for X over three coprime moduli. CRT gives:

```
C ≡ m^3 (mod n1*n2*n3)
```

The key point is that m is smaller than each ni (m is a valid message, so m < ni), which means `m^3 < n1*n2*n3`. C is the solution in the range [0, n1*n2*n3), so the modulus never wraps it. C equals `m^3` exactly over the ordinary integers, not only as a congruence. Taking the integer cube root of C gives m.

Remember the conditions. You need at least e ciphertexts (3 recipients for e = 3), the same m, a small e, and no random padding. If any of these is missing, this classic attack does not work. This is why small e without padding is a dangerous combination, and why real RSA always uses random padding (OAEP), so that m^e is larger than n and the assumption "m^3 < product of moduli" breaks.

(CRT has another use in RSA, which is speeding up decryption. Instead of computing `c^d mod n`, the implementation computes separately mod p and mod q with exponents dp and dq, then combines with CRT, which is several times faster. If one of those computations suffers a hardware fault, it leaks a factor of n. That is the Bellcore-style fault attack. I only name it here.)

## 2. Demo

The plain Python below implements CRT and the integer cube root, then builds the full Hastad broadcast from scratch until the flag is recovered.

```python
# crt_hastad.py - CRT and Hastad broadcast attack (e=3)
from math import prod, gcd
import random

def crt(residues, moduli):
    # Combine the system x = residues[i] (mod moduli[i]), assuming pairwise coprime moduli.
    M = prod(moduli)
    x = 0
    for a, m in zip(residues, moduli):
        Mi = M // m
        x += a * Mi * pow(Mi, -1, m)   # Gauss formula, pow(.,-1,.) is the modular inverse
    return x % M, M

def icbrt(x):
    # Integer cube root by binary search (no floats, to avoid rounding errors).
    if x < 0:
        raise ValueError
    hi = 1
    while hi ** 3 <= x:
        hi *= 2
    lo = hi // 2
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid ** 3 <= x:
            lo = mid
        else:
            hi = mid - 1
    return lo

def is_prime(n):
    if n < 2: return False
    for p in (2,3,5,7,11,13,17,19,23,29,31,37):
        if n % p == 0: return n == p
    d, r = n - 1, 0
    while d % 2 == 0: d //= 2; r += 1
    for a in (2,3,5,7,11,13,17,19,23,29,31,37):
        x = pow(a, d, n)
        if x in (1, n - 1): continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1: break
        else:
            return False
    return True

def gen_prime(bits, rng):
    while True:
        p = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
        if is_prime(p): return p

def main():
    # Check CRT on the old puzzle: expect (23, 105)
    print("crt([2,3,2],[3,5,7]) =", crt([2, 3, 2], [3, 5, 7]))

    rng = random.Random(1337)   # fixed seed so the output is stable
    e = 3
    flag = b"FLAG{h4stad_br0adcast}"
    m = int.from_bytes(flag, "big")

    # Generate 3 moduli, each a product of 2 primes, pairwise coprime, each > m
    bits = (m.bit_length() // 2) + 16
    mods = []
    while len(mods) < 3:
        n = gen_prime(bits, rng) * gen_prime(bits, rng)
        if n > m and all(gcd(n, k) == 1 for k in mods):
            mods.append(n)

    cts = [pow(m, e, n) for n in mods]              # 3 ciphertexts of the same m
    print("m^3 < product of moduli ?", m ** 3 < prod(mods))

    C, _ = crt(cts, mods)                           # CRT merge: C = m^3 mod product
    print("C == m^3 ?", C == m ** 3)

    m_rec = icbrt(C)                                # integer cube root gives m
    recovered = m_rec.to_bytes((m_rec.bit_length() + 7) // 8, "big")
    print("Recovered:", recovered)

if __name__ == "__main__":
    main()
```

Output:

```
crt([2,3,2],[3,5,7]) = (23, 105)
m^3 < product of moduli ? True
C == m^3 ? True
Recovered: b'FLAG{h4stad_br0adcast}'
```

In the output, CRT solves the old puzzle correctly and returns (23, 105). In the Hastad part the condition `m^3 < product of moduli` holds, so after the CRT merge `C` equals `m^3` exactly over the integers (the line `C == m^3 ? True`), and its integer cube root returns the flag unchanged. The attacker never knows a factor of any modulus and never solves RSA in the usual sense. Only CRT and one cube root are used.

## 3. Lab

- Task: you captured a secret message broadcast with RSA e = 3 to three recipients. The data is three pairs `(n1, c1), (n2, c2), (n3, c3)`. Recover the plaintext and decode it to an ASCII flag. To practice, generate your own data: pick a flag, convert it to a number m, generate three coprime moduli that are each larger than m (as in the demo), and compute ci = m^3 mod ni.
- Files: none, build it from the description.
- Hints, in steps:
  - Hint 1: the three equations `ci ≡ m^3 (mod ni)` are a CRT system with unknown `X = m^3`.
  - Hint 2: combine with CRT to get C. Since m < each ni, we have `m^3 < n1*n2*n3`, so C = m^3 over the integers.
  - Hint 3: take the integer cube root of C (use your own `icbrt` or `gmpy2.iroot(C, 3)`). Do NOT use `C ** (1/3)`, because floats lose precision.
- Done when: you recover m and decode the flag.

## 4. Key takeaways

- CRT needs pairwise coprime moduli. Then the solution is unique modulo the product of the moduli.
- Combine by substitution or by Gauss's formula (which needs modular inverses).
- Hastad broadcast needs the same m, a small e, at least e recipients, and no random padding.
- When `m^e < product of moduli`, CRT gives exactly `m^e` over the integers, and you only take the e-th root.
- Random padding (OAEP) breaks the classic Hastad attack.

## 5. Common pitfalls

- Applying the CRT formula to non-coprime moduli without checking. The result is wrong and no error is raised. Always check gcd first.
- Taking the cube root with floats (`C ** (1/3)` or `pow(C, 1/3)`). For large numbers floats lose precision and the answer is wrong. Use an integer cube root (binary search or `gmpy2.iroot`).
- Too few ciphertexts. With e = 3 and only 2 recipients there are not enough constraints to rebuild the full m^3.
- Messages with different random padding for each recipient. They are no longer the same m, so classic Hastad fails (you need the generalized Hastad variant with polynomials, which is much harder).
- Treating the combined modulus as the product when the moduli are not coprime. In that case it is the lcm.

## 6. Further reading

- "An Introduction to Mathematical Cryptography" (Hoffstein, Pipher, Silverman), the CRT section.
- Dan Boneh, "Twenty Years of Attacks on the RSA Cryptosystem", the Hastad broadcast section, a classic survey.
- CryptoHack (cryptohack.org), the CRT and Hastad challenges in the RSA track.
- SageMath `CRT_list` and `sympy.ntheory.modular.crt`, to check your own implementation against.
