---
title: "Lesson 6.4: Wiener Attack and Coppersmith"
image:
  path: /assets/img/covers/crypto-6-4-wiener-attack-coppersmith.webp
  alt: "Wiener Attack and Coppersmith"
date: 2023-08-21 09:38:00 +0700
categories: ["Cryptography", "Crypto · RSA"]
tags: [cryptography, rsa, wiener, coppersmith]
render_with_liquid: false
---

These are two higher-level attacks. The Wiener attack breaks RSA when the private exponent d is too small, using continued fractions. Coppersmith is a whole family of attacks that find small roots of a polynomial modulo N using lattice reduction (LLL). They let you recover a message when part of it is known, or factor n when part of p is known. This lesson gives you Wiener in plain Python, and Coppersmith in SageMath with `small_roots`.

![Wiener attack and Coppersmith small roots](/assets/img/crypto/crypto-6-4-wiener-attack-coppersmith.svg)
_Wiener searches convergents of e/n. Coppersmith builds a lattice and reduces it with LLL._

Part: 6 (RSA) | Time: about 60 minutes | Difficulty: hard

**Prerequisites:** Lessons 6.1, 6.2 and 6.3. The Coppersmith part needs SageMath. Basic knowledge of vectors and matrices helps with LLL but is not required to run the code.

**Tools:** Python 3 with gmpy2 for Wiener. SageMath (the `sage` command) for Coppersmith. Sage includes `small_roots` and LLL.

## Goals

After this lesson you can:

- Explain why a small d leaks the key, and implement the Wiener attack with continued fractions.
- State how small d must be for Wiener to work (`d < n^(1/4) / 3`).
- Use Sage's `small_roots` for two Coppersmith problems, a partly known message (stereotyped message) and known high bits of p (partial key exposure).
- Understand the core idea of LLL well enough to tell when Coppersmith applies.

## 1. Theory

### 1.1. Why a small d is dangerous

People sometimes want a small d so decryption and signing are fast (exponentiation with a small exponent is cheaper). But a small d breaks RSA. The reason comes from the key relation:

```
e * d = 1 + k * phi    (for some integer k)
```

Since `phi` is very close to n (phi = n - (p+q) + 1, and p+q is small compared with n), we get the approximation `e*d ≈ k*n`, which means `e/n ≈ k/d`. The fraction `k/d` is an extremely good approximation of `e/n`. Continued fraction theory says every good enough approximation of a rational number appears among its convergents. So you expand `e/n` as a continued fraction, walk through the convergents `k/d`, and for each candidate d test whether it opens the key.

Wiener proved that if `d < n^(1/4) / 3`, then d is guaranteed to be the denominator of some convergent of `e/n`, so the attack always succeeds. The sign to look for in a challenge is a very large e (close to n), because a small d forces a large e (they are inverses modulo phi).

To check a candidate `(k, d)`, from `e*d = 1 + k*phi` we get `phi = (e*d - 1) / k`, which must divide evenly. With phi in hand, solve the quadratic `x^2 - (n - phi + 1)x + n = 0` to find p and q (since `p+q = n - phi + 1` and `p*q = n`). If the equation has integer roots, d is correct.

### 1.2. Coppersmith: small roots of a polynomial modulo N

Coppersmith's theorem (1996) solves this problem. Given a polynomial `f(x)` of degree d modulo N, find the small integer roots `x0` with `|x0| < N^(1/d)`. This can be done in polynomial time, even though finding an arbitrary root modulo N is hard in general. The key step is to turn the modular problem into a problem over the integers. If x0 is small enough, a well-chosen combination of f and multiples of N makes f(x0) so small that it equals 0 over the integers and not only modulo N. That combination is found with lattice reduction.

Two common CTF uses:

In a stereotyped message (partly known message), you know most of the plaintext and only a short piece x is missing. Write `m = a + x` where a is the known part. Then `c = (a + x)^e mod n`, so x is a small root of `f(x) = (a + x)^e - c mod n`. If the unknown part is short enough (`x < n^(1/e)`), `small_roots` finds x.

In partial key exposure (high bits of p known), you know the high bits of p, and the low part (say the last 200 bits) is unknown, called x. Write `p = p_high + x`. Then `f(x) = p_high + x` has a root x for which `f(x)` divides n (because it equals p). This is the divisor-finding variant of Coppersmith (the `beta` parameter in Sage). If the number of unknown bits is below about half the bits of p, p can be recovered, and then n is factored. This flaw happens in practice when a key is partly leaked through a side channel or printed incompletely.

### 1.3. LLL, simplified

LLL (Lenstra, Lenstra, Lovasz, 1982) is a lattice basis reduction algorithm. A lattice is the set of all integer combinations of a few basis vectors, which forms a regular grid of points in space. A basis can consist of long, skewed vectors that describe the same grid as a basis of short, nearly perpendicular vectors. LLL turns a bad basis into a good one (short vectors) in polynomial time.

This connects to Coppersmith because we build a lattice where each vector encodes the coefficients of a polynomial (f and well-chosen multiples of N times powers of x). A short vector found by LLL corresponds to a polynomial with small coefficients, small enough that it vanishes at the root x0 over the integers. Solving that polynomial over the integers is easy and gives x0. You do not build the lattice yourself in a CTF, because Sage's `small_roots` wraps all of it. Still, knowing this helps you tune the parameters `X` (the upper bound of the root), `beta` and `epsilon` when it fails to find a root.

## 2. Demo

### 2.1. Wiener attack with continued fractions (plain Python)

```python
# wiener.py: break RSA when d is small, using continued fractions
import gmpy2
from Crypto.Util.number import getPrime, inverse

def cf_expansion(a, b):
    # expand a/b into a sequence of continued fraction quotients
    while b:
        q = a // b
        yield q
        a, b = b, a - q * b

def convergents(cf):
    # generate the convergents (numerator, denominator) from the quotients
    num0, num1 = 0, 1
    den0, den1 = 1, 0
    for q in cf:
        num = q * num1 + num0
        den = q * den1 + den0
        yield num, den
        num0, num1 = num1, num
        den0, den1 = den1, den

def wiener(e, n):
    for k, d in convergents(cf_expansion(e, n)):
        if k == 0:
            continue
        if (e * d - 1) % k != 0:
            continue
        phi = (e * d - 1) // k
        b = n - phi + 1               # = p + q
        disc = b * b - 4 * n          # discriminant of x^2 - b x + n
        if disc < 0:
            continue
        s, exact = gmpy2.iroot(disc, 2)
        if exact and (b + s) % 2 == 0:
            return int(d)             # found d
    return None

# use a key with a small d for illustration
p, q = getPrime(512), getPrime(512)
n, phi = p * q, (p - 1) * (q - 1)
d = getPrime(80)                      # d is about 80 bits, much smaller than n^(1/4) ~ 256 bits
while gmpy2.gcd(d, phi) != 1:
    d = getPrime(80)
e = inverse(d, phi)                   # e is large (close to 1024 bits) because d is small

d_rec = wiener(e, n)
print("d recovered correctly?", d_rec == int(d))
```

Output:

```
d recovered correctly? True
```

Note that d is only 80 bits while `n^(1/4)` is about 256 bits, so the Wiener condition is met with room to spare. As a result e grows to almost 1024 bits. That is the sign to recognize at once when a challenge gives you an e close to n, so try Wiener first. The algorithm recovers d exactly without brute-force factoring n, and walks through only a few dozen convergents.

### 2.2. Coppersmith: stereotyped message (SageMath)

```python
# coppersmith_stereotyped.sage: most of the plaintext known, a short piece missing
from Crypto.Util.number import bytes_to_long, long_to_bytes
set_random_seed(1)
p = random_prime(2**512); q = random_prime(2**512)
n = p * q; e = 3

# message: known prefix, last 5 bytes (40 bits) unknown
msg = b"The secret code is: " + b"01234"
m = bytes_to_long(msg)
c = power_mod(m, e, n)

# the attacker knows the prefix, sets the unknown part = 0
known = bytes_to_long(b"The secret code is: " + b"\x00" * 5)

PR.<x> = PolynomialRing(Zmod(n))
f = (known + x)^e - c
f = f.monic()                         # normalize the leading coefficient to 1
roots = f.small_roots(X=2**40, beta=1.0, epsilon=0.05)
print("roots:", roots)
if roots:
    rec = known + int(roots[0])
    print("recovered:", long_to_bytes(int(rec)))
```

Running `sage coppersmith_stereotyped.sage` prints:

```
roots: [206983803700]
recovered: b'The secret code is: 01234'
```

The small root `x = 206983803700` is the numeric value of the 5 bytes `"01234"`. The parameter `X=2**40` tells Sage the root is below 40 bits, and `beta=1.0` is used because we look for a root modulo the full n. If the unknown part is longer (close to `n^(1/e)` bits), you must raise `X`, and it can fail once you pass the theoretical limit.

### 2.3. Coppersmith: high bits of p known (SageMath)

```python
# coppersmith_partial_p.sage: high bits of p known, recover p -> factor n
set_random_seed(2)
p = random_prime(2**512); q = random_prime(2**512)
n = p * q

# assume the low 200 bits of p leaked (312 high bits known)
known_high = (p >> 200) << 200        # set the low 200 bits = 0
PR.<x> = PolynomialRing(Zmod(n))
f = x + known_high                    # p = known_high + x, x < 2^200
# beta=0.4 since p ~ n^0.5, we look for a divisor of size about n^beta
roots = f.small_roots(X=2**200, beta=0.4, epsilon=0.03)
print("roots:", roots)
if roots:
    pp = known_high + int(roots[0])
    print("p correct?", n % pp == 0)
```

Output (the root value depends on the seed):

```
roots: [1415048056288467933821506898733528983378730236048721366743415]
p correct? True
```

Here we are not looking for a root modulo n. We look for a divisor of n of size about `n^beta`. The parameter `beta=0.4` says the divisor we want (p) has size at least about `n^0.4` (p is roughly `n^0.5`, and we take a slightly smaller beta to be safe). `small_roots` returns the low part of p, and adding the known high part gives the full p. The check `n % p == 0` confirms it. After factoring, decrypt as in Lesson 6.1. The theoretical limit is that p can be recovered when the number of unknown bits is below about half the bits of p.

## 3. Lab

- Task 1 (Wiener): you get an RSA-1024 `n`, an unusually large `e` (close to n), and `c`. Recover d and decrypt. Put the files in the Lab section below.
- Task 2 (stereotyped): you get `e = 3`, `n`, `c`, and a note that the plaintext has the form `b"flag: CTF{" + 6 unknown hex characters + b"}"`. Use `small_roots` to get the 6 characters.
- Task 3 (partial p): you get `n` and the top 312 bits of p (as a shifted number). Recover p, factor n, and decrypt.
- Hints, in order: (1) if e is close to n, think Wiener right away; (2) for stereotyped, put the unknown part at the right position in the integer (multiply by 256 to the power of the number of bytes after it); (3) if `small_roots` returns an empty list, try raising `X`, lowering `epsilon`, or rechecking beta.
- Done when: you have all three flags, and for each task you can say why the attack applies.

## 4. Key takeaways

- An unusually large e (close to n) signals a small d, so try Wiener.
- Wiener is guaranteed when `d < n^(1/4) / 3`. Expand `e/n` as a continued fraction and walk through the convergents `k/d`.
- Check each candidate by solving the quadratic for p and q from phi.
- Coppersmith stereotyped works when you know most of m and the unknown part is smaller than `n^(1/e)`. Use `small_roots` on the polynomial `(a+x)^e - c`.
- Coppersmith partial p works when you know more than half the bits of p. Use `small_roots` with `beta`.

## 5. Common pitfalls

- Running Wiener when d is not small. The algorithm runs but finds nothing. Wiener is one tool, so if it misses, change direction. There is a Boneh-Durfee variant that raises the limit to `d < n^0.292` using lattices, which is stronger but more complex.
- Placing the unknown part wrongly in the stereotyped case. If the unknown piece sits in the middle of the message and not at the end, multiply x by `256^(number of bytes after it)` to match the numeric value. With the wrong placement the root never appears.
- Expecting `small_roots` to break a root that is too large. Coppersmith has a hard theoretical limit (`n^(1/d)` for roots modulo n, half the bits for divisors). Past that limit it is impossible, and tuning parameters does not help.
- Forgetting `f.monic()` in the stereotyped case. `small_roots` needs a monic polynomial (leading coefficient 1). For `(known+x)^e` the leading coefficient is already 1, but if you transform the polynomial in another way, remember to normalize.
- Mixing up `beta` between the two problems. A root modulo the full n uses `beta=1.0`. A divisor of n uses a `beta` roughly equal to the divisor's size relative to n (about 0.4 to 0.5 for p).

## 6. Further reading

- Wiener, "Cryptanalysis of Short RSA Secret Exponents" (1990), the original paper.
- Coppersmith, "Small Solutions to Polynomial Equations, and Low Exponent RSA Vulnerabilities" (1996). A more approachable presentation is May, "Using LLL-Reduction for Solving RSA and Factorization Problems".
- Boneh and Durfee, "Cryptanalysis of RSA with Private Key d Less than N^0.292" (1999), if you want to push the Wiener limit.
- The CryptoHack "Mathematics" and "RSA" sections have hands-on Wiener and Coppersmith challenges. The `defund/coppersmith` repository on GitHub covers multivariate polynomials in Sage.
