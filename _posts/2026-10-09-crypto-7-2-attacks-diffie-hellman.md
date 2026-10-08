---
title: "Lesson 7.2: Attacks on Diffie-Hellman"
image:
  path: /assets/img/covers/crypto-7-2-attacks-diffie-hellman.webp
  alt: "Attacks on Diffie-Hellman"
date: 2026-10-09 15:10:00 +0700
categories: ["Cryptography", "Crypto · Diffie-Hellman"]
tags: [cryptography, diffie-hellman, pohlig-hellman, mitm]
render_with_liquid: false
---

Lesson 7.1 said DH is safe when the parameters are chosen correctly. This lesson does the opposite and collects three ways to break DH when the parameters or the implementation are wrong. Pohlig-Hellman splits the discrete log when `p-1` is smooth. Small subgroup confinement forces the shared key into a tiny subgroup and then guesses it. Man-in-the-middle uses the fact that plain DH does not authenticate either side. After this lesson you have working code that breaks a discrete log on a 123-bit `p`, and you can look at a parameter set and guess which flaw it has.

![Three attacks on Diffie-Hellman](/assets/img/crypto/crypto-7-2-attacks-diffie-hellman.svg)
_Pohlig-Hellman solves small discrete logs per prime factor of p-1 and joins them with CRT. Small subgroup and MITM attack the exchange itself._

**Prerequisites:** Lesson 7.1 (DH and discrete log), Lesson 1.3 (CRT, the Chinese remainder theorem), Lesson 1.2 (Euler's phi, order of an element). Baby-step giant-step from Lesson 7.1 helps.

**Tools:** Python 3 + sympy. Install with `pip install sympy`. The solved lab is in the Lab section below.

## Goals

You will understand and code Pohlig-Hellman, where a discrete log breaks even for a large `p` when `p-1` has only small prime factors. You will understand small subgroup confinement, where sending an element of small order pushes the secret into a small subgroup and leaks the other side's private key piece by piece. You will build a man-in-the-middle on plain DH and see why missing authentication is fatal. And you will be able to judge whether DH is safe by looking at `factorint(p-1)`.

## Theory

### Pohlig-Hellman: when p-1 is smooth, the discrete log breaks

Recall from Lesson 7.1 that the order of `g` divides `p-1`, and that brute force or BSGS costs about `sqrt(order)`. The idea of Pohlig-Hellman is this. If `p-1` factors into small prime powers `p-1 = q1^e1 * q2^e2 * ...`, then instead of solving one huge discrete log we solve many tiny discrete logs, one in each subgroup of order `qi^ei`, and combine them with CRT (Lesson 1.3).

To find `x` from `h = g^x mod p` where `g` has order `n = p-1`:

1. For each factor `q^e` of `n`, project the problem down to the subgroup of order `q^e`. Set `g_i = g^(n / q^e)` and `h_i = h^(n / q^e)`. Then `g_i` has order exactly `q^e`, and `x mod q^e` is the discrete log of `h_i` with base `g_i`.
2. Solve that small discrete log. Keep splitting it by base-`q` digits, where each digit is a discrete log in a group of order `q`, solved by BSGS very quickly because `q` is small.
3. With `x mod qi^ei` for every `i`, use CRT to join them into `x mod n`.

The total cost is roughly the sum of the `sqrt(qi)`. If the largest factor of `p-1` is only a few dozen, a discrete log on a `p` of hundreds of bits breaks in an instant. This is why safe parameters must use a safe prime. When `p = 2q + 1`, the largest factor of `p-1` is the huge `q`, and Pohlig-Hellman is useless.

### Small subgroup confinement

This is an active attack. The attacker does not solve the discrete log of `p`. They make the victim narrow the secret down to a small subgroup.

Suppose `p-1` has a small factor `t` (say `t = 5`). There is always an element `h` of order exactly `t`, obtained as `h = g^((p-1)/t) mod p`. It produces only `t` distinct values. If the victim (call him Bob, with private key `b`) receives `h` without checking it and then computes the secret `h^b mod p`, the result lies in a group of `t` elements. The attacker tries all `t` possibilities and learns `b mod t` right away.

Repeat with several small factors `t1, t2, ...` of `p-1`, collect `b mod ti` for each, then CRT them into the full `b` if the product of the `ti` exceeds the real order of `b`. This is the active version of Pohlig-Hellman. It even works against a safe prime if the implementation does not check the received value, since a safe prime still has the factor 2 and so leaks at least one bit.

### Man-in-the-middle without authentication

Plain DH only defends against passive eavesdropping. It does not defend against an attacker who sits in the path. Mallory stands between Alice and Bob. She intercepts Alice's `A` and replaces it with her own `M = g^m` toward Bob, and she intercepts Bob's `B` and also replaces it with `M` toward Alice. As a result Alice sets up a shared key with Mallory (thinking it is Bob), and Bob sets up a shared key with Mallory (thinking it is Alice). Mallory decrypts, reads, modifies, and re-encrypts for the other side. Neither of them notices.

The root cause is that nobody authenticates whose `A` and `B` they really are. The fix is to sign the DH values (as in TLS, Lesson 10.1) or to bind them to a pre-shared secret (PAKE). DH itself does not solve this.

## Demo

### Pohlig-Hellman from scratch, breaking a discrete log with smooth p-1

```python
# d72_ph.py: Pohlig-Hellman from scratch, break discrete log when p-1 is smooth
import math
from sympy import factorint, isprime, discrete_log

# fixed parameters: p-1 has only small factors (<= 23)
p = 7962994002710200590936746770260937501
g = 24
assert isprime(p)

def bsgs(g, h, p, order):
    # discrete log in a subgroup of (small) order `order`: find x, g^x = h mod p
    m = math.isqrt(order) + 1
    table = {}
    e = 1
    for j in range(m):
        table.setdefault(e, j)
        e = (e * g) % p
    factor = pow(g, m * (p - 2), p)   # g^(-m) mod p
    gamma = h
    for i in range(m):
        if gamma in table:
            return i * m + table[gamma]
        gamma = (gamma * factor) % p
    return None

def crt(residues, moduli):
    # combine the per-factor solutions into one solution mod the product
    from math import prod
    N = prod(moduli)
    x = 0
    for r, n in zip(residues, moduli):
        Ni = N // n
        x += r * Ni * pow(Ni, -1, n)
    return x % N

def pohlig_hellman(g, h, p, order):
    # order = order of g (here = p-1). Solve the dlog for each prime power.
    residues, moduli = [], []
    for q, e in factorint(order).items():
        qe = q ** e
        # shrink g, h into the subgroup of order q^e
        gi = pow(g, order // qe, p)
        hi = pow(h, order // qe, p)
        # find x mod q^e digit by digit in base q
        x = 0
        gamma = pow(gi, q ** (e - 1), p)   # element of order q
        for k in range(e):
            hk = pow(pow(gi, -1, p), x, p)
            hk = (hi * hk) % p
            hk = pow(hk, q ** (e - 1 - k), p)
            d = bsgs(gamma, hk, p, q)       # digit in [0, q)
            x += d * (q ** k)
        residues.append(x % qe)
        moduli.append(qe)
    return crt(residues, moduli)

if __name__ == "__main__":
    order = p - 1
    print("p bit-length =", p.bit_length())
    print("p-1 =", factorint(p - 1))

    secret = 0xC0FFEEBADC0DE  # secret key to recover
    h = pow(g, secret, p)
    print("secret that    =", secret)
    print("public h = g^secret mod p =", h)

    rec = pohlig_hellman(g, h, p, order)
    print("Pohlig-Hellman found x =", rec)
    print("matches secret?", rec == secret, "| check g^x == h?", pow(g, rec, p) == h)

    # cross-check with sympy
    print("sympy.discrete_log =", discrete_log(p, h, g))
```

Output:

```
p bit-length = 123
p-1 = {2: 2, 3: 8, 5: 8, 7: 8, 11: 1, 13: 3, 17: 2, 19: 4, 23: 6}
secret that    = 3395287270670558
public h = g^secret mod p = 5474449154460575143637376939195086802
Pohlig-Hellman found x = 3395287270670558
matches secret? True | check g^x == h? True
sympy.discrete_log = 3395287270670558
```

The discrete log on a 123-bit `p` comes out in under a second, only because `factorint(p-1)` shows the largest factor is 23. Each subgroup is small, so BSGS inside it is almost instant, and CRT joins the pieces into `secret`. The `sympy.discrete_log` line confirms the hand-written code matches the library. If `p` were a safe prime, `factorint(p-1)` would return one huge prime factor and the whole algorithm would stall.

### Small subgroup confinement, reading b mod t

```python
# d72_subgroup.py: small subgroup confinement, force the shared secret into a small subgroup
from sympy import isprime, factorint

# choose p so that p-1 has a small factor t for illustration (t = 5)
p = 0
for cand in range(10**6, 10**6 + 100000):
    if isprime(cand) and (cand - 1) % 5 == 0 and (cand - 1) % 2 == 0:
        p = cand
        break
g = 7
print("p =", p, "| p-1 =", factorint(p - 1))

# Bob has a secret key b, the attacker wants to learn b mod 5
b = 918273 % (p - 1)

# element of order 5: take g^((p-1)/5). This only generates a subgroup of 5 elements.
t = 5
h = pow(g, (p - 1) // t, p)
print("small-order element h = g^((p-1)/t) mod p =", h, "| order of h =", t)

# if Bob does NOT validate h and returns shared = h^b, it falls into a group of 5 elements
shared = pow(h, b, p)
# the attacker brute-forces 5 possibilities -> reads off b mod 5
for r in range(t):
    if pow(h, r, p) == shared:
        print("attacker reads: b mod", t, "=", r)
        break
print("check: actual b mod 5 =", b % 5)
```

Output:

```
p = 1000081 | p-1 = {2: 4, 3: 3, 5: 1, 463: 1}
small-order element h = g^((p-1)/t) mod p = 188136 | order of h = 5
attacker reads: b mod 5 = 3
check: actual b mod 5 = 3
```

With a single value `h` of order 5, the attacker gets `b mod 5` exactly. Collect the other factors of `p-1` too (here 2, 3 and 463), then CRT, and the whole of `b` is gradually revealed. The lesson is to always check that the value the other side sends lies in the subgroup of large prime order, and to reject elements of small order.

### Man-in-the-middle on plain DH

```python
# d72_mitm.py: man-in-the-middle when DH has no authentication
import hashlib
from sympy import nextprime

p = nextprime(2**120)
g = 5

def kdf(x):
    return hashlib.sha256(str(x).encode()).hexdigest()[:16]

# Alice and Bob are about to exchange keys
a, b = 111111111, 222222222
A, B = pow(g, a, p), pow(g, b, p)

# Mallory sits in the middle, has her own key m, and replaces both A and B
m = 999999999
M = pow(g, m, p)

# Alice receives M (thinking it is B), Bob receives M (thinking it is A)
key_alice = kdf(pow(M, a, p))   # Alice <-> Mallory
key_bob = kdf(pow(M, b, p))     # Bob   <-> Mallory
# Mallory computes both herself
key_mal_a = kdf(pow(A, m, p))
key_mal_b = kdf(pow(B, m, p))

print("Alice <-> Mallory key  :", key_alice, "| Mallory computes:", key_mal_a, key_alice == key_mal_a)
print("Bob   <-> Mallory key  :", key_bob, "| Mallory computes:", key_mal_b, key_bob == key_mal_b)
print("do Alice and Bob share a key?", key_alice == key_bob)
print("-> Mallory can read and modify every packet between the two parties.")
```

Output:

```
Alice <-> Mallory key  : 2e72076dc757345c | Mallory computes: 2e72076dc757345c True
Bob   <-> Mallory key  : 5302b61b8b1cbdb0 | Mallory computes: 5302b61b8b1cbdb0 True
do Alice and Bob share a key? False
-> Mallory can read and modify every packet between the two parties.
```

Alice and Bob think they share a key, but each of them is actually talking to Mallory. No operation is broken here. Nobody authenticates the other end. This is why every real protocol (TLS, SSH) signs or certifies the DH values.

### The solved lab

The Lab section below holds a complete Pohlig-Hellman challenge. It gives `p` with smooth `p-1`, `g`, and `A = g^a mod p`, where the secret key `a` is the flag as a number. `solve.py` is self-contained and prints the real flag, and `transcript.txt` records the output. Use it to compare against your own work from the lab below.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 7.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/7.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/7.2/solve.py" download><i class="fa-solid fa-file-code"></i>solve.py</a>
</div>
</div>

- Task (in the Lab section below): given `p = 7962994002710200590936746770260937501`, `g = 24`, and `A = g^a mod p`. The key `a` is the flag as a number (`bytes_to_long`). Recover `a`, convert it to bytes, and read the flag `DH{...}`.
- Files: `solve.py` (reference solution), `README.md` (description) and `transcript.txt` (real output), all in the Lab section below.
- Hints in steps: (1) run `factorint(p-1)` first and look at the largest factor; (2) if all factors are small, Pohlig-Hellman is the way, or call `sympy.discrete_log(p, A, g)` directly; (3) convert `a` to bytes with `a.to_bytes((a.bit_length()+7)//8, "big")`.
- Extension: turn the small subgroup demo into an active lab. Collect `b mod ti` for every small factor of `p-1` and CRT them to get all of `b`.
- Done when you get the flag `DH{...}` and can explain why this `p` is not safe.

## Key takeaways

- `factorint(p-1)` is the first thing to run on a DH challenge. If it is all small factors, use Pohlig-Hellman and it breaks at once.
- Pohlig-Hellman solves the discrete log in each subgroup of order `qi^ei` and then applies CRT. The cost is about the sum of `sqrt(qi)`.
- A safe prime `p = 2q + 1` blocks Pohlig-Hellman because `p-1` has only one large factor `q`.
- Small subgroup confinement: send an element of small order, force the secret into a small subgroup, read `b mod t`. Block it by checking that the received value lies in the subgroup of large prime order.
- Plain DH has no authentication, so it always falls to man-in-the-middle. Sign or certify the DH values.

## Common pitfalls

- Judging safety by the bit length of `p` alone. A 2048-bit `p` with smooth `p-1` still breaks to Pohlig-Hellman. Safety lies in the largest factor of `p-1`, not in the number of bits.
- Forgetting to check the received value. Accepting `0`, `1`, `p-1`, or any element of small order and still computing the secret opens the door to small subgroup attacks. Always check `pow(A, q, p) == 1` with `q` the expected prime order.
- Getting CRT wrong when the moduli are not coprime. In Pohlig-Hellman the `qi^ei` are pairwise coprime so CRT works, but merging repeated factors by hand gives wrong results. Use the distinct prime powers.
- Believing BSGS in a small subgroup needs `order = p-1`. It does not. Pass the small order `q` of the subgroup, otherwise the algorithm is slow or misses the solution.
- Treating man-in-the-middle as a flaw of the DH algorithm. It is a missing authentication at the protocol level. DH does its job (stopping passive eavesdropping), and authentication is a separate job.

## Further reading

- Pohlig, Hellman, "An Improved Algorithm for Computing Logarithms over GF(p)" (1978), the original paper of the algorithm.
- CryptoHack, the "Diffie-Hellman" group, especially "Parameter Injection", "Export-grade" and "Static Client", which match the subgroup and MITM cases.
- Cryptopals set 5, challenges 34 to 36 (MITM on DH, parameter injection), which are very close to this lesson.
- Write-ups on small subgroup attacks against TLS and SSH when static DH parameters are reused, to see that this flaw is real.
