---
title: "Lesson 7.1: Diffie-Hellman and the Discrete Logarithm Problem"
image:
  path: /assets/img/covers/crypto-7-1-diffie-hellman-discrete-logarithm.webp
  alt: "Diffie-Hellman and the Discrete Logarithm Problem"
date: 2023-09-16 01:42:00 +0700
categories: ["Cryptography", "Crypto · Diffie-Hellman"]
tags: [cryptography, diffie-hellman, discrete-log, key-exchange]
render_with_liquid: false
---

This lesson answers one question. How can two people who have never met, talking over a channel that is fully monitored, agree on a shared secret key that the eavesdropper cannot compute? After it you can run a Diffie-Hellman key exchange by hand on small numbers, explain why it is safe (the discrete logarithm problem), and tell good parameters from parameters that invite an attack.

![Diffie-Hellman key exchange and the discrete log wall](/assets/img/crypto/crypto-7-1-diffie-hellman-discrete-logarithm.svg)
_Both sides compute g^(ab) mod p. The eavesdropper sees p, g, A and B but would need a discrete log to get a or b._

**Prerequisites:** Lesson 1.1 (modular arithmetic, fast exponentiation, inverses), Lesson 1.2 (primes, Euler's phi), Lesson 1.4 (groups and finite fields). It helps to know the order of an element.

**Tools:** Python 3 + sympy. Install with `pip install sympy`. Everything else runs on plain integers.

## Goals

By the end you can explain how Diffie-Hellman works and why both sides get the same secret, understand that the discrete logarithm problem (DLP) is what protects it, run a DH exchange on small numbers and solve that DLP with brute force and baby-step giant-step, and recognize safe primes and generators when you read a challenge.

## Theory

### The problem: agreeing on a key over a public channel

Symmetric encryption (AES, Lesson 4) is fast and strong, but it has a chicken-and-egg problem. To encrypt, both sides need the same key, and to send the key safely you already need an encrypted channel. Diffie-Hellman (DH), published in 1976, removes that dependency. The two sides exchange a few public numbers that anyone can see, and still end up with a shared secret.

It relies on an operation that is easy in one direction and hard in the other, modular exponentiation. Computing `g^a mod p` is fast (fast exponentiation, Lesson 1.1). But given `g`, `p` and the result `g^a mod p`, nobody knows a fast way to recover `a` when `p` is large enough. That is the discrete logarithm problem.

### The DH protocol with small numbers

Public to everyone: a prime `p` and a generator `g`. Take `p = 23`, `g = 5`.

1. Alice picks a secret `a = 6`, computes `A = g^a mod p = 5^6 mod 23 = 8`, and sends `A = 8` to Bob.
2. Bob picks a secret `b = 15`, computes `B = g^b mod p = 5^15 mod 23 = 19`, and sends `B = 19` to Alice.
3. Alice computes `s = B^a mod p = 19^6 mod 23`.
4. Bob computes `s = A^b mod p = 8^15 mod 23`.

Both get the same number because `B^a = (g^b)^a = g^(a*b) = (g^a)^b = A^b (mod p)`. The eavesdropper sees `p, g, A, B`. To compute `s` they need `a` or `b`, which means solving a discrete log. The shared secret `s` (or a hash of it) becomes the AES key.

### The discrete logarithm problem (DLP)

Given the multiplicative group modulo `p`, a generator `g` and `h = g^x mod p`, the DLP is to find `x`. For small numbers you can brute force it, or use baby-step giant-step (BSGS), which splits the exponent space into two halves and trades memory for time, in about `sqrt(p)` steps. But the square root of a 2048-bit number is still a 1024-bit number, around `10^308` steps, which is infeasible. For standard parameters the best algorithm (index calculus) is sub-exponential but not polynomial, so 2048-bit DH is still considered safe.

The key point is that DH security rests on the DLP being hard, and the DLP is only hard when the parameters are chosen correctly. Wrong choices break it, and that is the material for Lesson 7.2.

### Safe parameters: safe primes and generators

The order of `g` is the smallest `n` such that `g^n = 1 mod p`. All powers of `g` repeat with period `n`, so `g` only produces `n` distinct values. If `n` is small, the key space is small and can be brute forced at once.

The multiplicative group mod `p` has `p-1` elements. By Lagrange's theorem, the order of every element divides `p-1`. If `p-1` has many small divisors, an attacker can split the problem into small pieces (Pohlig-Hellman, Lesson 7.2). To prevent this, people use a safe prime, meaning `p = 2q + 1` with `q` also prime. Then `p-1 = 2q` has only one small divisor, 2, and the rest is the huge prime `q`, which cannot be split.

The generator should have order `q` (it should live in the subgroup of large prime order) and avoid the useless element of order 2. A simple way to get one is `g = h^2 mod p` for any `h`, because squaring pushes `g` into the subgroup of order `q`.

## Demo

### One key exchange on small numbers

```python
# d71_dh.py: Diffie-Hellman key exchange with small numbers, really run
from sympy import isprime, n_order

# --- 1. public parameters ---
p = 23          # safe prime: 23 = 2*11 + 1, q = 11 is also prime
g = 5           # generator (generator element)

print("p =", p, "| p is prime?", isprime(p))
print("g =", g, "| order of g mod p =", n_order(g, p))

# --- 2. each side picks a secret key ---
a = 6           # Alice keeps this private
b = 15          # Bob keeps this private

A = pow(g, a, p)   # Alice sends this publicly
B = pow(g, b, p)   # Bob sends this publicly
print("Alice sends A = g^a mod p =", A)
print("Bob   sends B = g^b mod p =", B)

# --- 3. each side computes the shared secret ---
s_alice = pow(B, a, p)   # (g^b)^a
s_bob = pow(A, b, p)     # (g^a)^b
print("Alice computes s = B^a mod p =", s_alice)
print("Bob   computes s = A^b mod p =", s_bob)
print("do they match?", s_alice == s_bob)
print("check: g^(a*b) mod p =", pow(g, a * b, p))
```

Output:

```
p = 23 | p is prime? True
g = 5 | order of g mod p = 22
Alice sends A = g^a mod p = 8
Bob   sends B = g^b mod p = 19
Alice computes s = B^a mod p = 2
Bob   computes s = A^b mod p = 2
do they match? True
check: g^(a*b) mod p = 2
```

Both sides get `s = 2`, which equals `g^(a*b) mod p`. The order of `g = 5` is 22 (that is `p-1`), so 5 is a generator of the whole group. An eavesdropper only has `p=23, g=5, A=8, B=19`, and to get `s` they must find `a` from `5^a = 8 mod 23`.

### Solving the discrete log: brute force and baby-step giant-step

```python
# d71_dlog.py: solve the discrete log with brute force and baby-step giant-step (BSGS)
import math

def dlog_brute(g, h, p):
    # find x such that g^x = h mod p, trying sequentially
    cur = 1
    for x in range(p):
        if cur == h:
            return x
        cur = (cur * g) % p
    return None

def dlog_bsgs(g, h, p, order):
    # order = order of g. Split x = i*m + j, m = ceil(sqrt(order))
    m = math.isqrt(order) + 1
    # baby steps: store g^j -> j
    table = {}
    cur = 1
    for j in range(m):
        table[cur] = j
        cur = (cur * g) % p
    # giant step: factor = g^(-m)
    gm = pow(g, m * (p - 2), p)     # g^(-m) mod p, use Fermat because p is prime
    gamma = h
    for i in range(m):
        if gamma in table:
            return i * m + table[gamma]
        gamma = (gamma * gm) % p
    return None

if __name__ == "__main__":
    p, g = 23, 5
    A = 8        # from the demo above: pow(5, 6, 23) = 8
    x = dlog_brute(g, A, p)
    print("brute: log_5(8) mod 23 =", x, "| check:", pow(g, x, p) == A)

    # BSGS on a larger number
    p = 1019          # so nguyen to
    g = 2
    order = p - 1     # assume g generates the whole group
    secret = 777
    h = pow(g, secret, p)
    x = dlog_bsgs(g, h, p, order)
    print("BSGS: found x =", x, "| check g^x == h?", pow(g, x, p) == h)
```

Output:

```
brute: log_5(8) mod 23 = 6 | check: True
BSGS: found x = 777 | check g^x == h? True
```

Brute force finds `a = 6` (Alice's secret key) immediately because `p = 23` is tiny. BSGS solves a larger DLP (`p = 1019`) in about `sqrt(p)` steps instead of `p`. This is why real parameters must be large. Both brute force and BSGS fail once `p` reaches 2048 bits.

### Generating a real safe prime and exchanging keys with large numbers

```python
# d71_safeprime.py: generate a real safe prime and exchange keys on large numbers
from sympy import isprime, nextprime
import secrets

def gen_safe_prime(bits):
    # safe prime p = 2q + 1 with q also prime; set the high bit so p has exactly `bits` bits
    while True:
        q = nextprime(secrets.randbits(bits - 1) | (1 << (bits - 2)))
        p = 2 * q + 1
        if isprime(p) and p.bit_length() == bits:
            return p, q

p, q = gen_safe_prime(256)
print("p bit-length =", p.bit_length())
print("q = (p-1)/2 nguyen to?", isprime((p - 1) // 2))

# g: take a square -> lands in the subgroup of prime order q, avoiding small subgroups
g = pow(2, 2, p)   # the order of g is q (since p-1 = 2q)
assert pow(g, q, p) == 1 and g != 1

# secret key in [2, q-1]
a = secrets.randbelow(q - 2) + 2
b = secrets.randbelow(q - 2) + 2
A, B = pow(g, a, p), pow(g, b, p)
print("shared secrets match?", pow(B, a, p) == pow(A, b, p))
```

Output (the value of `p` is random, so it differs on every run and only the status lines are stable):

```
p bit-length = 256
q = (p-1)/2 nguyen to? True
shared secrets match? True
```

The logic is the same as the first demo, only `p` is now 256 bits. `pow(g, a, p)` uses fast exponentiation, so it stays instant, but the DLP on a 256-bit `p` is already out of reach for brute force and BSGS. In practice DH uses `p` of at least 2048 bits (the MODP groups in RFC 3526), or moves to ECC (Lesson 8) so that smaller numbers give the same security.

## Lab

This lesson is groundwork and has no challenge to break. Practice the following before Lesson 7.2:

- Re-implement DH end to end. Generate a 512-bit safe prime, exchange keys, hash the secret with SHA-256 into an AES-128 key, then encrypt a sentence and decrypt it again. The goal is to connect DH to symmetric encryption as one complete flow.
- Rewrite BSGS for the case where `g` does not generate the whole group. Pass the real `order` of `g` instead of `p-1`, and test it with a `g` of small order.
- Measure it. Increase `p` (16, 20, 24, 28 bits), time brute force against BSGS, and plot the result to see BSGS follow `sqrt(p)`.
- Done when the DH plus AES flow runs end to end and the timing table shows BSGS beating brute force as the theory predicts.

## Key takeaways

- DH: `p, g` are public, each side has a secret exponent, and the shared secret is `g^(a*b) mod p`. Both sides can compute it, the eavesdropper cannot.
- DH security rests on the discrete logarithm being hard, and the DLP is only hard when `p` is large and the order of `g` has a large prime factor.
- Brute force costs about `p` steps and BSGS about `sqrt(p)` steps. Both fail once `p` is large enough (2048 bits and up).
- A safe prime `p = 2q + 1` leaves `p-1` with a single large factor `q`, which blocks Pohlig-Hellman.
- Plain DH does not authenticate either side, so it is open to man-in-the-middle (Lesson 7.2).

## Common pitfalls

- Using the shared secret directly as an AES key. Hash it first with a KDF (for example SHA-256 or HKDF) and then take the key bytes. Using the raw number leaks structure and gives the wrong length.
- Choosing `g` of small order or a `p` that is not a safe prime. A `p-1` with many small factors opens the door to Pohlig-Hellman, even when `p` looks huge.
- Not checking the value the other side sends. Accepting `A = 0, 1` or `p-1` is a problem (elements of small order) and they must be rejected. This is exactly the small subgroup confinement in Lesson 7.2.
- Assuming DH protects against an active attacker by itself. It does not. DH only stops passive eavesdropping. Against man-in-the-middle you need signatures or certificates.
- Mixing up the order of `g` with `p-1` when writing BSGS. Passing the wrong `order` makes the algorithm miss the solution.

## Further reading

- Diffie, Hellman, "New Directions in Cryptography" (1976), the original paper.
- RFC 3526, the standard MODP groups (2048, 3072 and 4096-bit safe primes) that appear in real protocols.
- CryptoHack, the Diffie-Hellman track, from "Diffie-Hellman Starter" to weak parameter groups.
- A Graduate Course in Applied Cryptography (Boneh, Shoup), the chapter on discrete log and DH, for the math in depth.
