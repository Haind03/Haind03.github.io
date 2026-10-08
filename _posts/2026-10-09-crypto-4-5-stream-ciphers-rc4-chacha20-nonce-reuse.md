---
title: "Lesson 4.5: Stream ciphers, RC4, ChaCha20 and nonce reuse"
image:
  path: /assets/img/covers/crypto-4-5-stream-ciphers-rc4-chacha20-nonce-reuse.webp
  alt: "Stream ciphers, RC4, ChaCha20 and nonce reuse"
date: 2026-10-09 12:25:00 +0700
categories: ["Cryptography", "Crypto · Symmetric Encryption"]
tags: [cryptography, stream-cipher, nonce-reuse, chacha20]
render_with_liquid: false
---

A stream cipher encrypts by generating a keystream and XORing it into the plaintext, exactly like a one-time pad, except that the keystream comes from an algorithm instead of true randomness. It is compact, fast and needs no padding. It also has one fatal weakness, which is reusing a nonce. A repeated nonce turns the cipher into a two-time pad, and a two-time pad can be solved by hand. CTR from Lesson 4.2 is also a stream cipher, so this attack applies to CTR, RC4 and ChaCha20 alike.

![Stream ciphers, RC4, ChaCha20 and nonce reuse](/assets/img/crypto/crypto-4-5-stream-ciphers-rc4-chacha20-nonce-reuse.svg)
_With one keystream used twice, XORing the two ciphertexts removes the key and leaves P1 XOR P2._

Part 4 (Symmetric Encryption) | Time: about 40 minutes | Difficulty: medium

**Prerequisites:** Lesson 3.1 (XOR), Lesson 3.2 (one-time pad and why key reuse breaks it), Lesson 4.2 (CTR mode).

**Tools:** Python 3 and PyCryptodome.

## Goals

After this lesson you understand that a stream cipher is a keystream generator followed by an XOR, and that CTR is a stream cipher built from a block cipher. You know that RC4 is old and why it was retired, and that ChaCha20 is the one to use today. You can show that reusing a nonce gives C1 XOR C2 = P1 XOR P2, which means the keystream cancels. You can recover plaintext from two ciphertexts that share a keystream, using known plaintext and using crib dragging. You can recognize a nonce reuse challenge in a CTF and know how to prevent it.

## 1. Theory

### What a stream cipher does

A stream cipher produces a pseudorandom byte sequence called the keystream from a key (and a nonce), then encrypts with XOR:

```
Ci = Pi XOR keystream_i
```

Decryption regenerates the same keystream and XORs again, because XORing the same value twice cancels out. The difference from a one-time pad is that the one-time pad keystream is truly random, as long as the message, and used once. The keystream of a stream cipher is pseudorandom, generated from a short key, so it is not theoretically perfect, but it is good enough when used correctly.

CTR mode (Lesson 4.2) is a stream cipher because it encrypts a counter to produce the keystream `E(nonce||counter)`. So everything said here about nonce reuse also applies to AES-CTR, AES-GCM (because GCM uses CTR inside), RC4, ChaCha20 and Salsa20. They share one weakness.

### RC4: a legacy you should recognize and not use

RC4 is an old stream cipher that was used in WEP, WPA-TKIP and SSL/TLS. It has no explicit nonce and takes only a key, so the keystream depends entirely on the key. As a result, encrypting two messages with the same RC4 key repeats the keystream immediately, giving a two-time pad. Worse, the RC4 keystream has statistical bias, especially in the first bytes, which is enough to recover plaintext when many ciphertexts are collected (the 2013 attack on HTTP cookies over TLS). RC4 has been prohibited in TLS since 2015. In CTFs you still meet RC4 in old protocol analysis or reverse engineering tasks, so you need to recognize it, but never choose RC4 for real work.

### ChaCha20: the modern choice

ChaCha20 is a modern stream cipher by Daniel Bernstein. It is fast in software, needs no AES hardware, and is easy to run in constant time, so it is less exposed to timing side channels. It takes a 32-byte key and a nonce (8 or 12 bytes depending on the variant) and generates the keystream by repeating a mixing function over a 512-bit state. Combined with the Poly1305 MAC it forms ChaCha20-Poly1305, an AEAD (authenticated encryption) widely used by TLS 1.3 and WireGuard. Note that ChaCha20 is still a stream cipher, so it also breaks if a nonce is reused with the same key. Being modern does not remove the risk, and only nonce discipline protects you.

### Nonce reuse creates a two-time pad

This is the core of the lesson. Suppose we encrypt two plaintexts P1 and P2 with the same key and the same nonce, so the keystream K is identical:

```
C1 = P1 XOR K
C2 = P2 XOR K
```

XOR the two ciphertexts:

```
C1 XOR C2 = (P1 XOR K) XOR (P2 XOR K) = P1 XOR P2
```

The keystream K cancels completely. Now we hold `P1 XOR P2`, which no longer involves any key. This is the two-time pad situation that Lesson 3.2 warned about for the one-time pad, namely that reusing a keystream is fatal. How do we solve from `P1 XOR P2`?

- If we know part of P1 (known plaintext, for example we know the message starts with `GET / HTTP/1.1`), we get P2 for that part directly: `P2 = (P1 XOR P2) XOR P1`. If we know all of P1, we get the whole keystream `K = C1 XOR P1`, and we can decrypt every other ciphertext that shares K.
- If we know nothing, we use crib dragging: guess a common word such as ` the ` and slide it along `P1 XOR P2`. At any position where the XOR result is entirely printable and meaningful, the word appears in one of the two plaintexts, and we read the matching part of the other. Repeat and assemble the pieces, and both messages appear. The more ciphertexts share the keystream, the easier it gets, and statistics help (at each position, the space byte 0x20 leaves a characteristic trace when XORed).

The bitter point is that the whole process never touches the key and never breaks AES or ChaCha. It only needs a programmer who reused a nonce.

### Why people reuse nonces

Nonce reuse is not rare, for very human reasons, such as a fixed nonce for convenience (`nonce = b"\x00" * 12`), a random 8-byte nonce used for billions of messages (the collision probability rises quickly by the birthday paradox), a counter reset after a service restart, or a nonce copied from an old record. With a randomly generated 96-bit nonce, the risk starts after about 2^32 messages. The solution is an incrementing counter that is stored durably, or a nonce-misuse-resistant construction such as AES-GCM-SIV.

## 2. Demo

### Demo 1: nonce reuse makes the keystream cancel

```python
# demo_twotime.py: ChaCha20 with a repeated nonce -> C1 XOR C2 = P1 XOR P2
import os
from Crypto.Cipher import ChaCha20

key = os.urandom(32)
nonce = os.urandom(8)          # REUSED for both messages, this is the bug

def enc(msg: bytes) -> bytes:
    return ChaCha20.new(key=key, nonce=nonce).encrypt(msg)

m1 = b"The quick brown fox jumps over the lazy dog!!"
m2 = b"Pack my box with five dozen liquor jugs today"
c1, c2 = enc(m1), enc(m2)

xor_ct = bytes(a ^ b for a, b in zip(c1, c2))
xor_pt = bytes(a ^ b for a, b in zip(m1, m2))
print("C1 XOR C2 == P1 XOR P2:", xor_ct == xor_pt)  # True, the keystream cancels
```

### Demo 2: knowing one plaintext recovers all the others

```python
# demo_knownpt.py: know m1 -> derive the keystream -> decrypt m2
import os
from Crypto.Cipher import ChaCha20

key = os.urandom(32)
nonce = os.urandom(8)
def enc(m): return ChaCha20.new(key=key, nonce=nonce).encrypt(m)

m1 = b"The quick brown fox jumps over the lazy dog!!"
m2 = b"Pack my box with five dozen liquor jugs today"
c1, c2 = enc(m1), enc(m2)

keystream = bytes(a ^ b for a, b in zip(c1, m1))   # K = C1 XOR P1
rec2 = bytes(a ^ b for a, b in zip(c2, keystream)) # P2 = C2 XOR K
print("recovered m2:", rec2)
assert rec2 == m2
```

### Demo 3: crib dragging when no plaintext is known

```python
# demo_crib.py: no plaintext known, drag the crib ' the ' over P1 XOR P2
import os
from Crypto.Cipher import ChaCha20

key = os.urandom(32)
nonce = os.urandom(8)
def enc(m): return ChaCha20.new(key=key, nonce=nonce).encrypt(m)

m1 = b"the meeting is at the old bridge tonight at nine"
m2 = b"remember to bring the documents for the handover"
c1, c2 = enc(m1), enc(m2)
xor = bytes(a ^ b for a, b in zip(c1, c2))   # = m1 XOR m2, no key left

crib = b" the "
print("dragging crib", crib, "read P1 XOR P2, print positions with meaningful results:")
for pos in range(len(xor) - len(crib) + 1):
    seg = bytes(x ^ c for x, c in zip(xor[pos:pos+len(crib)], crib))
    if all(32 <= b < 127 for b in seg):      # keep printable results only
        print(f"  pos {pos:2d}: crib placed in one message -> the other message reveals {seg!r}")
```

Typical output (the filter only checks for printable bytes, so many positions are noise and you pick out the meaningful words by eye):

```
dragging crib b' the ' read P1 XOR P2, print positions with meaningful results:
  ...
  pos 16: crib placed in one message -> the other message reveals b'3the '
  pos 17: crib placed in one message -> the other message reveals b' the '
  pos 18: crib placed in one message -> the other message reveals b' the+'
  ...
  pos 35: crib placed in one message -> the other message reveals b'night'
  ...
```

At `pos 17`, placing ` the ` in one plaintext makes the other reveal exactly ` the ` (both sentences contain ` the ` near that position), and `pos 35` exposes the fragment `night` of the other sentence. Most other positions are noise that passed the printable filter, and you ignore them. Every time you hit a meaningful fragment you assemble it like a crossword, and you use the fragment you just guessed as a new crib for the next round. In a real task you try many cribs (` the `, `tion`, `GET `, `flag`) and many ciphertext pairs to fill in the text. To repeat, no key is involved anywhere in this process.

The RC4 case is left for you to try. Replace the three demos with `from Crypto.Cipher import ARC4` and `ARC4.new(key).encrypt(...)`. RC4 has no separate nonce, so encrypting two messages with the same key is already a two-time pad, which makes it even easier to hit.

## 3. Lab

- Task: you intercept several ciphertexts (for example 10 lines), all encrypted with the same keystream (a reused nonce, or the same RC4 key). Recover the content of the messages, one of which contains a flag. This is a variant of Cryptopals Set 3 Challenges 19 and 20 (break fixed-nonce CTR).
- Lab files: the Lab section below has `gen.py` (generates 12 AES-CTR ciphertexts with the same nonce into `ciphertexts.txt`), `solve.py` (the space trick and then known plaintext, recovering `flag{n0nce_reuse_is_tw0_time_pad}`) and `transcript.txt`.
- Hints, step by step:
  1. XOR the ciphertexts pairwise and confirm the keystream has cancelled (only P_i XOR P_j remains).
  2. Use the property of the space byte 0x20. XORing a letter with a space gives the same letter with the case swapped. At each column, look for which byte is likely a space to recover the keystream for that column.
  3. Crib drag common words and the flag format (for example `flag{` or `CTF{`).
  4. Assemble gradually. When you recover the keystream for a stretch, apply it to every ciphertext in that stretch.
- Done when: you read the content of the messages and get the flag without using the key.

<div class="lab-box">
<div class="lab-head"><b>LAB 4.5</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/4.5.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/4.5/gen.py" download><i class="fa-solid fa-file-code"></i>gen.py</a>
<a class="lab-file" href="/assets/labs-crypto/4.5/solve.py" download><i class="fa-solid fa-file-code"></i>solve.py</a>
</div>
</div>

## Key takeaways

- Stream cipher: Ci = Pi XOR keystream. Decryption regenerates the keystream and XORs again.
- CTR, RC4, ChaCha20 and Salsa20 are all stream ciphers and all follow the nonce rule.
- A reused nonce (or the same RC4 key) gives C1 XOR C2 = P1 XOR P2, so the keystream cancels and you have a two-time pad.
- With P1 XOR P2 you derive one plaintext from the other if you know one, and you use crib dragging if you know neither.
- RC4 is obsolete and should not be used. ChaCha20-Poly1305 is the modern choice, but the nonce must stay unique.
- Defense: use a nonce that is a durably stored incrementing counter, or use AES-GCM-SIV, which tolerates repeated nonces.

## Common pitfalls

- Assuming ChaCha20 or AES-GCM is safe because it is "modern". Nonce reuse breaks the scheme regardless of the algorithm. With GCM it also leaks the authentication key.
- Using a fixed nonce for convenience (`b"\x00"*12`). A classic mistake where demo code is copied straight into production.
- Generating a short random nonce and encrypting too many messages. By the birthday paradox, a 64-bit nonce starts to collide after about 2^32 messages.
- Confusing the nonce with the key. The nonce is not secret but must be unique. The key is secret and can be reused many times as long as each message gets a different nonce.
- With RC4, forgetting that there is no nonce, so every message under the same RC4 key shares the same keystream, a two-time pad from the second message on.
- Giving up on crib dragging too early. You need to try many cribs and assemble patiently. The more ciphertexts share the keystream, the more reliable the result.

## Further reading

- RFC 8439 (ChaCha20 and Poly1305), the current specification.
- Cryptopals Set 3, Challenges 19 and 20 (break fixed-nonce CTR), the standard two-time pad practice.
- AlFardan et al., "On the Security of RC4 in TLS" (2013), the reason RC4 was retired.
- Nguyen and Shparlinski and other papers on nonce reuse. Also read AES-GCM-SIV (RFC 8452) for the approach that resists nonce misuse.
- CryptoHack, the Symmetric section, the challenges on Stream Ciphers and the two-time pad challenges.
