---
title: "Lesson 8.2: ECDSA Private Key Recovery from Nonce Reuse"
image:
  path: /assets/img/covers/crypto-8-2-ecdsa-nonce-reuse.webp
  alt: "ECDSA Private Key Recovery from Nonce Reuse"
date: 2023-10-11 17:47:00 +0700
categories: ["Cryptography", "Crypto · Elliptic Curves"]
tags: [cryptography, ecdsa, nonce-reuse, secp256k1]
render_with_liquid: false
---

ECDSA is strong, but all of its security hangs on one thing. The nonce `k` must be random, secret, and different on every signature. If two different messages are signed with the same `k`, or if two signatures merely happen to share `k`, an attacker solves for `k` and then for the private key `d`. This flaw has broken the PlayStation 3 and several Bitcoin wallets. This lesson gives you the formula, a demo that runs on a small curve, and a lab that recovers a real private key on secp256k1.

![ECDSA nonce reuse recovers the private key](/assets/img/crypto/crypto-8-2-ecdsa-nonce-reuse.svg)
_Two signatures with the same r share the nonce k. Subtracting the two s values gives k, and k gives d._

**Prerequisites:** Lesson 8.1 (ECC, ECDSA signing and verifying), Lesson 1.1 (modular inverse). You should be comfortable with the formula `s = k^(-1)(z + r*d)`.

**Tools:** Python 3 + PyCryptodome (for the AES decryption in the lab). Install with `pip install pycryptodome`. The solved lab is described in the Lab section below.

## Goals

You will see why reusing the nonce `k` leaks `k` and then the private key `d`, and derive the formula. You will spot nonce reuse just by looking at two signatures, where `r` is the same. You will code the recovery of `d` from two signatures with the same `k`, running on a small curve. And you will recover a real private key on secp256k1 in the lab and decrypt the flag.

## Theory

### Why nonce reuse breaks ECDSA

Recall the signing formula from Lesson 8.1. With hash `z`, nonce `k`, and `r = (k*G).x mod n`, the signature is `(r, s)` with

```
s = k^(-1) * (z + r*d)  mod n
```

Now sign two different messages (hashes `z1`, `z2`) with the same `k`. Since `r` depends only on `k*G`, the same `k` gives the same `r`. The two signatures are:

```
s1 = k^(-1) * (z1 + r*d)  mod n
s2 = k^(-1) * (z2 + r*d)  mod n
```

Subtract the two: `s1 - s2 = k^(-1) * (z1 - z2) mod n`. Only one unknown `k` remains, and it solves directly:

```
k = (z1 - z2) * (s1 - s2)^(-1)  mod n
```

With `k` known, substitute into the first equation to get `d`:

```
d = (s1*k - z1) * r^(-1)  mod n
```

All of this is arithmetic mod `n`, with no curve operation at all. The flaw is in how `k` is generated, but the consequence is permanent loss of the signing key.

### How to recognize it

The clearest sign is two signatures on different messages that have the same `r`. Since `r = (k*G).x mod n`, a repeated `r` almost certainly means a repeated `k` (the chance of a random collision is `1/n`, which is tiny). In a CTF, a set of signatures where two share `r` should make you think of this attack at once. In real systems the flaw usually comes from a bad RNG (a wrongly deterministic `k`), cloned virtual machines that restore the same RNG state, or a programmer hardcoding `k` for convenience.

### Variants

Nonce bugs are not only about reuse. If `k` is biased, for example the top few bits are always 0, then collecting many signatures and building a lattice (HNP, the hidden number problem) also extracts `d`, but it needs tools like Sage and LLL, which are outside this lesson. If `k` is small or predictable (a weak RNG), guess `k` and apply the formula above with a single signature. This lesson focuses on reuse because it is simple, can be done by hand, and is the most common.

## Demo

### Recovering the private key on a small curve

We reuse the curve from Lesson 8.1 (`p = 97, a = 3, b = 2`, `G = (0, 14)`, `n = 103`) with private key `d = 42`. We sign two different messages with the same `k = 23` and then break it.

```python
# d82_demo.py: ECDSA leaks the private key when nonce k is reused (on the small curve from Lesson 8.1)
import hashlib

p, a, b = 97, 3, 2
INF = None
G = (0, 14)
n = 103

def point_add(P, Q):
    if P is INF: return Q
    if Q is INF: return P
    x1, y1 = P; x2, y2 = Q
    if x1 == x2 and (y1 + y2) % p == 0: return INF
    if P == Q:
        m = (3 * x1 * x1 + a) * pow(2 * y1, -1, p) % p
    else:
        m = (y2 - y1) * pow(x2 - x1, -1, p) % p
    x3 = (m * m - x1 - x2) % p
    y3 = (m * (x1 - x3) - y1) % p
    return (x3, y3)

def scalar_mul(k, P):
    R = INF; Q = P
    while k > 0:
        if k & 1: R = point_add(R, Q)
        Q = point_add(Q, Q); k >>= 1
    return R

def H(msg):
    return int.from_bytes(hashlib.sha256(msg).digest(), "big") % n

d = 42                       # secret signing key (the recovery target)
Q = scalar_mul(d, G)

def sign(msg, k):
    z = H(msg)
    r = scalar_mul(k, G)[0] % n
    s = (pow(k, -1, n) * (z + r * d)) % n
    return (r, s)

# --- sign TWO different messages with the SAME k (fatal mistake) ---
k = 23
m1, m2 = b"send 10 BTC to Alice", b"send 20 BTC to Bob"
r1, s1 = sign(m1, k)
r2, s2 = sign(m2, k)
print("signature 1: r =", r1, "s =", s1)
print("signature 2: r =", r2, "s =", s2)
print("r equal?", r1 == r2, "  <- sign of nonce reuse")

# --- attack: from two signatures with the same r, solve for k and then d ---
z1, z2 = H(m1), H(m2)
r = r1
k_rec = (z1 - z2) * pow(s1 - s2, -1, n) % n       # k = (z1 - z2) / (s1 - s2)
d_rec = (s1 * k_rec - z1) * pow(r, -1, n) % n     # d = (s1*k - z1) / r
print("recovered k =", k_rec, "(real:", k, ")")
print("recovered d =", d_rec, "(real:", d, ")")
print("correct?", d_rec == d and scalar_mul(d_rec, G) == Q)
```

Output:

```
signature 1: r = 19 s = 39
signature 2: r = 19 s = 73
r equal? True   <- sign of nonce reuse
recovered k = 23 (real: 23 )
recovered d = 42 (real: 42 )
correct? True
```

The two signatures have the same `r = 19` even though the messages differ, and that is the red flag. From there the formula pulls out `k = 23` and then `d = 42`, exactly the private key, and checking `d*G == Q` confirms it. The ECDLP is never touched, only a few modular divisions mod `n`.

### The solved lab on secp256k1

The Lab section below has the real version. It has two ECDSA signatures on secp256k1 (the Bitcoin curve) that share the same nonce, plus a flag encrypted with AES-GCM under a key derived from the private key. `solve.py` is self-contained, applies exactly the formula above to recover the 256-bit `d`, and decrypts the real flag. The formula is identical to the small demo, only `n` is the secp256k1 group order.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 8.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/8.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/8.2/solve.py" download><i class="fa-solid fa-file-code"></i>solve.py</a>
</div>
</div>

- Task: secp256k1, two messages `m1`, `m2` with signatures `(r, s1)` and `(r, s2)` that share `r`, and one AES-GCM ciphertext with a tag. The AES key is `sha256(str(d))`. Recover `d` and decrypt the flag `ECC{...}`.
- Files: `solve.py`, `README.md`, `transcript.txt`.
- Hints in steps: (1) compute `z1 = sha256(m1) mod n`, and `z2` the same way; (2) `k = (z1 - z2) * inverse(s1 - s2, n) mod n`; (3) `d = (s1*k - z1) * inverse(r, n) mod n`; (4) `key = sha256(str(d).encode()).digest()` then `AES.new(key, AES.MODE_GCM, nonce=...).decrypt_and_verify(ct, tag)`.
- Extension: write a function that scans a list of signatures, finds the pair with the same `r` by itself, then applies the attack. This is the realistic scenario when you hold many signatures from a service.
- Done when you get the correct private key `d` (check `d*G == Q`) and decrypt the flag `ECC{...}`.

## Key takeaways

- Two signatures on different messages with the same `r` mean the same nonce `k`. That is the only sign you need to look for.
- `k = (z1 - z2) / (s1 - s2) mod n`, then `d = (s1*k - z1) / r mod n`. All arithmetic is mod `n`.
- Leaking the `k` of a single signature is also enough to get `d`: `d = (s*k - z) / r mod n`.
- Defense: generate `k` deterministically following RFC 6979 (from `d` and the message), or use Ed25519 (deterministic nonces are part of its design).
- Nonce bugs are not only reuse. A nonce biased by a few bits can also be broken with a lattice (HNP), but that needs Sage.

## Common pitfalls

- Forgetting to reduce the hash mod `n`. The `z` in ECDSA is the hash truncated and reduced into `[0, n)`. Using the raw hash without reducing it skews the formula and gives a wrong `d`.
- Mixing `mod p` with `mod n`. Every operation in this attack is by the group order `n`, not the field prime `p`. Using the wrong modulus breaks it.
- Assuming a repeated `r` is enough with different signers. This lesson assumes the same signer. If two signatures share `r` but come from different signers, the attack does not apply (rare, and not meaningful in practice).
- The minus sign when computing `s1 - s2` can give a negative number. Python handles `pow(x, -1, n)` for negative numbers through the modulus, but if you write your own inverse, bring the value into `[0, n)` first.
- Thinking ECDSA being secure means you can ignore the nonce. The nonce is the weakest part. Pick Ed25519 or RFC 6979 so you do not have to generate `k` yourself.

## Further reading

- fail0verflow, the talk on the PS3 (reused ECDSA nonces exposed Sony's firmware signing key), a classic real-world example.
- RFC 6979, Deterministic ECDSA, a safe way to generate `k` deterministically from the key and the message.
- CryptoHack, the "Elliptic Curves" group, the ECDSA and nonce challenges, and the hidden number problem challenges if you want to try lattices.
- Nguyen, Shparlinski, "The Insecurity of the Elliptic Curve DSA with Partially Known Nonces", the theory behind the biased nonce attack.
