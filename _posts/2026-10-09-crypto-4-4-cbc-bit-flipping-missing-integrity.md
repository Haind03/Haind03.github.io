---
title: "Lesson 4.4: CBC bit flipping and missing integrity"
image:
  path: /assets/img/covers/crypto-4-4-cbc-bit-flipping-missing-integrity.webp
  alt: "CBC bit flipping and missing integrity"
date: 2026-10-09 12:20:00 +0700
categories: ["Cryptography", "Crypto · Symmetric Encryption"]
tags: [cryptography, cbc, bit-flipping, integrity]
render_with_liquid: false
---

The padding oracle in the previous lesson needs the server to leak a signal. Bit flipping needs even less. As long as the ciphertext is not authenticated, you can edit the ciphertext directly and bend the plaintext the receiver decrypts to your wishes, without knowing the key. This is the cleanest demonstration that encryption is not authentication, and why a system that provides only confidentiality and no integrity is open to an attacker.

![CBC bit flipping and missing integrity](/assets/img/crypto/crypto-4-4-cbc-bit-flipping-missing-integrity.svg)
_Editing c2 changes p3 in a controlled way and turns p2 into garbage._

Part 4 (Symmetric Encryption) | Time: about 35 minutes | Difficulty: medium

**Prerequisites:** Lesson 4.2 (CBC). You must understand Pi = D(Ci) XOR C(i-1). Lesson 3.1 (XOR).

**Tools:** Python 3 and PyCryptodome.

## Goals

After this lesson you can explain why flipping a bit in the previous ciphertext block flips exactly the matching bit in the next plaintext block. You know the price: the block that contains the edited bytes turns into garbage. You can forge a `;admin=true;` cookie with CBC bit flipping even when the input is filtered. You can flip bits in the IV to change the first plaintext block without damaging any block. You understand why authenticated encryption stops this attack.

## 1. Theory

### Mechanism: the XOR carries into the next block

Recall the CBC decryption formula for block i:

```
Pi = D(Ci) XOR C(i-1)
```

D(Ci) is fixed because it depends on the key and Ci. C(i-1) is in our hands, since it is only a ciphertext block. Suppose we XOR a value delta into byte j of block C(i-1):

```
C(i-1)[j]  ->  C(i-1)[j] XOR delta
```

When decrypting, byte j of block Pi becomes:

```
Pi[j]_new = D(Ci)[j] XOR (C(i-1)[j] XOR delta)
          = (D(Ci)[j] XOR C(i-1)[j]) XOR delta
          = Pi[j]_old XOR delta
```

So the plaintext byte at that position is XORed with exactly the delta we chose. If we know the old plaintext value at that byte (call it `old`) and want it to become `want`, we set:

```
delta = old XOR want
```

That is the whole attack. Flipping a bit in ciphertext block (i-1) flips exactly the corresponding bit in plaintext block i. The relation is one to one, so we can target each byte precisely.

### The price: block i-1 is destroyed

Nothing is free. When we modify C(i-1), the block P(i-1) (decrypted from C(i-1)) is destroyed, because:

```
P(i-1) = D(C(i-1)) XOR C(i-2)
```

When C(i-1) changes, D(C(i-1)) changes completely (recall the avalanche effect from Lesson 4.1, where changing one input byte of AES scrambles the whole output). So block P(i-1) turns into 16 bytes of garbage that we cannot control.

The practical strategy is to sacrifice a block we do not need in order to edit the next block that we do need. In the classic cookie task, we insert a filler block of harmless characters (it will be destroyed, and that is fine) right before the block that holds the `;admin=true` payload. The filler block is ruined, and the payload block shows what we wanted.

### Flipping bits in the IV

The first plaintext block uses the IV in the role of "C(i-1)":

```
P1 = D(C1) XOR IV
```

If we control the IV (it usually travels with the ciphertext), we can modify P1 by flipping the IV without damaging any block, because the IV is not the decryption output of any block. This is the cleanest case, since to change the first byte of the plaintext, flip exactly that byte in the IV. Many systems send the IV in the open right before the ciphertext, which makes this easy.

### Why missing integrity is fatal

Bit flipping works only because the receiver trusts the ciphertext without checking it. Encryption ensures that outsiders cannot read the content, but says nothing about whether the content was modified. These are two different goals, confidentiality and integrity. Plain CBC, plain CTR, OFB and CFB all provide only the first.

With authenticated encryption (AES-GCM, ChaCha20-Poly1305) or encrypt-then-MAC (encrypt first, then sign the ciphertext with HMAC), any edit to the ciphertext makes the tag or MAC wrong, and the receiver rejects it before decrypting to a bent plaintext. You can still flip bits, but the server no longer processes the result. Encryption without authentication gives no protection for integrity.

## 2. Demo

The scenario is Cryptopals Set 2 Challenge 16. The server takes your `userdata`, places it between two fixed strings, filters out the characters `;` and `=` (replacing them with an escape), then encrypts with CBC. The function `is_admin` decrypts and checks for the string `;admin=true`. Because of the filter, you cannot send `;admin=true` directly. But you can flip bits.

The idea is to send two blocks, one filler block of `A` characters (which will be destroyed) and one block containing `AAAAA?admin?true`, where `?` is a placeholder that is not filtered. Then flip bytes in the ciphertext of the filler block to turn `?` into `;` and `=`.

```python
# cbc_bitflip.py: forge ;admin=true even though the characters are filtered
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

KEY = os.urandom(16)
BS = 16
PRE  = b"comment1=cooking%20MCs;userdata="   # exactly 32 bytes = 2 blocks
POST = b";comment2=%20like%20a%20pound%20of%20bacon"

def submit(userdata: bytes) -> bytes:
    userdata = userdata.replace(b";", b"%3B").replace(b"=", b"%3D")  # filter
    data = PRE + userdata + POST
    iv = os.urandom(BS)
    c = AES.new(KEY, AES.MODE_CBC, iv)
    return iv + c.encrypt(pad(data, BS))

def is_admin(ct: bytes) -> bool:
    iv, body = ct[:BS], ct[BS:]
    c = AES.new(KEY, AES.MODE_CBC, iv)
    pt = unpad(c.decrypt(body), BS)
    return b";admin=true" in pt

if __name__ == "__main__":
    # PRE = 2 whole blocks (p0, p1). userdata starts at block p2.
    filler = b"A" * 16                 # p2: filler block, will be destroyed
    target = b"AAAAA?admin?true"       # p3: exactly 16 bytes, '?' is a placeholder
    ct = bytearray(submit(filler + target))

    # ct layout: iv(16) + c0(16) + c1(16) + c2(16) + c3(16)...
    # p3 = D(c3) XOR c2  => edit c2 to flip p3. c2 is at offset iv+2*16 = 48
    off = 48
    ct[off + 5]  ^= ord('?') ^ ord(';')   # position 5 in the block -> ';'
    ct[off + 11] ^= ord('?') ^ ord('=')   # position 11 in the block -> '='

    print("is_admin after bit flip:", is_admin(bytes(ct)))
    assert is_admin(bytes(ct))
    print("OK, forged ;admin=true without knowing the key")
```

It prints `is_admin after bit flip: True`. We never sent a `;` or `=` character through the filter. They were built by flipping exactly two bytes in the filler block. The filler block `p2` is now 16 bytes of garbage, but `is_admin` only looks for the string `;admin=true`, so it does not care about the garbage block.

To locate the target, note that `PRE` is exactly 32 bytes, so it fills the first two blocks, and our `userdata` starts exactly on the boundary of the third block. We put `?` at positions 5 and 11 in the `target` block, then flip exactly those two positions in the ciphertext block right before it (`c2`). The delta is `ord('?') XOR ord(';')` and `ord('?') XOR ord('=')`, which is the `old XOR want` formula.

For the IV variant, if the payload must sit in the first block, flip the IV (the first 16 bytes of `ct`) instead of `c2`, and then no block is destroyed.

## 3. Lab

- Task: an application stores a session in CBC form: `role=user;id=1337`. The application lets you set `id` but filters `;` and `=` in the input. Goal: change the session to `role=admin` (or append `;admin=true`) to gain privileges without knowing the key. It can be the IV variant if the `role` field is in the first block.
- Lab files: the Lab section below has a self-contained `solve.py` (forges `;admin=true` through bit flipping) and `transcript.txt`. For more practice, change the layout of `submit` and `is_admin` so the field you need to edit lands in a different block, to practice locating it.
- Hints, step by step:
  1. Find the length of the fixed prefix to know which byte your userdata starts at and which block index it falls in. Tip: send longer and longer input and watch which ciphertext block starts to change.
  2. Align things so the payload sits fully inside one block, with a block right before it that you are willing to sacrifice.
  3. Compute delta = old XOR want for each byte to edit and flip it in the previous ciphertext block.
  4. If the field to edit is in the first block, flip the IV. No filler block is needed.
- Done when: the server confirms you are admin, or the decrypted plaintext contains the privilege string you want.

<div class="lab-box">
<div class="lab-head"><b>LAB 4.4</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/4.4.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/4.4/solve.py" download><i class="fa-solid fa-file-code"></i>solve.py</a>
</div>
</div>

## Key takeaways

- Flipping byte j of C(i-1) XORs Pi[j] with the same delta: Pi[j]_new = Pi[j]_old XOR delta.
- To change Pi[j] from `old` to `want`, set delta = old XOR want.
- The price is that the matching block P(i-1) is destroyed. Sacrifice a filler block you do not need.
- To edit the first plaintext block, flip the IV. No block is destroyed.
- The attack needs the old plaintext at the byte you want to change, known or guessed.
- Defense: authenticated encryption (GCM) or encrypt-then-MAC. Any edit to the ciphertext is detected.

## Common pitfalls

- Flipping the wrong block. You must edit C(i-1) to affect Pi, which means the ciphertext block BEFORE the target plaintext block. Flipping the target block itself only turns it into garbage.
- Forgetting the IV when computing offsets. If the ciphertext you hold starts with the IV, the offset of ciphertext block k is 16 + k*16, not k*16.
- Misaligning block boundaries. If the prefix is not a multiple of 16, your payload spans two blocks and the flipping becomes a mess. Always add padding bytes so the payload fits in one block.
- Not knowing the old plaintext at the byte to edit. If you choose the plaintext yourself (such as the `?` placeholder) you know it for sure. If you edit a fixed server plaintext without knowing it, you must guess, or combine another attack that reveals the plaintext first.
- Thinking bit flipping reads the plaintext. It does not. It only edits the plaintext blindly, so you must know or guess the old content in advance. To read, use a padding oracle.
- Forgetting padding. If you accidentally edit the last block, the padding may become invalid and the server raises an error. Aim at a middle block and leave the last block alone.

## Further reading

- Cryptopals Set 2, Challenge 16 (CBC bitflipping attacks) and Set 4, Challenge 26 (the CTR variant).
- Moxie Marlinspike, "The Cryptographic Doom Principle", which argues that touching the plaintext before verifying the MAC leads to trouble.
- CryptoHack, the Symmetric section, the challenges on CBC and flipping.
- Material comparing encrypt-then-MAC with MAC-then-encrypt, to learn the correct order when combining a MAC.
