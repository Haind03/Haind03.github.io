---
title: "Lesson 6.2: Attacks on Weak RSA Parameters"
image:
  path: /assets/img/covers/crypto-6-2-attacks-weak-rsa-parameters.webp
  alt: "Attacks on Weak RSA Parameters"
date: 2026-10-09 14:10:00 +0700
categories: ["Cryptography", "Crypto · RSA"]
tags: [cryptography, rsa, factoring, fermat]
render_with_liquid: false
---

RSA being correct mathematically does not mean every use of it is safe. Most RSA challenges in CTFs do not break RSA itself. They break the way the parameters were chosen. This lesson covers three classic parameter mistakes and gives working code for each: a small exponent e with no padding (cube root), a small n that can be looked up on factordb, and p and q that are too close to each other (Fermat factorization).

![Three weak RSA parameter choices and the attack for each](/assets/img/crypto/crypto-6-2-attacks-weak-rsa-parameters.svg)
_Each weak parameter choice has a cheap attack that needs no private key._

Part: 6 (RSA) | Time: about 45 minutes | Difficulty: medium

**Prerequisites:** Lesson 6.1 (how RSA works), Lesson 1.1 (modular arithmetic). You should know what an integer square root and an integer cube root are.

**Tools:** Python 3 with gmpy2, PyCryptodome and sympy. Online lookup: factordb.com. Install with `pip install gmpy2 pycryptodome sympy requests`.

## Goals

After this lesson you can:

- Break RSA with `e = 3` when the message has no padding and `m^3 < n`, using a single cube root.
- Use factordb to get the factors of an n that someone has already factored.
- Recognize p and q that are close together and use Fermat factorization to split n almost instantly.
- Look at a set of RSA parameters and know which flaw to try first.

## 1. Theory

### 1.1. Small e with no padding: the cube root attack

Many older systems chose `e = 3` so encryption is fast. If the message m is small, specifically `m^3 < n`, then the modulo in `c = m^3 mod n` never happens. This means `c = m^3` exactly over the integers. The attacker does not need d and does not need to factor n. Taking the integer cube root of c gives m.

The conditions are a small e (3, sometimes 5 or 7), no random padding, and a message that is short compared to n. In a CTF, a short flag encrypted with RSA-2048 and e=3 almost always satisfies `m^3 < n`.

More generally, for any e, if `m^e < n` then `c = m^e` over the integers and you take the e-th root. If `m^e` is only a little larger than n (by a few multiples), there is still a way. Try `c + k*n` for k = 0, 1, 2, ... and take the e-th root each time, because `m^e = c + k*n` for some small k.

### 1.2. Small n: factordb and ready-made factoring tools

factordb.com is a community database that stores the factorization of a very large number of integers. If your n is small, or has appeared before (reused from an old challenge, or a well-known number), factordb may already have p and q. Once you have the factors, compute d as in Lesson 6.1.

Besides factordb, for n below roughly 70 to 80 decimal digits, tools on your own machine can factor it in reasonable time using `sympy.factorint`, or the stronger Pari/GP, msieve, yafu and CADO-NFS. As a rule of thumb, n under 256 bits can usually be factored, and n above 1024 bits is out of reach unless there is another flaw.

### 1.3. p and q close together: Fermat factorization

If the key generator picked p and q close together (for example p, then `q = nextprime(p)`), n has a structure that is easy to exploit. Fermat's idea is that every odd `n = p*q` can be written as a difference of two squares, `n = a^2 - b^2 = (a-b)(a+b)`, with `a = (p+q)/2` and `b = (q-p)/2`.

When p and q are close, b is small, so a is only slightly larger than `sqrt(n)`. The algorithm starts at `a = ceil(sqrt(n))` and increases a one step at a time. At each step it checks whether `a^2 - n` is a perfect square. When it is a perfect square `b^2`, you get `p = a - b` and `q = a + b`. The number of steps is roughly proportional to `(p-q)^2 / sqrt(n)`, so the closer p and q are, the faster it runs, often finishing on the first step.

Signs in a challenge include a statement saying p and q were generated close together, `isqrt(n)^2` being very close to n, or Fermat finishing within a few thousand steps when you try it.

## 2. Demo

### 2.1. Cube root attack with e = 3

```python
# cube_root.py: break RSA with e=3 and no padding when m^3 < n
import gmpy2
from Crypto.Util.number import bytes_to_long, long_to_bytes, getPrime

e = 3
# simulate a real key but with a short message
p, q = getPrime(512), getPrime(512)
n = p * q
m = bytes_to_long(b"CTF{small_e}")
c = pow(m, e, n)

# since m is short, m^3 < n, so no modulo reduction happens: c == m^3 over the integers
root, exact = gmpy2.iroot(c, 3)   # can bac ba nguyen
print("exact cube root?", exact)
print("recovered:", long_to_bytes(int(root)))
```

Output:

```
exact cube root? True
recovered: b'CTF{small_e}'
```

`gmpy2.iroot(c, 3)` returns a pair `(root, is_exact)`. The flag `exact = True` confirms that c is a perfect cube of an integer, and that integer is m. We never touched d and never factored n.

If `exact = False`, a modulo reduction did happen. Try a loop that adds multiples of n:

```python
# cube_root_kn.py: case where m^3 exceeds n by only a few multiples
for k in range(10000):
    root, exact = gmpy2.iroot(c + k * n, 3)
    if exact:
        print("found at k =", k, "->", long_to_bytes(int(root)))
        break
```

### 2.2. Looking up factordb

```python
# factordb_lookup.py: ask factordb whether n has been factored
import requests

def factordb(n):
    r = requests.get("http://factordb.com/api", params={"query": str(n)})
    data = r.json()
    # status: FF means fully factored; factors is a list [factor, exponent]
    factors = []
    for f, mult in data.get("factors", []):
        factors.extend([int(f)] * int(mult))
    return data.get("status"), factors

n = 1000036000099   # example of a small n (= 1000003 * 1000033)
status, factors = factordb("%d" % n)
print("status:", status, "factors:", factors)
```

For a small or known n, factordb returns `status = FF` and the list of factors. Then you can compute d right away:

```python
from Crypto.Util.number import inverse
p, q = factors
d = inverse(65537, (p - 1) * (q - 1))
```

When you are offline, or n is not on factordb but is still small, use sympy:

```python
from sympy import factorint
print(factorint(1000036000099))   # {1000003: 1, 1000033: 1}
```

### 2.3. Fermat factorization for close p and q

```python
# fermat.py: split n when p and q are close
import gmpy2

def fermat(n):
    a = gmpy2.isqrt(n)
    if a * a < n:
        a += 1                     # a = ceil(sqrt(n))
    steps = 0
    while True:
        b2 = a * a - n
        b, exact = gmpy2.iroot(b2, 2)
        if exact:                  # a^2 - n is a perfect square
            return int(a - b), int(a + b), steps
        a += 1
        steps += 1

p, q = 1000003, 1000033            # two primes very close together
n = p * q
fp, fq, steps = fermat(n)
print(f"n = {n}")
print(f"a = {gmpy2.isqrt(n) + 1}, found p={fp}, q={fq}, after {steps} steps")
```

Output:

```
n = 1000036000099
a = 1000018, found p=1000003, q=1000033, after 0 steps
```

The step count is 0. The very first candidate `a = ceil(sqrt(n)) = 1000018` gives `a^2 - n = 225 = 15^2`, so `b = 15`, `p = 1000018 - 15 = 1000003` and `q = 1000018 + 15 = 1000033`. This is why close p and q are a disaster. Fermat splits n almost instantly no matter how large n is, even a 2048-bit n if the gap between p and q is small enough.

Once you have p and q, the rest is the same as Lesson 6.1, so compute phi, compute d, and decrypt.

## 3. Lab

- Task 1 (small e): you get `e = 3`, an RSA-1024 `n`, and a `c`. The flag is short (under 40 bytes). Recover it. Put the files in the Lab section below.
- Task 2 (Fermat): you get an RSA-2048 `n` and a note saying "I accidentally chose q = nextprime(p)", plus `e = 65537` and `c`. Factor n and decrypt.
- Task 3 (factordb): you get a 256-bit `n` taken from an old challenge. Look it up on factordb. If it is there, solve it. If not, run `factorint`.
- Hints, in order: (1) try the cube root first because it is the cheapest; (2) if e is large and n looks normal, try Fermat for a few hundred thousand steps; (3) always send n to factordb in parallel.
- Done when: you have all three flags.
- Materialized lab: the Lab section below has a `solve.py` that runs all three flaws (cube root, Fermat, factordb with a `factorint` fallback) and a `transcript.txt` with the real output.

## 4. Key takeaways

- A small `e` (3, 5, 7) plus no padding plus a short message means you should try the e-th root immediately, with no need for d.
- If the root is not exact, try `c + k*n` with small k and take the root.
- A small or familiar n should go to factordb before anything else.
- If `isqrt(n)^2` is very close to n, or the statement hints that p and q are close, run Fermat.
- Once n is factored the problem is over. Compute phi, compute d, decrypt.

## 5. Common pitfalls

- Forgetting to check the `exact` flag of `iroot`. If you take the integer part of the root without checking exactness, you get a number that is off by a few units and may think the attack failed. Always read the second value.
- Mixing up `m^e < n` (cube root works directly) and `m^e > n` (you must add multiples of n or use another attack). Estimate the bit length of `m^e` first.
- Running Fermat in an unbounded loop. If p and q are not close, Fermat never finishes. Set a step limit (a few million, for example), give up, and try something else.
- Using HTTPS for the factordb API and hitting a certificate error. The public endpoint is `http://factordb.com/api`, and respect the rate limit instead of spamming it.
- Assuming a large n is safe. Fermat does not care how large n is, only how far apart p and q are. An RSA-2048 key whose p and q differ by 2^20 still breaks in an instant.

## 6. Further reading

- factordb.com. Browse a few numbers to get used to the JSON API format.
- CryptoHack, the "Factoring", "Inferius Prime" and "Square Eyes" challenges, which are exactly this kind of weak p and q.
- RsaCtfTool (used in depth in Lesson 6.6) automates most of these parameter flaws, but understand them by hand before using the tool.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 6.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/6.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/6.2/solve.py" download><i class="fa-solid fa-file-code"></i>solve.py</a>
</div>
</div>
