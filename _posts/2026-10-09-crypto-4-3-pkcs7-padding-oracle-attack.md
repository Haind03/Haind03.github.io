---
title: "Lesson 4.3: PKCS#7 padding and the padding oracle attack"
image:
  path: /assets/img/covers/crypto-4-3-pkcs7-padding-oracle-attack.webp
  alt: "PKCS#7 padding and the padding oracle attack"
date: 2023-05-19 06:42:00 +0700
categories: ["Cryptography", "Crypto · Symmetric Encryption"]
tags: [cryptography, padding-oracle, cbc, aes]
render_with_liquid: false
---

This is the best known and most common attack in the symmetric part of CTFs. If a server tells you whether the padding of a ciphertext is valid or not, you can decrypt the whole ciphertext without knowing the key. This lesson explains what PKCS#7 padding is, why a tiny valid or invalid signal is enough to break the scheme, how the byte-by-byte recovery works, and gives an attack script that runs from start to finish.

![PKCS#7 padding and the padding oracle attack](/assets/img/crypto/crypto-4-3-pkcs7-padding-oracle-attack.svg)
_The attacker sends a forged previous block, the server answers only valid or invalid, and that one bit reveals Ii._

Part 4 (Symmetric Encryption) | Time: about 45 minutes | Difficulty: hard

**Prerequisites:** Lesson 4.1 (AES), Lesson 4.2 (CBC, especially the formula Pi = D(Ci) XOR C(i-1)). A solid grasp of XOR from Lesson 3.1.

**Tools:** Python 3 and PyCryptodome.

## Goals

After this lesson you can state the PKCS#7 rule exactly, which is to add N bytes, each with value N. You understand what a padding oracle is and why one bit of information (valid or invalid) gradually leaks a whole plaintext. You can derive the intermediate value D(Ci) byte by byte by forcing valid padding. You can write and run a script that decrypts one block, then a whole message, through the oracle. You can recognize a padding oracle challenge and know how to defend against it.

## 1. Theory

### PKCS#7 padding

A block cipher such as AES needs the plaintext to be a multiple of 16 bytes. Real messages rarely fit exactly, so we add extra bytes, called padding. PKCS#7 is the most common rule, and it has one sentence, namely that if N bytes are needed, add exactly N bytes, each with the value N.

Examples for a 16-byte block:

- 1 byte short: add `01`.
- 4 bytes short: add `04 04 04 04`.
- Exactly 16 bytes: still add a whole block `10 10 ... 10` (sixteen bytes of value 0x10 = 16). Padding is always added, even when the message fits, so that removing it is unambiguous.

When decrypting, the receiver looks at the last byte, say N, and checks whether the last N bytes all have the value N. If so it removes those N bytes and returns the real plaintext. If not, the padding is invalid and an error is usually raised. That error is what the attack uses.

### What an oracle is, and why valid or invalid is enough

An oracle (a function or service that is willing to answer) in this context is anything that tells you whether a ciphertext decrypts to valid padding. It does not have to return the plaintext. It only has to distinguish two states:

- Valid padding: the server continues processing (returns 200, or reports "bad signature", or anything else that differs from the padding error).
- Invalid padding: the server complains with something like "bad padding", returns 500, or simply answers more slowly.

That is one bit of information. It sounds like nothing, but we will see that it is enough to extract every plaintext byte. The leak can be a different error message, a different HTTP status, a different response time, or even whether something is logged. In real code, `unpad` raising `ValueError` while the later code raises a different error is already enough to tell the cases apart.

### The lever: how CBC decrypts a block

Recall from Lesson 4.2 that CBC decrypts one block like this:

```
Pi = D(Ci) XOR C(i-1)
```

Call D(Ci) the intermediate value, written Ii. It is the output of AES decryption on the block Ci, before the XOR. So:

```
Pi = Ii XOR C(i-1)
```

The key point is that Ii depends only on Ci and the key, so it is fixed. C(i-1) is fully controlled by us, the attacker, because it is just a ciphertext block that we can change freely before sending it to the oracle. If we know Ii, we can compute Pi = Ii XOR C(i-1) using the real C(i-1). So the goal is to extract Ii byte by byte.

### Recovering the intermediate value byte by byte

We attack one pair of blocks, made of a forged block C' that we build and place right before the target block Ci. The oracle decrypts that pair and checks the padding of the last block, which means it checks whether `D(Ci) XOR C'` is valid PKCS#7 padding. Call the decrypted block P' = Ii XOR C'.

Start at the last byte (position 15). We want to force P' to have valid padding with value 0x01, meaning the last byte of P' equals 01. We keep the first 15 bytes of C' at 0 (or anything) and run the last byte of C' through all 256 values. For exactly one value the last byte of P' becomes 0x01 and the oracle reports valid. Then:

```
P'[15] = Ii[15] XOR C'[15] = 0x01
=> Ii[15] = C'[15] XOR 0x01
```

This gives byte 15 of the intermediate value. The real plaintext follows from Pi[15] = Ii[15] XOR C(i-1)[15], where C(i-1) is the real block that precedes it in the original ciphertext.

Move to byte 14. Now we want valid padding with value 0x02, so the last two bytes of P' must be `02 02`. We can force byte 15 because we know Ii[15], so we set C'[15] = Ii[15] XOR 0x02. For byte 14 we search 256 values until P'[14] = 0x02 and the oracle reports valid, which gives Ii[14] = C'[14] XOR 0x02. We continue backwards. To get the byte at position pos, set the target padding N = 16 - pos, force all bytes after pos to N (possible because we know their Ii), then search byte pos.

There is a small trap at the last byte (N = 1). It can happen that byte 15 of P' is not 0x01 but byte 14 happens to make the block a longer valid padding (for example P' ends with `02 02`). To be sure, when we find a candidate for N = 1 we flip one bit in byte 14 of C' and ask the oracle again. If it is still valid, the last byte really is 0x01. If not, we hit a coincidence and discard the candidate. The script below handles exactly this.

### Why missing integrity keeps this attack alive

A padding oracle works only because plain CBC does not authenticate the ciphertext. We send the oracle forged ciphertexts (a custom C') and it still decrypts them and checks the padding. With a MAC (for example encrypt-then-MAC), a forged ciphertext fails the MAC check before it ever reaches the padding step, and the oracle stays silent. Once again, missing integrity is the root cause.

## 2. Demo

The script builds both the oracle and the attacker in one file so you can run it right away. The oracle part plays the server (it knows the key). The attack part plays you (it may only call `padding_ok`). In a real challenge, `padding_ok` becomes an HTTP request and the attack logic stays the same.

```python
# padding_oracle.py: build the oracle and the attack, decrypt without the key
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

KEY = os.urandom(16)   # secret, the attacker does NOT know it
BS = 16

# --- server side ---
def encrypt(msg: bytes) -> bytes:
    iv = os.urandom(BS)
    c = AES.new(KEY, AES.MODE_CBC, iv)
    return iv + c.encrypt(pad(msg, BS))

def padding_ok(ct: bytes) -> bool:
    # oracle: only answers whether the padding is valid
    iv, body = ct[:BS], ct[BS:]
    c = AES.new(KEY, AES.MODE_CBC, iv)
    try:
        unpad(c.decrypt(body), BS)
        return True
    except ValueError:
        return False

# --- attacker side: only uses padding_ok, never KEY ---
def decrypt_block(prev: bytes, cur: bytes) -> bytes:
    inter = bytearray(BS)       # intermediate value Ii = D(cur)
    recovered = bytearray(BS)   # real plaintext of this block
    for pad_val in range(1, BS + 1):
        pos = BS - pad_val
        forged = bytearray(BS)
        # force the known bytes to the target padding value
        for i in range(pos + 1, BS):
            forged[i] = inter[i] ^ pad_val
        for guess in range(256):
            forged[pos] = guess
            if padding_ok(bytes(forged) + cur):
                if pad_val == 1:
                    # rule out a coincidence: flip 1 bit of the previous byte, still valid means sure
                    forged[pos - 1] ^= 1
                    if not padding_ok(bytes(forged) + cur):
                        continue
                inter[pos] = guess ^ pad_val
                recovered[pos] = inter[pos] ^ prev[pos]
                break
        else:
            raise RuntimeError(f"could not find the byte at position {pos}")
    return bytes(recovered)

def attack(ct: bytes) -> bytes:
    blocks = [ct[i:i+BS] for i in range(0, len(ct), BS)]
    out = b""
    for i in range(1, len(blocks)):           # block 0 is the IV
        out += decrypt_block(blocks[i-1], blocks[i])
    return unpad(out, BS)

if __name__ == "__main__":
    secret = b"flag{padding_oracle_is_dangerous_ok}"
    ct = encrypt(secret)
    print("ciphertext (hex):", ct.hex())
    recovered = attack(ct)
    print("recovered        :", recovered)
    assert recovered == secret
    print("OK, decrypted successfully without knowing the key")
```

Run it and the output is:

```
ciphertext (hex): 3a1f...<random on every run>...
recovered        : b'flag{padding_oracle_is_dangerous_ok}'
OK, decrypted successfully without knowing the key
```

Notice that the `attack` function never touches `KEY`. It calls `padding_ok` a few thousand times in total (at most 256 times per byte, 16 bytes per block). The cost is only the patience to ask the same valid or invalid question many times. In a real challenge you replace the body of `padding_ok` with a request to the server and read the response, and everything else stays the same.

To watch how the intermediate value is recovered, add a line that prints `inter` after each round in `decrypt_block`. You will see it fill in from the last byte to the first.

## 3. Lab

- Task: a web service accepts a cookie of the form `iv || ciphertext` (hex or base64), decrypts it with AES-CBC and returns different errors for bad padding and for bad content. Recover the plaintext of the cookie (it contains a flag). This is the network version of Cryptopals Set 3 Challenge 17.
- Lab files: the Lab section below has a self-contained `solve.py` (oracle and attack, recovering `flag{padding_oracle_is_dangerous_ok}`) and `transcript.txt`. For the network version, write a small HTTP oracle with Flask that returns 200 when the padding is valid and 403 when not, call it from the client with `requests`, and keep `decrypt_block` as it is.
- Hints, step by step:
  1. Find the signal that separates valid padding from invalid, such as HTTP status, response body, or timing. Write `padding_ok(ct)` returning `True` or `False` from it.
  2. Recover the intermediate value of the last block first, by forcing the last byte to 0x01. Check it against a plaintext you know in your own test setup.
  3. Generalize to every position and every block. Remember the coincidence check at the last byte (N = 1), as in the demo.
  4. The IV is block 0. To decrypt the first block you need the IV as prev.
- Done when: you print the full plaintext of the cookie, including the flag, without knowing the key.

<div class="lab-box">
<div class="lab-head"><b>LAB 4.3</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/4.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/4.3/solve.py" download><i class="fa-solid fa-file-code"></i>solve.py</a>
</div>
</div>

## Key takeaways

- PKCS#7: add N bytes, each with value N. A message that fits exactly still gets a whole 0x10 block.
- The oracle only has to leak one bit, padding valid or invalid. The signal can be an error code, the body, or timing.
- CBC: Pi = D(Ci) XOR C(i-1). We control C(i-1) and extract D(Ci) byte by byte by forcing padding.
- To get the byte at position pos, set the target padding N = 16 - pos, force the later bytes to N, and search byte pos over 256 values.
- Handle the coincidence at N = 1 by flipping one bit of the previous byte and asking again.
- Defense: use AEAD (GCM), or encrypt-then-MAC, or return identical and constant-time errors for every kind of failure.

## Common pitfalls

- Forgetting that the IV is the first block. To decrypt the first plaintext block, prev is the IV. If the challenge does not send the IV, the first block cannot be recovered, only the second block onward.
- Ignoring the coincidence at the last byte. Without the recheck you occasionally pick a wrong byte and the whole block is off. Always do the bit-flip confirmation for N = 1.
- Mixing up the XOR direction between the intermediate value and the prev block. Remember that Ii = guess XOR pad_val (in the forged space), while the real plaintext = Ii XOR the real prev. Confusing the forged prev with the real prev gives garbage.
- Expecting only "01" padding and forgetting that the server may accept longer padding. Forcing from the last byte backwards already handles this, but when debugging you have to separate what is valid because you forced it from what is valid by chance.
- Real oracles often do not return a clear error. Sometimes the signal is timing (bad padding is handled faster because it stops early). You have to measure the time and pick a threshold.
- The attack is slow because of network calls. Each byte takes up to 256 requests, so a 16-byte block takes at most 4096 requests. Cache results, parallelize over byte positions, and stop the loop as soon as you find the byte.

## Further reading

- Serge Vaudenay, "Security Flaws Induced by CBC Padding", the original 2002 paper that introduced the padding oracle.
- Cryptopals Set 3, Challenge 17 (The CBC padding oracle), the standard practice problem.
- POODLE and Lucky Thirteen, two real TLS vulnerabilities that are padding oracle variants. Read them to see that this is not limited to CTFs.
- CryptoHack, the Symmetric section, the challenges on CBC and padding.
