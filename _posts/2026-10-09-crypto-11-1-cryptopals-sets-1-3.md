---
title: "Lesson 11.1: Cryptopals Sets 1 to 3"
image:
  path: /assets/img/covers/crypto-11-1-cryptopals-sets-1-3.webp
  alt: "Cryptopals Sets 1 to 3"
date: 2026-10-09 19:05:00 +0700
categories: ["Cryptography", "Crypto · Real-World Practice"]
tags: [cryptography, cryptopals, padding-oracle, xor]
render_with_liquid: false
---

Cryptopals is the best-known set of crypto exercises in the security community. It has 66 challenges in 8 sets, and it teaches you to break crypto instead of just using it. This lesson introduces the approach, goes through sets 1 to 3, and solves three backbone challenges with code that really runs: single-byte XOR, ECB detection, and a padding oracle on CBC. Once you have done these three, you have the rhythm of the whole collection.

![CBC padding oracle, one byte at a time](/assets/img/crypto/crypto-11-1-cryptopals-sets-1-3.svg)
_The padding oracle loop: forge the previous block, ask the oracle, and recover the intermediate value D(C_i) one byte at a time._

Part: 11 (Real-World Practice) | Time: about 90 minutes | Difficulty: medium to hard

**Prerequisites:** Lesson 3.1 (XOR, frequency scoring), Lesson 4.2 (ECB and CBC modes), Lesson 4.3 (PKCS#7 padding and the padding oracle). This lesson puts that knowledge together as a puzzle-solving skill.

**Tools:** Python 3 and PyCryptodome (for the AES parts). The XOR challenges need only the standard library.

## Goals

By the end of this lesson you can explain what Cryptopals is and how sets 1 to 3 are laid out, solve single-byte XOR with English frequency scoring, detect ECB from repeated blocks alone, and run a padding oracle attack that recovers a full plaintext without the key.

## Theory

### What Cryptopals is and why to do it

Cryptopals (cryptopals.com, written by Thomas Ptacek and colleagues) is a set of hands-on challenges. Each one asks you to code an attack yourself. The idea is that you only really understand a vulnerability once you have written the code that exploits it. There is no official answer key and no automatic grading, only you and the interpreter.

The eight sets go from basic to very hard. The first three are the foundation:

- Set 1 (Basics): hex and base64 encoding, single-byte XOR, repeating-key XOR, ECB detection. This is the warm-up, used to get familiar with the tools and with scoring plaintext.
- Set 2 (Block crypto): implementing PKCS#7, ECB cut-and-paste, byte-at-a-time ECB decryption, CBC bit flipping. It shows where the block cipher modes break.
- Set 3 (Block & stream crypto): the padding oracle (challenge 17, the most famous), breaking CTR with a fixed nonce, and recovering the MT19937 state. This is where the attacks start to get serious.

### Strategy

A few rules from experience:

1. Write all the basic helper functions once, and write them well: `xor_bytes`, `score_english`, splitting into blocks, PKCS#7 pad and unpad. Later sets reuse them constantly.
2. Always work on `bytes`, not `str`. Mixing the two is the number one source of bugs. Only call `.decode()` when printing the final result.
3. Scoring plaintext is a skill you use throughout. A good English frequency scorer solves most of set 1.
4. Leave behind one reusable function per challenge instead of writing code once and throwing it away. The collection is designed so that you build on your earlier work.

### Three backbone challenges

The three challenges solved in the demo section stand for three ways of thinking:

- Single-byte XOR (set 1, challenge 3): brute force a small key space and score the results to pick the right one. This is the pattern for every "try everything, then filter" attack.
- ECB detection (set 1, challenge 8): recognise a broken mode from the structure of the ciphertext alone. This is the pattern for "read the leaked signal".
- Padding oracle (set 3, challenge 17): use one binary signal (is the padding valid or not) to recover the whole plaintext. This is the pattern for oracle attacks, one of the most elegant attack types in crypto.

## Demo

### Set 1, challenge 3: single-byte XOR

The task gives a hex string. The plaintext is English text XORed with one single byte. Try all 256 bytes, score each result by how English it looks, and keep the highest score.

```python
# c03_single_xor.py: Cryptopals set 1 challenge 3
ENG = {'a':.082,'b':.015,'c':.028,'d':.043,'e':.127,'f':.022,'g':.020,'h':.061,
       'i':.070,'j':.0015,'k':.0077,'l':.040,'m':.024,'n':.067,'o':.075,'p':.019,
       'q':.0010,'r':.060,'s':.063,'t':.091,'u':.028,'v':.0098,'w':.024,'x':.0015,
       'y':.020,'z':.00074,' ':.18}

def score(b):
    return sum(ENG.get(chr(c).lower(), -0.05) for c in b)   # penalize odd bytes

ct = bytes.fromhex("1b37373331363f78151b7f2b783431333d78397828372d363c78373e783a393b3736")
best = max(((k, bytes(c ^ k for c in ct)) for k in range(256)), key=lambda kv: score(kv[1]))
print("key (byte)  :", best[0], hex(best[0]))
print("plaintext   :", best[1].decode())
```

Output:

```
key (byte)  : 88 0x58
plaintext   : Cooking MC's like a pound of bacon
```

The key is the byte `0x58` (the character X). The key space has only 256 values, so brute force is free. The only hard part is the scoring, which must make English plaintext rank above garbage. Giving the space character a high weight and penalising odd bytes is enough for most challenges.

### Set 1, challenge 8: detect AES-ECB

ECB encrypts each 16-byte block independently, so two identical plaintext blocks give two identical ciphertext blocks. Counting duplicate blocks is enough to expose it. We build a self-contained example: one plaintext with repeated blocks, encrypted with ECB and with CBC, then count.

```python
# c08_detect_ecb.py: Cryptopals set 1 challenge 8
from Crypto.Cipher import AES
import os

key = os.urandom(16)
pt = b"YELLOW SUBMARINE" * 3 + b"and some tail xx"   # first 3 blocks are identical
ecb = AES.new(key, AES.MODE_ECB).encrypt(pt)
cbc = AES.new(key, AES.MODE_CBC, iv=os.urandom(16)).encrypt(pt)

def dup_blocks(ct, bs=16):
    blocks = [ct[i:i+bs] for i in range(0, len(ct), bs)]
    return len(blocks) - len(set(blocks))              # number of repeated blocks

print("duplicate blocks (ECB):", dup_blocks(ecb), "-> this is ECB" if dup_blocks(ecb) else "")
print("duplicate blocks (CBC):", dup_blocks(cbc), "-> no pattern leaked")
```

Output:

```
duplicate blocks (ECB): 2 -> this is ECB
duplicate blocks (CBC): 0 -> no pattern leaked
```

Three identical plaintext blocks leave two duplicates in the ECB ciphertext (three equal blocks give two repeats after the first one). CBC has no duplicate block because each block is mixed with the previous one. In the real Cryptopals challenge you scan a file of many hex lines and pick the line with duplicate blocks. That line is the one encrypted with ECB. It is the same counting trick.

### Set 3, challenge 17: padding oracle attack on CBC

This is the classic. The server keeps a secret key and gives you a ciphertext (IV plus blocks) and a single oracle. The oracle tells you whether the ciphertext you send has valid PKCS#7 padding after decryption. From that one bit we recover the whole plaintext without knowing the key.

The principle, recalled from Lesson 4.3, is that in CBC the plaintext block P_i = D(C_i) XOR C_(i-1), where D is block decryption. We control C_(i-1) (the previous block, or the IV). We change the previous block one byte at a time and ask the oracle until the padding is valid. That gives us each byte of D(C_i), and XORing with the real previous block gives the plaintext.

```python
# c17_padding_oracle.py: Cryptopals set 3 challenge 17
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os

KEY = os.urandom(16)
BS = 16

def encrypt():
    pt = b"flag{p4dding_0racle_l34ks_th3_wh0le_plaintext}"
    iv = os.urandom(BS)
    return iv + AES.new(KEY, AES.MODE_CBC, iv).encrypt(pad(pt, BS))

def oracle(iv_ct):                     # the only leak: is the padding valid or not
    iv, ct = iv_ct[:BS], iv_ct[BS:]
    dec = AES.new(KEY, AES.MODE_CBC, iv).decrypt(ct)
    try:
        unpad(dec, BS)
        return True
    except ValueError:
        return False

def attack(iv_ct):
    blocks = [iv_ct[i:i+BS] for i in range(0, len(iv_ct), BS)]
    recovered = b""
    for bi in range(1, len(blocks)):            # solve each block after the IV
        prev, cur = blocks[bi-1], blocks[bi]
        inter = bytearray(BS)                   # inter = D(cur), the intermediate value
        for pad_val in range(1, BS + 1):
            pos = BS - pad_val
            for guess in range(256):
                forged = bytearray(BS)
                for j in range(pos + 1, BS):
                    forged[j] = inter[j] ^ pad_val      # force the later bytes to pad_val
                forged[pos] = guess
                if oracle(bytes(forged) + cur):
                    if pad_val == 1:            # filter noise: confirm it is not caused by the neighbouring byte
                        forged[pos-1] ^= 0xff
                        if not oracle(bytes(forged) + cur):
                            continue
                    inter[pos] = guess ^ pad_val
                    break
        recovered += bytes(inter[j] ^ prev[j] for j in range(BS))
    return recovered

if __name__ == "__main__":
    iv_ct = encrypt()
    pt = attack(iv_ct)
    print("plaintext (with padding):", pt)
    print("flag:", unpad(pt, BS).decode())
```

Output:

```
plaintext (with padding): b'flag{p4dding_0racle_l34ks_th3_wh0le_plaintext}\x02\x02'
flag: flag{p4dding_0racle_l34ks_th3_wh0le_plaintext}
```

We never touch the key. All we use is the answer to "is the padding valid", repeated a few thousand times. Note the noise filter at `pad_val == 1`. When searching for the byte that gives padding 1, a false hit can happen because the neighbouring byte also happens to form valid padding. So we flip the byte before it and ask again to be sure it is a one-byte padding. Without this step you occasionally get a wrong plaintext at a block boundary.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 11.1</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/11.1.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/11.1/c03_single_xor.py" download><i class="fa-solid fa-file-code"></i>c03_single_xor.py</a>
<a class="lab-file" href="/assets/labs-crypto/11.1/c08_detect_ecb.py" download><i class="fa-solid fa-file-code"></i>c08_detect_ecb.py</a>
<a class="lab-file" href="/assets/labs-crypto/11.1/c17_padding_oracle.py" download><i class="fa-solid fa-file-code"></i>c17_padding_oracle.py</a>
</div>
</div>

- Task: all three scripts above run as they are. Retype each one from scratch without looking, then compare with the version above.
- Extend set 1: turn `c03` into the repeating-key XOR solver (challenge 6) that you did in Lesson 3.3, and write challenge 5 (encrypt with repeating-key XOR) to close the XOR part of set 1.
- Extend set 2: starting from `c08`, do byte-at-a-time ECB decryption (challenge 12). The idea is to feed in a growing input so each secret byte is pushed across a block boundary, then look it up in a table.
- Extend set 3: turn `attack` in `c17` into a function that takes any IV and ciphertext, then try it on a multi-block ciphertext to see that it decrypts every block.
- Hints, step by step: (1) always work on `bytes`; (2) in the padding oracle, solve each block independently and use the block right before it as the lever; (3) go from the last byte of the block (padding 1) back to the first; (4) remember the noise filter for the padding 1 byte.
- Done when: the three scripts print the same results as in the demo section, and you have solved at least the first 10 challenges of set 1 on the original site.

## Key takeaways

- Cryptopals teaches breaking by making you code the attacks yourself, with no answer key.
- Single-byte XOR: the key space is 256, so brute force it and score by English letter frequency.
- ECB leaks because identical plaintext blocks give identical ciphertext blocks. Counting duplicate blocks is enough.
- Padding oracle: one bit, "padding valid", is enough to recover the full plaintext without the key.
- In CBC, P_i = D(C_i) XOR C_(i-1), and controlling C_(i-1) is what makes the oracle attack work.
- Always work on bytes, and build helper functions you can reuse across the sets.

## Common pitfalls

- Mixing `str` with `bytes`. Every XOR, slice, and comparison must be on bytes. Decode only at the final print.
- A scorer that is too weak makes single-byte XOR pick the wrong byte. Missing weight for the space or no penalty for control bytes often fails.
- Forgetting the noise filter at `pad_val == 1` in the padding oracle, which gives a wrong byte at a block boundary with no obvious reason.
- Getting the order wrong in the padding oracle. The known bytes must be forced to the current padding value (`pad_val`), not left unchanged.
- Thinking ECB detection needs the key. It does not. You only look at the ciphertext structure, which is the point of the challenge.
- Using CTR or GCM and expecting a padding oracle to work. A padding oracle only applies to modes with padding such as CBC. Stream modes have no padding.

## Further reading

- cryptopals.com is the original source. Work through it in order from set 1. There is no answer key, so do not look for solutions early. The struggle is what builds skill.
- Lessons 3.1, 3.3 (XOR) and Lessons 4.2, 4.3 (modes and padding oracle) in this series are the theory behind the three challenges here.
- "The Cryptopals Crypto Challenges" has many community write-ups on GitHub. Look only after you have tried it yourself and are really stuck.
- CryptoHack is a web-based challenge set with automatic grading, a good companion to Cryptopals.
- Lessons 11.2 (writing a write-up) and 11.3 (the protocol analysis project) in this series are the next step once you are comfortable solving challenges.
