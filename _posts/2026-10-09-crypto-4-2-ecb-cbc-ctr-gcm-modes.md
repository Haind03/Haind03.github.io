---
title: "Lesson 4.2: ECB, CBC, CTR and GCM modes of operation"
image:
  path: /assets/img/covers/crypto-4-2-ecb-cbc-ctr-gcm-modes.webp
  alt: "ECB, CBC, CTR and GCM modes of operation"
date: 2026-10-09 12:10:00 +0700
categories: ["Cryptography", "Crypto · Symmetric Encryption"]
tags: [cryptography, aes, block-cipher-modes, ecb]
render_with_liquid: false
---

AES only transforms 16 bytes at a time. To encrypt data of arbitrary length we have to choose a mode of operation that chains the blocks together. This lesson covers the four modes you meet most often in CTFs and in real code. It shows why ECB leaks patterns so badly that you can see a picture through the ciphertext, how CBC and CTR chain blocks, what GCM adds that the other three lack, how an IV differs from a nonce, and when to use which mode.

![ECB, CBC, CTR and GCM modes of operation](/assets/img/crypto/crypto-4-2-ecb-cbc-ctr-gcm-modes.svg)
_The four modes side by side, with the property that matters most for each._

Part 4 (Symmetric Encryption) | Time: about 35 minutes | Difficulty: medium

**Prerequisites:** Lesson 4.1 (block ciphers and AES). Lesson 3.1 (XOR), which you need to follow CTR and CBC.

**Tools:** Python 3 and PyCryptodome. The ECB image demo needs no image library. We write a raw PPM file that any viewer can open (GIMP, IrfanView, or ImageMagick `convert`).

## Goals

After this lesson you can explain why ECB leaks patterns and build a small "ECB penguin" yourself. You understand how CBC and CTR chain blocks, and that CTR turns a block cipher into a stream cipher. You can tell an IV (initialization vector) from a nonce (number used once) and know what each one requires. You know that GCM gives both confidentiality and authentication (authenticated encryption), while plain ECB, CBC and CTR do not. You can pick the right mode for a situation and spot a wrong mode when reading someone else's code.

## 1. Theory

Notation: the plaintext is cut into blocks P1, P2, P3 and so on, each 16 bytes. The ciphertext is C1, C2, C3. E(.) encrypts one AES block with the key and D(.) decrypts one block.

### ECB: every block is encrypted on its own

ECB (Electronic Codebook) is the simplest mode: Ci = E(Pi). Each block is encrypted independently of every other block.

The consequence is serious. Two identical plaintext blocks produce two identical ciphertext blocks, because E is a deterministic function. The same input under the same key always gives the same output. So ECB leaks where the plaintext repeats, directly in the ciphertext, and no key is needed to see it.

The classic example is the ECB penguin. Take a picture of a penguin with large flat-colored areas, encrypt it with AES-ECB and display the ciphertext as an image. The flat areas (many identical blocks) become identical patches of noise, and the outline of the penguin stays clearly visible. Encryption that still shows the picture is not protecting anything. We rebuild this in section 2 with a simple square image.

Outside CTFs, ECB also causes the byte-at-a-time ECB decryption bug. If an oracle (a function that answers queries, here an encryption function) concatenates your input with a secret and encrypts the result in ECB, you can recover the secret one byte at a time. That is the lab in Lesson 4.6. In short, ECB is almost always wrong, unless you encrypt exactly one random block that never repeats.

### CBC: chaining with XOR

CBC (Cipher Block Chaining) fixes the repetition problem of ECB by mixing each plaintext block with the previous ciphertext block before encrypting:

```
C1 = E(P1 XOR IV)
C2 = E(P2 XOR C1)
C3 = E(P3 XOR C2)
...
Ci = E(Pi XOR C(i-1))
```

The IV (initialization vector) is a 16-byte block that plays the role of "C0" for the first block. Because of the XOR with the previous block, two identical plaintext blocks now produce different ciphertext blocks (the C(i-1) values differ), and the pattern disappears.

Decryption runs the other way, with Pi = D(Ci) XOR C(i-1). Note one point that matters a lot for the next lessons. To decrypt block i we only need D(Ci) and C(i-1). An attacker who controls C(i-1) (it sits right inside the ciphertext) controls every byte of plaintext block i after the XOR. This is the root of both CBC bit flipping (Lesson 4.4) and the padding oracle (Lesson 4.3).

The IV in CBC must be unpredictable for every encryption. A fixed IV, or one that can be guessed, is a bug. The IV does not need to be secret, and it is usually sent at the start of the ciphertext. CBC also needs the plaintext to be a multiple of the block size, so it needs padding, which brings the risk of a padding oracle.

### CTR: turning a block cipher into a stream cipher

CTR (Counter) does not encrypt the plaintext directly. It encrypts a sequence of counters to produce a keystream, then XORs the keystream into the plaintext, like a one-time pad:

```
keystream_block_i = E(nonce || counter_i)
Ci = Pi XOR keystream_block_i
```

Each counter block is the nonce joined with an increasing number (0, 1, 2...). Since it is only an XOR, CTR needs no padding, the ciphertext is exactly as long as the plaintext, and single odd bytes can be encrypted. Decryption is identical to encryption, since you regenerate the keystream and XOR. CTR uses AES as a keystream generator, so it is a stream cipher.

The benefits are no padding (so no padding oracle), good parallelism and random access. The danger is severe because the nonce and counter must never repeat under the same key. If you encrypt two different messages with the same nonce, the keystreams are identical. XORing the two ciphertexts cancels the keystream and reveals the XOR of the two plaintexts. This is the two-time pad, the subject of Lesson 4.5. Here the nonce is a number used once, and reusing it breaks the scheme.

### IV versus nonce

The two words are often mixed up. The difference is in the requirement:

- The CBC IV must be random and unpredictable. Repeating an IV in CBC reveals when two messages share a common block prefix, and a predictable IV opens the door to chosen-plaintext attacks such as BEAST.
- The nonce of CTR (and of stream ciphers and GCM) only has to be unique under one key. It does not have to be random, and an incrementing counter is a valid nonce as long as it is never reused. Reuse is fatal immediately, which is worse than reusing a CBC IV.

In short, an IV must not be predictable and a nonce must not be reused. Neither has to be secret.

### GCM: authenticated encryption

Plain ECB, CBC and CTR only provide confidentiality of the content. They give no integrity and no authentication of origin. If an attacker edits the ciphertext, the receiver decrypts garbage (or a deliberately altered plaintext, see CBC bit flipping) and has no idea it was modified. Missing integrity is the root of most attacks in this part.

GCM (Galois/Counter Mode) combines CTR encryption with an authentication function based on multiplication in the field GF(2^128). It produces an authentication tag, usually 16 bytes. On decryption the receiver recomputes the tag and compares. One wrong bit in the ciphertext, in the AAD (additional authenticated data, which is authenticated but not encrypted, for example a header) or in the tag makes verification fail, and the receiver refuses to return any plaintext. This is authenticated encryption (AEAD), the standard you should use today.

GCM uses CTR inside, so the rule against nonce reuse still applies, and it is worse here. Repeating a nonce in GCM not only leaks plaintext but also leaks the authentication key, which allows forging tags for other messages (the "forbidden attack"). GCM is safe only when the nonce never repeats.

### Which mode to use

A practical summary:

- ECB is almost never acceptable. The only case is encrypting a single random block, for example wrapping a key. ECB in an application that handles user data should be treated as a bug.
- CBC is for legacy compatibility only, and it must be combined with a MAC such as HMAC in an encrypt-then-MAC construction to get integrity. Plain CBC without a MAC invites padding oracles and bit flipping.
- CTR is fine for confidentiality, but it still needs a separate MAC for integrity and strict nonce management.
- GCM (or ChaCha20-Poly1305) should be the default. It includes integrity. You only need discipline with nonces.

Without an authentication tag the attacker can modify the ciphertext, and almost every lesson in this part exploits exactly that.

## 2. Demo

### Demo 1: ECB leaks a pattern in an image

This script creates a PPM image (a raw, uncompressed format) with a white rectangle on a black background, encrypts it in ECB and writes the result to a file. Open both files in an image viewer and you can still see the rectangle in the encrypted image, because the flat areas produce identical ciphertext blocks.

```python
# demo_ecb_image.py: create a PPM image, encrypt in ECB, the pattern stays visible
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

W = H = 256
key = os.urandom(16)
header = f"P6\n{W} {H}\n255\n".encode()   # PPM header, RGB color

pixels = bytearray()
for y in range(H):
    for x in range(W):
        v = 255 if (64 <= x < 192 and 80 <= y < 176) else 0  # white rectangle
        pixels += bytes([v, v, v])
body = bytes(pixels)

ct = AES.new(key, AES.MODE_ECB).encrypt(pad(body, 16))[:len(body)]  # trim to match the pixels

open("orig.ppm", "wb").write(header + body)
open("ecb.ppm",  "wb").write(header + ct)

blocks  = [body[i:i+16] for i in range(0, len(body), 16)]
cblocks = [ct[i:i+16]   for i in range(0, len(ct),   16)]
print("plaintext: unique blocks", len(set(blocks)),  "/", len(blocks))
print("ECB ct   : unique blocks", len(set(cblocks)), "/", len(cblocks))
```

Output:

```
plaintext: unique blocks 2 / 12288
ECB ct   : unique blocks 2 / 12288
```

Both the original image and the encrypted image contain exactly 2 distinct kinds of block (an all-black block and an all-white block), because the image has only two flat regions. ECB maps those two kinds of block to exactly two kinds of ciphertext block, so the structure of the rectangle survives. Open `ecb.ppm` and you will see the square standing out against noise. This is a minimal version of the ECB penguin.

### Demo 2: CBC removes the pattern, compared with ECB

```python
# demo_modes.py: same repeated plaintext, ECB leaks and CBC does not
import os
from Crypto.Cipher import AES

key = os.urandom(16)
pt = b"YELLOW SUBMARINE" * 4   # 4 identical blocks

ct_ecb = AES.new(key, AES.MODE_ECB).encrypt(pt)
iv = os.urandom(16)
ct_cbc = AES.new(key, AES.MODE_CBC, iv).encrypt(pt)

def uniq(ct):
    b = [ct[i:i+16] for i in range(0, len(ct), 16)]
    return len(set(b)), len(b)

print("ECB:", uniq(ct_ecb), "-> every block is identical, leaks at once")
print("CBC:", uniq(ct_cbc), "-> all four blocks differ")
```

The output is `ECB: (1, 4)` against `CBC: (4, 4)`. For the same repeated plaintext, ECB gives 4 identical ciphertext blocks and CBC gives 4 different ones thanks to the chaining.

### Demo 3: GCM detects modification, plain CTR does not

```python
# demo_gcm_integrity.py: GCM rejects a modified ciphertext
import os
from Crypto.Cipher import AES

key = os.urandom(16)
msg = b"account balance: 1000 dong"
pos = msg.index(b"1")                     # position of the first digit of the balance

# plain CTR: a modified ciphertext still decrypts (to a changed plaintext) with no error
c = AES.new(key, AES.MODE_CTR, nonce=os.urandom(8))
nonce = c.nonce
ct = c.encrypt(msg)
tampered = bytearray(ct)
tampered[pos] ^= ord('1') ^ ord('9')      # turn balance 1000 into 9000
out = AES.new(key, AES.MODE_CTR, nonce=nonce).decrypt(bytes(tampered))
print("CTR: decrypting the modified ciphertext gives:", out, "(no error at all)")

# GCM: modify the ciphertext -> verification fails -> rejected
g = AES.new(key, AES.MODE_GCM)
ngcm = g.nonce
ctg, tag = g.encrypt_and_digest(msg)
bad = bytearray(ctg); bad[pos] ^= ord('1') ^ ord('9')
try:
    AES.new(key, AES.MODE_GCM, nonce=ngcm).decrypt_and_verify(bytes(bad), tag)
    print("GCM: tampering NOT detected (wrong)")
except ValueError:
    print("GCM: tampering detected, decryption refused (correct)")
```

Plain CTR decrypts to `b'account balance: 9000 dong'`. The attacker flipped exactly the byte holding the digit `1` to change the balance from 1000 to 9000, with no warning at all. GCM raises `ValueError` immediately because the tag does not match. That is the difference between having integrity and not having it.

## 3. Lab

- Task: you get an encryption endpoint (simulated by a function) that takes plaintext from you and returns ciphertext. Work out whether it uses ECB or CBC, only by choosing plaintext and inspecting the ciphertext (chosen plaintext). This is a reduced version of Cryptopals Set 2 Challenge 11.
- Files: see the Lab section below if present. If you build it yourself, write an encryption function that picks ECB or CBC at random on every call, adds a few random bytes at the start and end, and then guess the mode.
- Hints, step by step:
  1. Send a very long plaintext of identical bytes (at least 3 blocks, for example 48 bytes or more), so that two identical input blocks are sure to land on block boundaries.
  2. Cut the ciphertext into 16-byte blocks. If two adjacent ciphertext blocks are equal, it is ECB.
  3. If there are no equal blocks despite the repeated input, it is CBC (or another chaining mode). Repeat several times to rule out luck.
- Done when: you guess the mode correctly on 20 calls in a row.

## Key takeaways

- ECB: Ci = E(Pi), independent blocks, leaks patterns, a picture stays visible. Avoid it.
- CBC: Ci = E(Pi XOR C(i-1)), the IV must be random and unpredictable, it needs padding, and it is vulnerable to padding oracle and bit flipping without a MAC.
- CTR: Ci = Pi XOR E(nonce||counter), a stream cipher with no padding. Never repeat a nonce.
- An IV must not be guessable and a nonce must not be reused. Neither needs to be secret.
- GCM and ChaCha20-Poly1305 give authenticated encryption (AEAD) with integrity and are the default choice. The nonce still must not repeat.
- Without an authentication tag the ciphertext can be modified, which is the root of most symmetric attacks.

## Common pitfalls

- Using CBC or CTR and assuming it is safe because the data is "encrypted". Without a MAC there is no integrity, and the attacker can edit the ciphertext freely.
- A fixed IV in CBC. This is very common in careless code (IV = 16 zero bytes). It leaks equal prefixes and enables chosen-plaintext attacks.
- Repeating a nonce in CTR or GCM. This is the most serious mistake in this part. With GCM it also leaks the authentication key.
- Mixing modes and ciphers carelessly in a library, for example forgetting to set a nonce, letting the library generate one and then not saving it, so the data cannot be decrypted. Always store and send the IV or nonce with the ciphertext.
- Assuming GCM ciphertext is unreadable until it is verified. PyCryptodome has `decrypt` (no verification) and `decrypt_and_verify`. Calling plain `decrypt` throws away the integrity check. Always use `decrypt_and_verify`.
- Cutting or joining the IV or nonce at the wrong position. A common convention is to place the nonce or IV at the start of the ciphertext, but that is not a rule. Read the encrypting code to learn the layout.

## Further reading

- NIST SP 800-38A (ECB, CBC, CTR) and SP 800-38D (GCM), the standards for these modes.
- The original blog post on the ECB penguin (the Tux image encrypted in ECB), for the classic example.
- Cryptopals Set 2, Challenge 11 (ECB/CBC detection oracle) and Challenge 8 (detect AES in ECB).
- CryptoHack, the Symmetric section, the challenges on Modes of Operation and AES-GCM.
- Matthew Green, the blog post "How to choose an authenticated encryption mode", for how to choose a mode in practice.
