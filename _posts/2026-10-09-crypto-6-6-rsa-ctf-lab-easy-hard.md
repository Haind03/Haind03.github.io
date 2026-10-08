---
title: "Lesson 6.6: RSA CTF Lab from Easy to Hard"
image:
  path: /assets/img/covers/crypto-6-6-rsa-ctf-lab-easy-hard.webp
  alt: "RSA CTF Lab from Easy to Hard"
date: 2023-09-07 12:21:00 +0700
categories: ["Cryptography", "Crypto · RSA"]
tags: [cryptography, rsa, ctf, rsactftool]
render_with_liquid: false
---

The previous five lessons gave you the individual attacks. This lesson is the practice range. We line up a set of RSA challenges from easy to hard, each tied to a flaw you have learned, and more importantly we build a workflow so that a set of parameters tells you what to try first. You will use two kinds of tools, RsaCtfTool for automatic scanning and SageMath for the attacks that need lattices, plus a complete sample solver script that dispatches across several attacks.

![RSA triage flow from parameters to attack](/assets/img/crypto/crypto-6-6-rsa-ctf-lab-easy-hard.svg)
_Read the numbers first, then pick the attack that matches the sign._

Part: 6 (RSA) | Time: about 90 minutes | Difficulty: hard

**Prerequisites:** all of Lessons 6.1 to 6.5. This is a capstone lesson with no new theory. It combines what you have learned.

**Tools:** Python 3 with gmpy2, PyCryptodome and sympy. RsaCtfTool (`git clone https://github.com/RsaCtfTool/RsaCtfTool`). SageMath. factordb (online).

## Goals

After this lesson you can:

- Use a checklist that classifies an RSA challenge by its parameter signs, so you know which attack to try first and do not waste time.
- Use RsaCtfTool, from raw n/e/c or from a PEM key file, and read its results.
- Tell when to drop the automatic tool and work by hand in SageMath.
- Keep a working multi-layer sample solver script that you can extend for real competitions.

## 1. Theory

### 1.1. The triage procedure

Before typing any command, look at the parameters and ask these questions in order:

1. Is n small (under 256 to 512 bits)? If so, check factordb and run `factorint`. If it factors, you are done.
2. Is e small (3, 5, 7)? If so, try the e-th root (one ciphertext), or Hastad if there are several moduli and several ciphertexts of the same m.
3. Is e unusually large (close to n)? If so, try Wiener (small d).
4. Are p and q close (`isqrt(n)^2` very near n, or the statement hints at it)? If so, Fermat.
5. Are there several n? If two n share a common divisor (`gcd(ni, nj) > 1`), factor both right away. If the same n has two e, use common modulus. If the same m goes out under several n with a small e, use Hastad.
6. Do you know part of the plaintext or part of p? Coppersmith (Sage `small_roots`).
7. Is there an oracle that says whether the padding is valid? Bleichenbacher.
8. No clear sign: run everything through RsaCtfTool, and check factordb in parallel.

A good habit is to print `n.bit_length()`, `e`, `e.bit_length()` and the `gcd` of every pair of n as soon as you receive the challenge. Half the answers sit in those numbers.

### 1.2. What RsaCtfTool is

RsaCtfTool is a general-purpose tool that bundles dozens of RSA attacks (factordb, Fermat, Wiener, Boneh-Durfee, Pollard p-1, ECM, common factor, small e, and more). It takes raw parameters or key files and tries them one by one. It is very handy in qualifying rounds, but it is a black box, so when it fails you still have to understand the problem yourself. Use it for fast scanning, not as a replacement for learning.

### 1.3. When you need SageMath

RsaCtfTool is strong on flaws that have a closed-form algorithm. Attacks that need a custom lattice (multivariate Coppersmith, unusual partial key forms, known high bits of both p and d, systems of modular equations) you have to build yourself in Sage. Sage provides `PolynomialRing`, `small_roots`, `LLL`, `matrix`, and big integers without friction. The rule is that standard flaws go to RsaCtfTool, and flaws that need thinking go to Sage.

## 2. Demo

### 2.1. The challenge set, ordered by difficulty

Below is the exercise map. Each entry lists the sign and the attack. Use it to generate your own practice challenges (or find matching problems on CryptoHack).

- Level 1 (warm-up): n around 256 bits, e=65537. Sign: small n. Attack: factordb or `factorint`.
- Level 2 (small e): e=3, short flag, large n. Sign: e=3 with no padding. Attack: cube root.
- Level 3 (Fermat): n of 2048 bits but `q = nextprime(p)`. Sign: p and q close. Attack: Fermat.
- Level 4 (common modulus): one n, two e, two c of the same m. Attack: extended Euclid (Lesson 6.3).
- Level 5 (Hastad): e=3, three (n, c) of the same m. Attack: CRT then cube root.
- Level 6 (Wiener): e close to n. Sign: unusually large e. Attack: continued fractions.
- Level 7 (shared prime): many keys, two n share one prime factor. Attack: `gcd(n1, n2)`.
- Level 8 (Coppersmith stereotyped): most of the plaintext is known. Attack: Sage `small_roots`.
- Level 9 (partial p): high bits of p known. Attack: Sage Coppersmith divisor finding.
- Level 10 (Bleichenbacher): a padding oracle is available. Attack: padding oracle attack (Lesson 6.5).

### 2.2. Using RsaCtfTool

From raw parameters:

```bash
# from n, e, c directly
python3 RsaCtfTool.py -n 0xC0FFEE... -e 65537 --uncipher 0xDEADBEEF...

# force a few specific attacks (faster than scanning all)
python3 RsaCtfTool.py -n <N> -e <E> --attack wiener,fermat,factordb --uncipher <C>

# list every available attack
python3 RsaCtfTool.py --list
```

From a public key file (common when the challenge gives you `pubkey.pem`):

```bash
# read n, e from a PEM file, try to recover the private key
python3 RsaCtfTool.py --publickey pubkey.pem --private

# decrypt a ciphertext file
python3 RsaCtfTool.py --publickey pubkey.pem --uncipherfile flag.enc
```

Reading the result, if it prints a private key (PEM) or an "unciphered data" line, you are done. If it runs for a while and reports that nothing was found, go back to the triage in section 1.1 and think by hand.

### 2.3. Using SageMath for lattice attacks

Sage is the home ground for Coppersmith. A minimal template for a stereotyped message (details in Lesson 6.4):

```python
# in sage
PR.<x> = PolynomialRing(Zmod(n))
f = (known + x)^e - c
f = f.monic()
print(f.small_roots(X=2**unknown_bits, beta=1.0, epsilon=0.05))
```

And for a shared prime between two keys, no lattice needed, only one line:

```python
# if two moduli share a prime factor
from math import gcd
p = gcd(n1, n2)
assert p != 1 and p != n1          # found the common factor
q1 = n1 // p
d1 = inverse_mod(e, (p-1)*(q1-1))
```

### 2.4. A complete multi-layer solver script

This script takes `(n, e, c)` and tries small e, Wiener and Fermat in turn. It is a frame you can extend with more layers (factordb, common modulus, Hastad) depending on the challenge. The `__main__` part tests itself with three cases generated on the spot.

```python
#!/usr/bin/env python3
# solve.py: layered RSA solver, tries the common attacks one by one
import gmpy2
from Crypto.Util.number import long_to_bytes, inverse

def fermat(n, max_steps=1_000_000):
    a = gmpy2.isqrt(n)
    if a * a < n:
        a += 1
    for _ in range(max_steps):
        b2 = a * a - n
        b, exact = gmpy2.iroot(b2, 2)
        if exact:
            return int(a - b), int(a + b)
        a += 1
    return None

def decrypt_with_pq(n, e, c, p, q):
    d = inverse(e, (p - 1) * (q - 1))
    return long_to_bytes(pow(c, d, n))

def small_e_root(n, e, c):
    # try c + k*n for small k, then take the e-th root
    for k in range(5000):
        r, exact = gmpy2.iroot(c + k * n, e)
        if exact:
            return long_to_bytes(int(r))
    return None

def cf_expansion(a, b):
    while b:
        q = a // b
        yield q
        a, b = b, a - q * b

def convergents(cf):
    n0, n1, d0, d1 = 0, 1, 1, 0
    for q in cf:
        num = q * n1 + n0
        den = q * d1 + d0
        yield num, den
        n0, n1, d0, d1 = n1, num, d1, den

def wiener(e, n):
    for k, d in convergents(cf_expansion(e, n)):
        if k == 0:
            continue
        if (e * d - 1) % k:
            continue
        phi = (e * d - 1) // k
        b = n - phi + 1
        disc = b * b - 4 * n
        if disc < 0:
            continue
        s, ok = gmpy2.iroot(disc, 2)
        if ok and (b + s) % 2 == 0:
            return int(d)
    return None

def solve(n, e, c):
    # 1) small e: e-th root (one ciphertext, small m^e)
    if e <= 7:
        r = small_e_root(n, e, c)
        if r:
            return ("small_e_root", r)
    # 2) Wiener: unusually large e -> small d
    if e.bit_length() > n.bit_length() - 10:
        d = wiener(e, n)
        if d:
            return ("wiener", long_to_bytes(pow(c, d, n)))
    # 3) Fermat: p, q close together
    fac = fermat(n, max_steps=200000)
    if fac:
        p, q = fac
        return ("fermat", decrypt_with_pq(n, e, c, p, q))
    return (None, None)

if __name__ == "__main__":
    from Crypto.Util.number import bytes_to_long, getPrime
    from sympy import nextprime
    # Ca A: small e = 3
    p, q = getPrime(512), getPrime(512); n = p * q; e = 3
    c = pow(bytes_to_long(b"FLAG{easy_small_e}"), e, n)
    print("A:", solve(n, e, c))
    # Case B: Fermat (p, q close together)
    p = nextprime(2**255); q = nextprime(p + 2**20); n = int(p * q); e = 65537
    c = pow(bytes_to_long(b"FLAG{fermat_me}"), e, n)
    print("B:", solve(n, e, c))
    # Case C: Wiener (small d)
    p, q = getPrime(512), getPrime(512); n = p * q; phi = (p - 1) * (q - 1)
    d = getPrime(80)
    while gmpy2.gcd(d, phi) != 1:
        d = getPrime(80)
    e = inverse(d, phi)
    c = pow(bytes_to_long(b"FLAG{wiener}"), e, n)
    print("C:", solve(n, e, c))
```

Output:

```
A: ('small_e_root', b'FLAG{easy_small_e}')
B: ('fermat', b'FLAG{fermat_me}')
C: ('wiener', b'FLAG{wiener}')
```

Each case lands in its own attack layer. Case A is solved in `small_e_root`, case B in `fermat`, and case C in `wiener`. On a real challenge, call `solve(n, e, c)`. If it returns `(None, None)`, the challenge belongs to the group that needs common modulus, Hastad, Coppersmith or an oracle. Reopen the matching lesson and add another layer.

## 3. Lab

- Main task: get 10 challenges matching the 10 levels in section 2.1 (generate them with the scripts in the Lab section below, or use the CryptoHack challenges suggested in section 6). Solve them in order and record for each one the sign you noticed, the attack you used, and the number of commands it took.
- Extend the script: add the missing layers to `solve.py`, namely factordb (HTTP API), common modulus (takes two pairs of e and c), Hastad (takes lists of n and c), and shared prime (takes a list of n and tries the gcd of every pair).
- Tool comparison: for each challenge, run RsaCtfTool and your own script side by side, and see which is faster and why.
- Hints, in order: (1) always print the bit length of n and e first; (2) let RsaCtfTool scan while you read the statement; (3) when both fail, it is almost certainly Coppersmith or an implementation bug, so open Sage.
- Done when: you have all 10 flags, and your `solve.py` solves at least 7 of the 10 on its own with no manual help.
- Materialized lab: the Lab section below has a multi-layer `solve.py` (self-testing the three cases A/B/C), `gen/generate_cases.py` which generates sample challenges, and `transcript.txt` with the real output.

## 4. Key takeaways

- Always triage first. Print `n.bit_length()`, `e`, `e.bit_length()` and the gcd of every pair of n.
- Small n goes to factordb. Small e goes to the e-th root or Hastad. Large e goes to Wiener. Close p and q go to Fermat.
- With many keys, try the `gcd` of every pair of n first. It is the cheapest gift.
- Use RsaCtfTool for standard flaws and SageMath for attacks that need lattices (Coppersmith).
- Keep your own multi-layer `solve.py` and extend it after each competition.

## 5. Common pitfalls

- Jumping into RsaCtfTool and skipping triage. It scans for a long time and sometimes misses a flaw a human sees at once (for example e=3). Look at the numbers first and type commands second.
- Forgetting to check the gcd of every pair of n when there are many keys. A shared prime is the easiest flaw and is often missed because nobody thinks of it. One loop of `gcd` settles it.
- Letting Fermat run forever. Always set a step limit. If p and q are not close, Fermat never returns.
- Installing RsaCtfTool with missing dependencies and then thinking the challenge is hard. Many of its attacks need sage, pari, or extra Python libraries. Read its own error log.
- Pasting values in the wrong base. The ciphertext in a challenge is usually hex or base64, not decimal. Convert to the right base before passing it to `pow`. One base mistake can cost a whole session of doubting the algorithm.
- Trusting a tool's "flag" output blindly. Always check that the flag matches the challenge format (for example `CTF{...}`) before submitting.

## 6. Further reading

- RsaCtfTool on GitHub. Read the README for the list of attacks and how to pass parameters.
- Boneh, "Twenty Years of Attacks on the RSA Cryptosystem", an overview map of what other flaws exist beyond these lessons.
- The full CryptoHack RSA path, and Cryptopals sets 5 and 6 (the RSA and Bleichenbacher challenges), for hands-on practice.
- factordb.com for small n, and the `defund/coppersmith` repository for multivariate Coppersmith in Sage.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 6.6</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/6.6.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/6.6/solve.py" download><i class="fa-solid fa-file-code"></i>solve.py</a>
</div>
</div>
