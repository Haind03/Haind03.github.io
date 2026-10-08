---
title: "Lesson 6.5: RSA Padding, PKCS#1 v1.5, Bleichenbacher and OAEP"
image:
  path: /assets/img/covers/crypto-6-5-rsa-padding-pkcs1-bleichenbacher-oaep.webp
  alt: "RSA Padding, PKCS#1 v1.5, Bleichenbacher and OAEP"
date: 2023-08-29 23:00:00 +0700
categories: ["Cryptography", "Crypto · RSA"]
tags: [cryptography, rsa, padding-oracle, bleichenbacher]
render_with_liquid: false
---

Textbook RSA is deterministic and purely multiplicative, so it leaks information and falls to many attacks. Padding exists to fix that by adding randomness and structure to the message before encryption. But badly done padding is worse than none, and PKCS#1 v1.5 is the classic example. In 1998 Bleichenbacher showed that an oracle that only answers "is the padding valid or not" is enough to decrypt any ciphertext. This lesson explains the PKCS#1 v1.5 structure, the idea of the padding oracle attack with working code on a small key, and how OAEP does it correctly.

![PKCS#1 v1.5 block layout and the Bleichenbacher oracle loop](/assets/img/crypto/crypto-6-5-rsa-padding-pkcs1-bleichenbacher-oaep.svg)
_The attacker sends modified ciphertexts and uses each yes/no answer to narrow the interval that contains m._

Part: 6 (RSA) | Time: about 55 minutes | Difficulty: hard

**Prerequisites:** Lessons 6.1 and 6.2. It helps to read Lesson 4.3 first (padding oracle on CBC), so you see the same oracle idea in an RSA setting.

**Tools:** Python 3 with gmpy2 and PyCryptodome. Install with `pip install gmpy2 pycryptodome`.

## Goals

After this lesson you can:

- Draw the byte-by-byte structure of a PKCS#1 v1.5 encryption block.
- Explain what a padding oracle is and why a single yes/no bit is a fatal vulnerability.
- Understand Bleichenbacher's three-step idea (blinding, narrowing the interval, convergence) and run an implementation on a small key.
- Know what OAEP does differently and why it stops this class of attack.

## 1. Theory

### 1.1. Why padding is needed

Textbook RSA `c = m^e mod n` has two problems. First, it is deterministic. The same m gives the same c, so an attacker can compare ciphertexts and build a lookup table of likely messages (for example "yes"/"no", or a short PIN). Second, it is purely multiplicative (malleable). Since `(m1*m2)^e = c1*c2`, an attacker can transform a ciphertext at will and create relations between plaintexts. Padding adds randomness to remove determinism, and adds structure to detect tampering.

### 1.2. PKCS#1 v1.5 for encryption

The PKCS#1 v1.5 standard (RFC 2313) formats the encryption block to exactly k bytes (k is the byte length of n) like this:

```
00 || 02 || PS || 00 || M
```

- The first `00` byte makes sure the numeric value is smaller than n.
- The `02` byte identifies encryption mode (signing mode uses `01`).
- `PS` (padding string) is random non-zero bytes, at least 8 bytes long. This is the random part that removes determinism.
- The `00` byte is a separator that marks the end of padding and the start of the message.
- `M` is the real message (often an AES session key).

On decryption the receiver checks that the first two bytes are `00 02`, that there are at least 8 non-zero PS bytes, and that a `00` separator exists. If any check fails, the standard says to return an error. That is where the trouble starts.

### 1.3. Padding oracle: one bit is enough

A padding oracle is any behavior of the system that reveals whether a ciphertext decrypts to a valid PKCS#1 v1.5 block. It can be a different error code, a different error message, or only a different response time. The attacker does not need the content, only this yes/no signal.

The key point is that RSA is multiplicative. The attacker can multiply the target ciphertext c by `s^e` to get `c' = c * s^e = (m*s)^e mod n`. Send c' to the oracle. If it says "valid padding", then `m*s mod n` starts with the two bytes `00 02`, so `m*s mod n` lies in the interval `[2B, 3B)` with `B = 2^(8*(k-2))`. Each yes answer gives the attacker one inequality about m. After collecting enough inequalities, the interval containing m shrinks to a single point.

### 1.4. The Bleichenbacher algorithm (idea)

Let `B = 2^(8*(k-2))`. A valid block starting with `00 02` means `2B <= m < 3B`. The attack looks for integers s such that `c * s^e mod n` is still valid, and each valid s gives one constraint. There are three main steps:

1. Blinding: if the target c is not known to be valid, find a random s0 so that `c*s0^e` is valid and use that as the starting point. Usually c is already valid (it is a real ciphertext), so this step is trivial.
2. Narrowing the interval: keep a set of intervals M that contain the possible values of m. Find the next smallest s that makes the oracle say yes. When M has only one interval left, use the jump formula with r to speed up, instead of trying each s.
3. Convergence: each valid s cuts M down using the system `2B <= m*s - r*n < 3B`. Repeat until M shrinks to a single point, and that point is m.

In practice this costs a few hundred thousand to a few million oracle queries for RSA-1024, which is entirely feasible. A modern variant (ROBOT, 2017) showed the flaw is still alive in many TLS devices, decades later.

### 1.5. OAEP done correctly

OAEP (Optimal Asymmetric Encryption Padding, PKCS#1 v2) replaces the predictable linear padding with a two-round Feistel-like mixing structure that uses two hash functions (mask generation functions). It has two important properties:

- All-or-nothing: unless the whole structure is decoded correctly, no piece of information comes out. One wrong bit turns the entire decryption into indistinguishable garbage.
- Randomization by a seed: encrypting the same message twice gives two different ciphertexts, so it is no longer deterministic.

As a result, the "is the padding valid" oracle of OAEP cannot confine m to a numeric interval the way PKCS#1 v1.5 can, so Bleichenbacher does not apply. OAEP has a security proof in the random oracle model when used correctly. In practice, new RSA encryption always uses OAEP, and signatures use PSS.

## 2. Demo

### 2.1. Building a PKCS#1 v1.5 block and an oracle

```python
# pkcs15.py: build a PKCS#1 v1.5 block and a padding oracle
import os
from Crypto.Util.number import getPrime, inverse, bytes_to_long, long_to_bytes

bits = 256                              # small key so the demo runs fast
p = getPrime(bits // 2); q = getPrime(bits // 2); n = p * q
while n.bit_length() != bits:
    p = getPrime(bits // 2); q = getPrime(bits // 2); n = p * q
e = 65537; d = inverse(e, (p - 1) * (q - 1))
k = (n.bit_length() + 7) // 8           # byte length of n

def pkcs15_pad(msg):
    ps_len = k - 3 - len(msg)
    ps = bytes(b or 1 for b in os.urandom(ps_len))  # padding with no zero bytes
    return b"\x00\x02" + ps + b"\x00" + msg

def oracle(ct):
    # oracle only returns whether the first two bytes are 00 02
    em = long_to_bytes(pow(ct, d, n), k)
    return em[0] == 0 and em[1] == 2

msg = b"hi!"
em = pkcs15_pad(msg)
m = bytes_to_long(em)
c = pow(m, e, n)
print("valid block?", oracle(c))        # True
```

The oracle above deliberately returns a single bit, valid or not. That is all Bleichenbacher needs.

### 2.2. Full Bleichenbacher on a small key

The implementation below decrypts c using only calls to `oracle`, never using d directly (d lives only inside the oracle, which plays the role of the victim server).

```python
# bleichenbacher.py: decrypt through the padding oracle (continues pkcs15.py)
import gmpy2

B = 2 ** (8 * (k - 2))
def ceildiv(a, b):
    return -(-a // b)

def attack(c):
    # step 1: find the first s that makes the oracle say yes (the real c is usually already valid so s is small)
    s = ceildiv(n, 3 * B)
    while not oracle((c * pow(s, e, n)) % n):
        s += 1
    M = [(2 * B, 3 * B - 1)]             # initial interval containing m
    s_i = s
    while True:
        if len(M) > 1:
            # several intervals left: search the next s sequentially
            s_i += 1
            while not oracle((c * pow(s_i, e, n)) % n):
                s_i += 1
        else:
            # only one interval left: jump by r for speed
            a, b = M[0]
            r = ceildiv(2 * (b * s_i - 2 * B), n)
            found = False
            while not found:
                s_lo = ceildiv(2 * B + r * n, b)
                s_hi = (3 * B + r * n) // a
                s_i = s_lo
                while s_i <= s_hi:
                    if oracle((c * pow(s_i, e, n)) % n):
                        found = True
                        break
                    s_i += 1
                if not found:
                    r += 1
        # narrow the interval set M using the s_i just found
        newM = set()
        for (a, b) in M:
            r_lo = ceildiv(a * s_i - 3 * B + 1, n)
            r_hi = (b * s_i - 2 * B) // n
            for r in range(r_lo, r_hi + 1):
                na = max(a, ceildiv(2 * B + r * n, s_i))
                nb = min(b, (3 * B - 1 + r * n) // s_i)
                if na <= nb:
                    newM.add((na, nb))
        M = list(newM)
        if len(M) == 1 and M[0][0] == M[0][1]:
            return M[0][0]              # converged to a single point = m

rec = attack(c)
print("recovered correctly?", rec == m)
print("plaintext:", long_to_bytes(rec, k))
```

Running it right after section 2.1 prints:

```
recovered correctly? True
plaintext: b'\x00\x02...<random padding>...\x00hi!'
```

The recovered block starts with `00 02`, followed by random padding, a `00` byte, then `hi!`. Split after the last `00` byte of the padding to get the message. The whole process only calls `oracle`, which shows that one yes/no bit is enough. This uses a 256-bit key for speed. RSA-1024 takes more queries, but the principle is the same.

### 2.3. OAEP: randomized and all-or-nothing

```python
# oaep.py: OAEP randomizes and resists malleability
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

key = RSA.generate(2048)
pub = key.publickey()

c1 = PKCS1_OAEP.new(pub).encrypt(b"same")
c2 = PKCS1_OAEP.new(pub).encrypt(b"same")
print("are the two ciphertexts different?", c1 != c2)   # True: because of the random seed
print(PKCS1_OAEP.new(key).decrypt(c1))      # b'same'
```

Encrypting the same `b"same"` twice gives two completely different ciphertexts, thanks to the random seed inside OAEP. It is no longer deterministic, and there is no numeric interval for Bleichenbacher to work on.

## 3. Lab

- Task 1 (understand the oracle): change the oracle in section 2.1 so it answers through response time (sleep longer when the padding is valid) instead of returning a bool. Rewrite the attack to read the timing signal. The point is that an oracle is not necessarily an error code.
- Task 2 (run it for real): you get a simulated endpoint (the script `server.py` in the Lab section below) that takes a ciphertext and returns yes/no. Use Bleichenbacher to recover the plaintext of a given ciphertext.
- Task 3 (compare): encrypt the same flag 100 times with textbook RSA, with PKCS#1 v1.5 and with OAEP. Count the identical ciphertexts in each case and explain the numbers.
- Hints, in order: (1) for a timing oracle, take the median of several measurements to filter noise; (2) the larger the key, the longer the attack, so start with a small key; (3) remember `B = 2^(8*(k-2))`.
- Done when: you recover the plaintext in task 2, and the count table in task 3 is correct (textbook: 100 identical, OAEP: 0 identical).
- Materialized lab: the Lab section below has `server.py` (a PKCS#1 v1.5 oracle with a 256-bit key for speed) and `solve.py` (full Bleichenbacher, recovering `flag{pkcs1_v15_bb}`). Measured runs take from a few seconds to over a minute, roughly tens to hundreds of thousands of queries depending on the random key. See `transcript.txt`.

## 4. Key takeaways

- The PKCS#1 v1.5 encryption block is `00 02 || PS (>=8 non-zero bytes) || 00 || M`, exactly k bytes long.
- A padding oracle is any way of revealing "padding valid or not", including through timing or error codes.
- The multiplicative property `c*s^e = (m*s)^e` is the lever. Each valid s gives an interval constraint on m.
- `B = 2^(8*(k-2))`, and a valid block means `2B <= m < 3B`. Collect constraints until M shrinks to one point.
- OAEP is randomized and all-or-nothing, and it blocks Bleichenbacher. For new work use OAEP for encryption and PSS for signatures.

## 5. Common pitfalls

- Believing that hiding error messages is enough. Timing is also an oracle. The correct defense is constant-time decryption that always behaves the same way even when the padding is wrong (see the Bleichenbacher countermeasure section of RFC 5246), not hiding the error code.
- Computing `B` or `k` wrongly. k is the byte length of n (`(bit_length+7)//8`) and B is `2^(8*(k-2))`. Being off by one byte makes every inequality wrong and the attack never converges.
- Treating signature padding as if it were encryption padding. Signing mode uses the byte `01` and `FF` padding, which is different from encryption mode (`02`, random padding). Do not mix them up.
- Thinking OAEP is immune to everything. OAEP blocks Bleichenbacher-style padding attacks, but a sloppy implementation can still leak through side channels when it distinguishes decryption errors. Security depends on both the standard and the implementation.
- Using the same RSA key for both PKCS#1 v1.5 encryption and signing. Do not. Separate keys by purpose, and drop v1.5 entirely when you can.

## 6. Further reading

- Bleichenbacher, "Chosen Ciphertext Attacks Against Protocols Based on the RSA Encryption Standard PKCS #1" (CRYPTO 1998), the original paper, readable and well worth reading.
- "Return Of Bleichenbacher's Oracle Threat" (ROBOT, 2017), which shows the 1998 flaw still alive in modern TLS.
- RFC 8017 (PKCS#1 v2.2) for the OAEP and PSS specification.
- CryptoHack, the "RSA" section on padding, and related TLS challenges.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 6.5</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/6.5.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/6.5/server.py" download><i class="fa-solid fa-file-code"></i>server.py</a>
<a class="lab-file" href="/assets/labs-crypto/6.5/solve.py" download><i class="fa-solid fa-file-code"></i>solve.py</a>
</div>
</div>
