---
title: "Lesson 11.2: Writing a Crypto CTF Writeup for ECDSA Nonce Reuse"
image:
  path: /assets/img/covers/crypto-11-2-writing-crypto-ctf-writeup-ecdsa.webp
  alt: "Writing a Crypto CTF Writeup for ECDSA Nonce Reuse"
date: 2023-12-19 04:38:00 +0700
categories: ["Cryptography", "Crypto · Real-World Practice"]
tags: [cryptography, ecdsa, nonce-reuse, ctf-writeup]
render_with_liquid: false
---

Solving a challenge is half the work. Writing it up so others can follow is the other half, and it is the half that makes you remember it and improve. This lesson covers a process for recognising the type of a crypto challenge, a from-scratch checklist, how to write a short but complete writeup, and then a full sample writeup for an ECDSA nonce reuse challenge with solve code that really runs and prints the flag.

![ECDSA nonce reuse, from two signatures to the key](/assets/img/crypto/crypto-11-2-writing-crypto-ctf-writeup-ecdsa.svg)
_Two signatures with the same r give k, and k gives the private key d._

Part: 11 (Real-World Practice) | Time: about 75 minutes | Difficulty: hard

**Prerequisites:** Lesson 1.1 (modular arithmetic, inverses), Lesson 8.1 (ECC, ECDSA), and Lesson 8.2 (ECDSA nonce reuse) if available. This lesson is a direct application of the nonce reuse attack.

**Tools:** Python 3 and PyCryptodome (`bytes_to_long`, `long_to_bytes`). The ECDSA math is written by hand and needs no curve library.

## Goals

By the end of this lesson you have a recognition process that tells you whether a challenge is RSA, XOR, ECC, or something else. You know what a good writeup contains and how to make it reproducible. You can prove the formula that recovers the private key from ECDSA nonce reuse, and you can solve a full ECDSA challenge to the flag with running code.

## Theory

### Recognising the type of a crypto challenge

Before typing code, read the challenge and classify it. A few questions, in order:

1. What files are given? A `pubkey.pem` or an (n, e, c) triple is RSA. A curve and some points is ECC. A bare blob of hex or base64 is encoding or XOR. An `iv` and 16-byte blocks mean a block cipher.
2. Are there any big numbers? An n of several hundred digits is RSA or discrete log. Numbers tied to "curve", "G", "P" are ECC.
3. Is anything repeated? Two ciphertexts with the same structure, two signatures with the same r, or a nonce that shows up twice all point to nonce reuse or key reuse.
4. Is there an oracle? A server that answers true or false about something (padding, a comparison, timing) means an oracle attack.
5. Is the code home-made? If the challenge ships a server.py or a hand-written cipher, read it closely. The bug is almost always one wrong design decision (ECB, fixed nonce, wrong MAC use).

For ECDSA specifically there are two deadly signs. One is two signatures on different messages with the same r (a reused nonce). The other is a nonce generated from a weak source (time, a counter, a bad PRNG). When you see the same r, the challenge is almost solved.

### What a good writeup contains

The minimum structure that lets a reader reproduce your work:

- Challenge: a summary of what is given and what you must find. Paste the important parameters.
- Recognition: why you concluded this is this kind of attack. Point to the concrete sign (for example "r1 == r2, so the nonce was reused").
- Attack theory: the formula and a short proof of why it recovers the secret. This is the part that makes a writeup worth more than a block of code.
- Exploit code: a script that runs end to end, so that pasting it gives the flag.
- Flag and wrap-up: the real flag, plus one line on the lesson (what the root bug is and how to prevent it).

The main rule is that the reader must be able to reproduce the result from the writeup alone, without asking you. Also be honest about where you got stuck. A writeup that includes the wrong turns is often worth more than one with only a clean solution.

### The math of ECDSA nonce reuse

A quick recap of ECDSA (Lesson 8.1). Take a curve with generator point G of order n, private key d, and public key P = d·G. To sign a message m:

- Compute z = Hash(m), reduced mod n.
- Pick a random nonce k, compute the point R = k·G, and take r = R.x mod n.
- Compute s = k^(-1)·(z + r·d) mod n.
- The signature is (r, s).

The nonce k must be secret and used only once. Suppose two different messages m1 and m2 are signed with the same k. Then r is the same (r depends only on k), and:

```
s1 = k^(-1) (z1 + r d)  (mod n)
s2 = k^(-1) (z2 + r d)  (mod n)
```

Subtracting the two sides gives s1 - s2 = k^(-1) (z1 - z2), which yields k directly:

```
k = (z1 - z2) * (s1 - s2)^(-1)   (mod n)
```

With k known, substitute into the first equation. s1·k = z1 + r·d, so d is:

```
d = (s1 k - z1) * r^(-1)   (mod n)
```

Two lines of modular arithmetic, and the private key falls out. There is no need to break the discrete log and no lattice is needed. All the strength of ECDSA is lost because one nonce was reused. This is exactly the mistake that got the Sony PS3 cracked and drained many Bitcoin wallets.

## Demo

### The challenge

The server signs on secp256k1. It publishes the public key and two signatures for two different messages. Look closely and the r values of the two signatures are equal. The private key is the flag encoded as a number. Find the flag.

The parameters and real output of the "server" (`chall.py` in the Lab section below):

```
m1 = b'transfer 10 coins to alice'
r1 = 0xcdf0e3eec0fa477bd838b85049e6b991b5ab21904a64d953b42ee1486e53858e
s1 = 0xb62fcafc13530506eb1a304131da3c7c49bb31ebd186007a8659ae3e37c053e0
m2 = b'transfer 99 coins to mallory'
r2 = 0xcdf0e3eec0fa477bd838b85049e6b991b5ab21904a64d953b42ee1486e53858e
s2 = 0x5db9a313c891fe387c4b5e8cbea17916f8f4c20f6c459807e228742b4f4ad249
r1 == r2 ? True
```

### Recognition

The sign is right on the surface: `r1 == r2` while `m1 != m2`. Since r depends only on the nonce k, equal r values mean the same k was used for both signatures. This is ECDSA nonce reuse, and by the math above we recover d with two modular divisions. The hash is SHA-256. It must match the function the server used exactly, otherwise z is wrong and d comes out as garbage.

### Exploit code

```python
# solve.py: recover the private key from ECDSA nonce reuse, then read the flag
import hashlib
from Crypto.Util.number import bytes_to_long, long_to_bytes

n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141  # order of secp256k1

def H(msg):
    return bytes_to_long(hashlib.sha256(msg).digest()) % n

def recover(m1, r, s1, m2, s2):
    z1, z2 = H(m1), H(m2)
    # s1 - s2 = k^-1 (z1 - z2)  => k = (z1 - z2)/(s1 - s2) mod n
    k = (z1 - z2) * pow(s1 - s2, -1, n) % n
    # s1 k = z1 + r d           => d = (s1 k - z1)/r mod n
    d = (s1 * k - z1) * pow(r, -1, n) % n
    return k, d

m1 = b"transfer 10 coins to alice"
m2 = b"transfer 99 coins to mallory"
r  = 0xcdf0e3eec0fa477bd838b85049e6b991b5ab21904a64d953b42ee1486e53858e
s1 = 0xb62fcafc13530506eb1a304131da3c7c49bb31ebd186007a8659ae3e37c053e0
s2 = 0x5db9a313c891fe387c4b5e8cbea17916f8f4c20f6c459807e228742b4f4ad249

k, d = recover(m1, r, s1, m2, s2)
print("recovered nonce k :", hex(k))
print("private key d      :", hex(d))
print("flag               :", long_to_bytes(d).decode())
```

Output:

```
recovered nonce k : 0x1337c0debeef1337c0debeef1337c0debeef
private key d      : 0x666c61677b65636473615f6b5f7265753565217d
flag               : flag{ecdsa_k_reu5e!}
```

### Flag and lesson

The flag is `flag{ecdsa_k_reu5e!}`. The private key d, converted to bytes, is the flag. That is how the challenge embeds the answer. The recovered nonce is `0x1337c0debeef...`, which is the value the server reused (you can see it in `chall.py`).

The root lesson is that an ECDSA nonce must be truly random and must never repeat. The RFC 6979 standard fixes this completely by generating the nonce deterministically from the private key and the message. This removes the risk of a bad PRNG and guarantees no repeat across different messages. This is why every modern signing library uses RFC 6979.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 11.2</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/11.2.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/11.2/chall.py" download><i class="fa-solid fa-file-code"></i>chall.py</a>
<a class="lab-file" href="/assets/labs-crypto/11.2/solve.py" download><i class="fa-solid fa-file-code"></i>solve.py</a>
</div>
</div>

- Task: `chall.py` generates the challenge (it writes `sigs.txt`) and `solve.py` solves it. Run `python3 chall.py && python3 solve.py` and you must get `flag{ecdsa_k_reu5e!}`.
- Write the writeup yourself: using the structure in the "What a good writeup contains" section, rewrite this lesson in your own words, with a proof of the two formulas for k and d. The goal is that someone who has not learned ECDSA can still reproduce it.
- Variation to practise: edit `chall.py` so the two messages use two different nonces (the fix), run `solve.py`, and watch it output a garbage d. Understand why, since when `r1 != r2` the formula does not apply.
- Try another type: replace the ECDSA challenge with an RSA Wiener or common modulus challenge (from Part 6), then write the writeup in the same frame. This practises recognition and presentation.
- Hints, step by step: (1) check `r1 == r2` first; (2) remember to reduce z mod n; (3) the hash function must match the server; (4) use `pow(x, -1, n)` for the modular inverse (Python 3.8 or later).
- Done when: the code prints the right flag and you have a writeup file that others can read and follow.

## Key takeaways

- Recognise first, code second. Classify the challenge from the files, numbers, repetition, and oracles.
- ECDSA: two signatures with the same r on different messages mean nonce reuse, and the challenge is almost solved.
- Formulas: k = (z1 - z2)/(s1 - s2) mod n, then d = (s1·k - z1)/r mod n.
- z must be reduced mod n, and the hash must match the one the server uses.
- A good writeup has: the challenge, recognition, theory with proof, code, flag, and the lesson.
- Prevent nonce reuse with the deterministic nonce of RFC 6979.

## Common pitfalls

- Forgetting to reduce z mod n, or using the wrong hash (SHA-1 vs SHA-256). With a wrong z, d is garbage even though the formula is right.
- Confusing the curve order n with the field modulus p. All signature operations are mod n (the group order), not mod p.
- Using the wrong inverse. It must be `pow(s1 - s2, -1, n)`, and note that `s1 - s2` can be negative. Python handles it mod n, but it is still good to apply `% n`.
- Thinking you need to break the discrete log to get d. You do not. Nonce reuse turns it into trivial arithmetic, so do not take a detour.
- Writing a writeup that only pastes code with no explanation. The reader, and you after three months, will not know why it works.
- Hiding the wrong turns. A writeup that includes where you got stuck and how you got out is usually more useful than a polished solution alone.

## Further reading

- RFC 6979 (deterministic ECDSA). Read it to see how nonce reuse is blocked at the root.
- The Sony PS3 break (fail0verflow, 2010) and the Bitcoin wallet thefts caused by nonce reuse are real examples of this exact bug.
- Lessons 8.1 and 8.2 in this series cover the ECC basics and the details of the nonce reuse attack.
- The CryptoHack "Elliptic Curves" section and ECDSA challenges from many CTFs give more practice.
- Blogs from strong CTF teams (for example write-ups from pwndevils and Super Guesser) show how to present a crypto writeup professionally.
