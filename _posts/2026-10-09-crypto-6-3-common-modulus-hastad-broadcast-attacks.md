---
title: "Lesson 6.3: Common Modulus and Hastad Broadcast Attacks"
image:
  path: /assets/img/covers/crypto-6-3-common-modulus-hastad-broadcast-attacks.webp
  alt: "Common Modulus and Hastad Broadcast Attacks"
date: 2026-10-09 14:15:00 +0700
categories: ["Cryptography", "Crypto · RSA"]
tags: [cryptography, rsa, hastad, crt]
render_with_liquid: false
---

Both attacks in this lesson appear when the same message is encrypted more than once. Common modulus is one m, one n and two different exponents e. Hastad broadcast is one m sent to several recipients, with the same small e and different n. Neither needs to factor n. They use pure algebra and tools you already have, the extended Euclidean algorithm and the Chinese Remainder Theorem (CRT).

![Common modulus and Hastad broadcast attack flows](/assets/img/crypto/crypto-6-3-common-modulus-hastad-broadcast-attacks.svg)
_Both attacks recover m from public values only._

Part: 6 (RSA) | Time: about 45 minutes | Difficulty: medium

**Prerequisites:** Lesson 6.1 (how RSA works), Lesson 1.1 (modular inverse, extended Euclid), Lesson 1.3 (CRT). This lesson uses CRT heavily, so review it if you are not comfortable.

**Tools:** Python 3 with gmpy2 and PyCryptodome. Install with `pip install gmpy2 pycryptodome`.

## Goals

After this lesson you can:

- Recover the plaintext when the same m is encrypted under the same n with two coprime exponents.
- Explain why sharing one n between two users is a bad idea even when each user keeps a separate d.
- Run the Hastad broadcast attack. Collect e ciphertexts of the same m under e moduli, combine them with CRT, then take the e-th root.
- Recognize the signs of each attack in a challenge statement.

## 1. Theory

### 1.1. Common modulus attack

Scenario: one message m is encrypted twice with the same modulus n but two different public exponents e1 and e2. We have:

```
c1 = m^e1 mod n
c2 = m^e2 mod n
```

If `gcd(e1, e2) = 1`, the extended Euclidean algorithm gives two integers a and b with `a*e1 + b*e2 = 1`. Then:

```
c1^a * c2^b = m^(a*e1) * m^(b*e2) = m^(a*e1 + b*e2) = m^1 = m  (mod n)
```

That gives m with no d and no factoring. There is one technical detail. One of a and b is negative (the sum is 1 while both e are large and positive). Raising to a negative power means you first take the modular inverse of the matching ciphertext, then raise it to the absolute value of the exponent.

This flaw exists because some systems put many users on one n to save work, with each user having their own pair (e, d). The designer assumed a separate d was enough. But if the same m reaches two users (the same announcement sent to two employees, for example), a third party who captures both ciphertexts reads m. It gets worse. Sharing n also lets each user factor n from their own pair (e, d) and then compute everyone else's d. The conclusion is to never share n.

### 1.2. Hastad broadcast attack

Scenario: the same message m is sent to e different recipients. All use the same small exponent e (classically e=3), and each has their own modulus n1, n2, n3. These moduli are pairwise coprime, which is almost always true for independently generated n. We capture:

```
c1 = m^3 mod n1
c2 = m^3 mod n2
c3 = m^3 mod n3
```

Let `M = m^3`. We know M mod n1, M mod n2 and M mod n3. CRT combines them into `M mod (n1*n2*n3)`. Since `m < ni` for every i, we have `m^3 < n1*n2*n3`, so the value CRT produces is `M = m^3` over the integers, with no wraparound. Taking the integer cube root gives m.

In general you need exactly e ciphertexts (or more) for e different recipients, so that the condition `m^e < product of the n` holds. For e=3 you need 3 copies, for e=5 you need 5, and so on.

This is the second reason a small e is dangerous (the first is the cube root in Lesson 6.2). Random padding breaks Hastad, because each ciphertext is then `(pad_i || m)^e` with a different pad, so the raw m is no longer the same. But deterministic padding (the same insertion pattern) can still be broken by the extended form of Hastad (the original, which uses polynomials).

### 1.3. Three questions to answer

1. What does the correct mechanism look like? Each user has their own key, each session has a different message, and the message has random padding. No shared n, and no small e without padding.
2. What goes wrong? A shared n opens the common modulus attack. Broadcasting the same m to many recipients with a small e opens Hastad.
3. How is it exploited? Common modulus uses extended Euclid and then multiplies the two ciphertexts. Hastad uses CRT to combine the ciphertexts and then takes the e-th root.

## 2. Demo

### 2.1. Common modulus attack

```python
# common_modulus.py: same n, two different e, recover m
import gmpy2
from Crypto.Util.number import getPrime, bytes_to_long, long_to_bytes

p, q = getPrime(512), getPrime(512)
n = p * q
m = bytes_to_long(b"CTF{common_modulus_wins}")

e1, e2 = 17, 65537
assert gmpy2.gcd(e1, e2) == 1          # required condition
c1 = pow(m, e1, n)
c2 = pow(m, e2, n)

# extended Euclid: find a, b such that a*e1 + b*e2 = 1
g, a, b = gmpy2.gcdext(e1, e2)
assert g == 1

def powmod_signed(base, exp, mod):
    # handle negative exponents: take the inverse, then raise to the absolute value
    if exp < 0:
        base = gmpy2.invert(base, mod)
        exp = -exp
    return pow(int(base), int(exp), int(mod))

m_rec = (powmod_signed(c1, a, n) * powmod_signed(c2, b, n)) % n
print(long_to_bytes(int(m_rec)))       # b'CTF{common_modulus_wins}'
```

Output:

```
b'CTF{common_modulus_wins}'
```

The key call is `gmpy2.gcdext(e1, e2)`, which returns `(g, a, b)` with `a*e1 + b*e2 = g`. Since the gcd is 1, the formula `c1^a * c2^b = m` holds. One of a and b is negative, so `powmod_signed` inverts that ciphertext before exponentiating. The whole attack uses only (n, e1, e2, c1, c2) and never needs either d.

### 2.2. Hastad broadcast attack

```python
# hastad.py: same m, same e=3, three different moduli
import gmpy2
from functools import reduce
from Crypto.Util.number import getPrime, bytes_to_long, long_to_bytes

e = 3
m = bytes_to_long(b"CTF{hastad_broadcast}")

mods, cs = [], []
for _ in range(e):                     # exactly e ciphertexts needed
    N = getPrime(512) * getPrime(512)
    mods.append(N)
    cs.append(pow(m, e, N))

def crt(residues, moduli):
    N = reduce(lambda x, y: x * y, moduli)
    total = 0
    for c, ni in zip(residues, moduli):
        Ni = N // ni
        total += c * Ni * int(gmpy2.invert(Ni, ni))
    return total % N

X = crt(cs, mods)                      # X = m^3 mod (n1*n2*n3) = m^3 that
root, exact = gmpy2.iroot(X, e)        # can bac ba nguyen
print("exact root?", exact)
print(long_to_bytes(int(root)))        # b'CTF{hastad_broadcast}'
```

Output:

```
exact root? True
b'CTF{hastad_broadcast}'
```

CRT merges the three congruences `m^3 mod ni` into `m^3 mod (n1*n2*n3)`. Because `m < ni`, `m^3` is smaller than the product of the three moduli, so the CRT value is `m^3` in full. The flag `exact = True` confirms it, and the cube root gives m. If you only have two ciphertexts (one short of e=3), CRT is not enough, `m^3` is still larger than `n1*n2`, and the root will not be exact.

## 3. Lab

- Task 1 (common modulus): you get `n`, `e1 = 3`, `e2 = 5`, `c1` and `c2` of the same flag. Recover the flag. Put the files in the Lab section below.
- Task 2 (Hastad): you get `e = 3` and three pairs `(n1, c1)`, `(n2, c2)`, `(n3, c3)` of the same flag. Recover the flag.
- Task 3 (trap variant): a Hastad challenge that gives only two ciphertexts with e=3. Try to solve it, explain why it fails, and say what is missing.
- Hints, in order: (1) common modulus needs `gcd(e1, e2) = 1`, so check that first; (2) handle the negative exponent with a modular inverse; (3) Hastad needs enough ciphertexts and pairwise coprime n, so check `gcd(ni, nj)` (if two n share a factor, that is a different gift, because you can factor them right away).
- Done when: you have the flags for tasks 1 and 2 and a correct explanation for task 3.
- Materialized lab: the Lab section below has a `solve.py` that runs both common modulus (e1=3, e2=5) and Hastad (e=3, three moduli), and a `transcript.txt` with the real output.

## 4. Key takeaways

- Common modulus means the same n and two e with `gcd(e1, e2) = 1`. Use extended Euclid, then `m = c1^a * c2^b mod n`.
- A negative exponent in the formula means taking the modular inverse of that ciphertext and then raising to the absolute value.
- Never let several users share one modulus n.
- Hastad needs the same m, the same small e, and at least e ciphertexts under different moduli. CRT combines them, then you take the e-th root.
- Random padding breaks both attacks because the raw m is no longer the same across ciphertexts.

## 5. Common pitfalls

- Forgetting to handle the negative coefficient in common modulus. `pow(c, -3, n)` does not behave like a positive exponent here, so invert the ciphertext first. Python 3.8 and later allow `pow(c, -1, n)`, but for a large negative exponent it is still clearer to invert and then exponentiate.
- Miscounting the Hastad ciphertexts. e=3 needs three copies, not two. With one missing, CRT does not cover enough and the cube root is wrong.
- Assuming the Hastad moduli are coprime without checking. If two moduli share a prime factor (`gcd(ni, nj) > 1`), CRT fails, but you have just factored both n. Always check the gcd of every pair first.
- Confusing Hastad with the cube root from Lesson 6.2. The cube root case has one n, one ciphertext and `m^3 < n`. Hastad has several n and several ciphertexts, where each `m^3 > ni` but the combined value is smaller than the product. Read the statement and count the moduli.
- Thinking common modulus needs d. It does not. Both d values stay secret, and we only need the two ciphertexts and the two public e.

## 6. Further reading

- Hastad, "Solving Simultaneous Modular Equations of Low Degree" (1988), the original paper, with the stronger polynomial version that also breaks linear padding.
- Boneh, "Twenty Years of Attacks on the RSA Cryptosystem" (1999), a short survey of all the classic attacks. Worth keeping at hand.
- CryptoHack, the "Modulus Inutilis" and "Everything is Still Big" challenges, for practice with small e and broadcast.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 6.3</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/6.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/6.3/solve.py" download><i class="fa-solid fa-file-code"></i>solve.py</a>
</div>
</div>
