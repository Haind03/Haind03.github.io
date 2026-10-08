---
title: "Lesson 4.1: Block Ciphers and AES Basics"
image:
  path: /assets/img/covers/crypto-4-1-block-ciphers-aes-basics.webp
  alt: "Block Ciphers and AES Basics"
date: 2026-10-09 12:05:00 +0700
categories: ["Cryptography", "Crypto · Symmetric Encryption"]
tags: [cryptography, aes, block-cipher, avalanche]
render_with_liquid: false
---

This lesson answers one question, which is what AES actually does. After it you can tell a block cipher from a stream cipher, you know how many bytes AES takes in and gives out, you understand why it mixes so well that flipping one input bit changes about half of the output, and you know the key schedule well enough not to be put off when reading a write-up.

![AES as a keyed permutation on one 16-byte block, with rounds and round keys](/assets/img/crypto/crypto-4-1-block-ciphers-aes-basics.svg)
_AES maps one 16-byte block to one 16-byte block under a key, through 10, 12, or 14 rounds._

Level: medium, about 25 minutes. Prerequisite: Lesson 3.1 (single-byte and multi-byte XOR). Knowing hex, bytes, and XOR is enough. No linear algebra is needed. Tools: Python 3 and PyCryptodome (`pip install pycryptodome`).

## Goals

You will state what a block cipher is and why it is only a keyed permutation on a fixed-size block of data. You will remember exactly that AES works on a 16-byte block with a 16/24/32-byte key, no more and no less. You will encrypt one block yourself and observe the avalanche effect (change one bit, about half of the output flips). You will explain the key schedule at an overview level without implementing each round. And you will see why AES alone is not secure encryption and must be combined with a mode.

## Theory

### What a block cipher is

A block cipher is a function that takes exactly one block of fixed size, plus a key, and returns a block of the same size. For AES the block is 16 bytes (128 bits). You give it 16 bytes of plaintext and a key, and it returns 16 bytes of ciphertext. Give the decryption function the same key, and those 16 bytes of ciphertext turn back into the original 16 bytes of plaintext.

The point to fix in your head is that for a fixed key, a block cipher is a bijection (a one-to-one mapping) on the set of all 16-byte blocks. Each 16-byte plaintext maps to exactly one 16-byte ciphertext, with no collisions and nothing lost. There are 2^128 possible blocks, and each key selects one permutation of those 2^128 elements. AES is just a way to generate a random-looking permutation from a key, compact enough to run in hardware.

Cryptographers formalize this with the concept of a PRP (pseudorandom permutation), where an attacker cannot distinguish AES from a truly random permutation if he does not know the key. You do not need to prove anything here. Keep the intuition that AES is a byte-shuffling box that can be reversed if you have the key.

### How much AES takes in and gives out

Three numbers to know by heart:

- Block size: always 16 bytes. AES-128, AES-192, and AES-256 all have a 16-byte block. Only the key length differs.
- Key size: 16 bytes (AES-128), 24 bytes (AES-192), or 32 bytes (AES-256). There is no AES-512. Anyone who mentions AES-512 is making it up.
- Number of rounds: 10 rounds for a 128-bit key, 12 for 192-bit, 14 for 256-bit.

What if your plaintext is not a multiple of 16 bytes? The block cipher itself does not accept it, because it only knows exactly 16 bytes. To encrypt data of any length you must cut it into several blocks and chain them with a mode of operation, which is the topic of Lesson 4.2. To make the last block a full 16 bytes you need padding (adding extra bytes), which is Lesson 4.3. Keep these three layers separate in your head. The block cipher handles one block, the mode handles chaining, and padding handles the partial block.

### Inside the box (a top-down view)

You do not need to implement AES to attack it, and almost no CTF challenge asks you to break AES itself. But knowing roughly what it does makes the documentation less overwhelming. AES arranges the 16 bytes into a 4x4 grid called the state, then repeats several rounds, each with four steps:

1. SubBytes: replace each byte with another byte through a fixed lookup table called the S-box. This is the nonlinear step, and it is why AES cannot be solved with linear algebra.
2. ShiftRows: rotate the rows of the grid, mixing byte positions.
3. MixColumns: mix the bytes within each column using multiplication in the finite field GF(2^8). This step spreads the influence of one byte across the whole column.
4. AddRoundKey: XOR the state with the round key (subkey) of that round.

The last round skips MixColumns, a detail that does not matter for us. What matters is that ShiftRows and MixColumns together create diffusion, SubBytes creates confusion, and after enough rounds one input bit affects every output bit. That is the avalanche effect we measure ourselves in the demo.

### What the key schedule is

Each round needs its own 16-byte round key instead of reusing the original key. The key schedule is the procedure that expands the original key into a sequence of round keys. For AES-128 it produces 11 round keys of 16 bytes (one for the initial AddRoundKey plus 10 rounds), 176 bytes in total. The expansion splits the key into 4-byte words, then produces new words by XORing the earlier word with a function of the nearest word (rotate the bytes, pass them through the S-box, XOR with a round constant).

You do not need to code the key schedule again. Remember two things that are useful when attacking:

- The AES key schedule is invertible: if you know enough round keys you can work backward to the original key. In some side-channel or fault attacks people recover the last round key and compute backward. This is not the job of ordinary CTF crypto, but it is good to know it exists.
- The key schedule adds no entropy. If the original key is weak (for example only 4 random bytes that are then repeated), expanding it to 176 bytes does not make it stronger. Security still rests on the original key.

### Why AES alone is not secure encryption

AES is only a machine that scrambles one block. If you use that machine to encrypt each 16-byte block independently (that is ECB mode), two identical plaintext blocks give two identical ciphertext blocks. An attacker looking at the ciphertext sees right away where the plaintext repeats. So the sentence "I encrypt with AES" says nothing yet. You must ask what mode, where the IV/nonce is, and whether there is authentication. All the following lessons of this part revolve around exactly those three questions.

## Demo

This demo attacks nothing. It lets you handle the black box to confirm three properties, namely that it is deterministic, it is reversible, and it shows avalanche. Paste it and run it directly.

```python
# demo_aes_blackbox.py: AES as a black box for one block
import os
from Crypto.Cipher import AES

def hexs(b):
    return b.hex()

def popcount_diff(a: bytes, b: bytes) -> int:
    # count the differing bits between two byte strings of equal length
    return sum(bin(x ^ y).count("1") for x, y in zip(a, b))

def main():
    key = bytes.fromhex("000102030405060708090a0b0c0d0e0f")  # fixed 16 bytes
    pt  = bytes.fromhex("00112233445566778899aabbccddeeff")  # exactly 1 block of 16 bytes

    ecb = AES.new(key, AES.MODE_ECB)
    ct = ecb.encrypt(pt)
    print("plaintext :", hexs(pt))
    print("ciphertext:", hexs(ct))

    # 1) deterministic: same input and same key always give the same output
    ct2 = AES.new(key, AES.MODE_ECB).encrypt(pt)
    print("encrypting again gives the same result:", ct == ct2)

    # 2) reversible: decryption returns the exact plaintext
    back = AES.new(key, AES.MODE_ECB).decrypt(ct)
    print("decryption restores the plaintext:", back == pt)

    # 3) avalanche: flip exactly 1 plaintext bit, count how many ciphertext bits change
    pt_flip = bytearray(pt)
    pt_flip[0] ^= 0x01            # flip the lowest bit of the first byte
    ct_flip = AES.new(key, AES.MODE_ECB).encrypt(bytes(pt_flip))
    diff = popcount_diff(ct, ct_flip)
    print("ciphertext bits changed when flipping 1 input bit:", diff, "/ 128")

    # avalanche when flipping 1 bit of the KEY (plaintext unchanged)
    key_flip = bytearray(key)
    key_flip[0] ^= 0x01
    ct_key = AES.new(bytes(key_flip), AES.MODE_ECB).encrypt(pt)
    print("ciphertext bits changed when flipping 1 key bit  :", popcount_diff(ct, ct_key), "/ 128")

if __name__ == "__main__":
    main()
```

Running it, you will see something like:

```
plaintext : 00112233445566778899aabbccddeeff
ciphertext: 69c4e0d86a7b0430d8cdb78070b4c55a
encrypting again gives the same result: True
decryption restores the plaintext: True
ciphertext bits changed when flipping 1 input bit: 62 / 128
ciphertext bits changed when flipping 1 key bit  : 59 / 128
```

The numbers 62 and 59 change depending on which bit you flip, but they always stay around 64, which is half. The key/plaintext pair in the demo is the standard AES-128 test vector from the FIPS-197 appendix. The ciphertext `69c4e0d8...` matches the original document, so you can use it to check that your library works correctly.

The two avalanche lines are the part worth looking at. Flipping exactly one input bit changes about half of the 128 output bits. That is the sign of a well-mixing block cipher, since from observing the ciphertext there is no way to tell that a similar input gives a similar output. Because of this property you cannot search for a key bit by bit, since the output does not change smoothly with the input.

PyCryptodome does not expose the key schedule directly, but you can compute its size. AES-128 needs 11 round keys x 16 bytes = 176 bytes, and AES-256 needs 15 x 16 = 240 bytes.

## Lab

- Task: you are given a black-box function `black_box(data: bytes) -> bytes` (simulated by a service or a function in the lab file). It encrypts `data` with a block cipher under a fixed key you do not know. Determine (a) the block size of the cipher in bytes, and (b) whether the cipher encrypts each block independently, only by sending input and looking at the output, without knowing the key.
- Provided file: see the Lab section below if a sample exists. If not, build it yourself: write a `black_box` function using `AES.MODE_ECB` with a fixed random key, but when analyzing pretend you do not know it is AES or ECB.
- Hint 1: send inputs of growing length (1, 2, 3... bytes) and see where the output length jumps. The size of the jump is the block size.
- Hint 2: send an input made of many identical blocks (for example 48 bytes of the letter A). If the output has two identical 16-byte blocks, the cipher encrypts each block independently.
- Hint 3: change exactly one input byte and compare outputs. If only one output block changes, the blocks are independent. If several blocks change, there is chaining (CBC/CTR, covered in Lesson 4.2).
- Done when: you print the block size as exactly 16, and correctly conclude that the cipher works in the mode where each block is independent.

## Key takeaways

- AES block size is always 16 bytes, key 16/24/32 bytes, rounds 10/12/14. There is no AES-512.
- For a fixed key, a block cipher is a bijection on 16-byte blocks, and decryption is the inverse mapping.
- Avalanche: changing one input bit or key bit flips about half of the output bits. That is why you cannot search for the key gradually.
- The key schedule expands the original key into round keys, is invertible, and adds no entropy.
- AES alone is not secure encryption: you must state the mode, the IV/nonce, and whether there is integrity.

## Common pitfalls

- Thinking "a longer key makes the mode better". A 256-bit key does not fix a mode mistake. ECB with AES-256 leaks patterns exactly like AES-128.
- Confusing block size with key size. Beginners often think AES-256 has a 32-byte block. That is wrong: the block is still 16 bytes, only the key is 32 bytes.
- Thinking AES handles padding itself. It does not. The block cipher only processes exactly 16 bytes. Padding belongs to the layer above, and forgetting to strip the padding after decryption is a classic bug.
- Calling `AES.MODE_ECB` in real code and believing it is "secure encryption". ECB is almost always a bug, except in a few very narrow cases (encrypting exactly one random block). ECB in a real application is a red flag most of the time.
- Reusing the same PyCryptodome cipher object for several encryptions. With ECB it is fine, but with CBC/CTR the object carries state, and calling `encrypt` several times continues instead of resetting. Create a new object for each message to be safe.

## Further reading

- FIPS-197, the NIST standard for AES. Read the test vectors in the appendix to compare against your library.
- A Graduate Course in Applied Cryptography (Boneh, Shoup), the chapter on block ciphers and the PRP/PRF concepts.
- Cryptopals Set 1 Challenge 7 (AES in ECB mode) to get used to calling AES through a library.
- CryptoHack, the Symmetric Ciphers path, AES section, from "Keyed Permutations" to "Structure of AES".
