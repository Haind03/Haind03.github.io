---
title: "Lesson 3.1: Single-Byte and Multi-Byte XOR"
image:
  path: /assets/img/covers/crypto-3-1-single-byte-multi-byte-xor.webp
  alt: "Single-Byte and Multi-Byte XOR"
date: 2026-10-09 11:05:00 +0700
categories: ["Cryptography", "Crypto · XOR and OTP"]
tags: [cryptography, xor, repeating-key-xor, hamming-distance]
render_with_liquid: false
---

XOR is the base of almost every stream cipher. This lesson covers breaking single-byte XOR by brute-forcing 256 keys, extending that to multi-byte (repeating-key) XOR, guessing the key length with Hamming distance, and using crib dragging when you already know a piece of the plaintext. After it you can write your own XOR solver for CTFs.

![Breaking repeating-key XOR: guess key length, split into columns, solve each column](/assets/img/crypto/crypto-3-1-single-byte-multi-byte-xor.svg)
_Repeating-key XOR reduces to a key length guess plus one single-byte problem per column._

Level: medium, about 45 minutes. Prerequisite: Lesson 2.2 (frequency analysis, the English scoring is reused here) and basic bytes handling in Python. Tools: Python 3 with the standard library only.

## Goals

You will know the XOR properties and why XOR underlies stream ciphers. You will break single-byte XOR by trying all 256 keys and scoring the results. You will guess the key length of repeating-key XOR with normalized Hamming distance, split the ciphertext by key length, and break each key byte as a single-byte problem. You will also use crib dragging to recover the key when you know part of the plaintext.

## Theory

### What XOR is and why it suits cryptography

XOR (exclusive or) works on each bit: two equal bits give 0, two different bits give 1.

```
0 xor 0 = 0
0 xor 1 = 1
1 xor 0 = 1
1 xor 1 = 0
```

Four properties you must know by heart, because every XOR attack relies on them:

1. Self-inverse: `a xor b xor b = a`. Encryption and decryption use the same operation. Encryption is `c = p xor k`, decryption is `p = c xor k`.
2. Commutative and associative: `a xor b = b xor a`, and `(a xor b) xor c = a xor (b xor c)`. The order does not matter.
3. Identity element: `a xor 0 = a`. XOR with 0 changes nothing.
4. Self-cancelling: `a xor a = 0`. XOR of a value with itself is all zeros.

Property 4 is the key to many attacks. If two ciphertexts use the same key, XOR them together and the key cancels, leaving only the XOR of the two plaintexts. You will see this again in Lesson 3.2 (two-time pad).

A stream cipher is in essence: generate a pseudo-random keystream as long as the plaintext, then XOR it byte by byte. RC4, ChaCha20, and OTP all follow this pattern. So understanding XOR means understanding the core.

### Single-byte XOR: a one-byte key

The simplest form takes one key byte k (0 to 255) and XORs it into every byte of the plaintext.

```
c[i] = p[i] xor k   for every i
```

The key has only 256 values, so you break it by brute force: try all 256 keys, get 256 candidate plaintexts, then score which one looks most like English (or like printable text). The scoring counts printable characters, rewards common letters and the space, and penalizes control bytes. Reusing the English frequency chi-squared idea from Lesson 2.2 is the standard approach. The highest-scoring candidate is almost always the real plaintext, and its key is the key byte.

### Multi-byte XOR: repeating-key (Vigenere on bytes)

The key is m bytes long and repeats along the plaintext:

```
c[i] = p[i] xor k[i mod m]
```

This is Vigenere done on bytes instead of letters. It breaks by the same logic as Lesson 2.2. If you know the key length m, split the ciphertext into m groups (group j holds the bytes at positions j, j+m, j+2m, ...). Each group is XORed with exactly one key byte, so it is a single-byte problem. Solving m single-byte problems gives the whole key.

So breaking repeating-key XOR reduces to two familiar steps: find m, then break single-byte m times. The difference from Vigenere is that you use Hamming distance to guess m instead of IoC (bytes are not letters, so the letter-based IoC does not apply directly).

### Finding the key length with Hamming distance

The Hamming distance between two byte sequences is the number of differing bits. For example `'A'` (0x41 = 0100 0001) and `'C'` (0x43 = 0100 0011) differ in 1 bit, so the Hamming distance is 1.

Why does it help guess the key length? Two arbitrary English plaintext segments of the same length are fairly similar in their bits because they use a narrow character set, so their Hamming distance is small. Two random byte segments differ in about half of their bits (a normalized Hamming distance of about 4 bits per byte).

Now suppose you cut the ciphertext into blocks of exactly the true key length m. Each block is XORed with the same key string. XORing two such blocks cancels the key and leaves the XOR of two plaintext segments, which are similar in bits, so the Hamming distance is small. If you cut at the wrong length, the key does not cancel, the bytes look random, and the Hamming distance is large. So the true m is the value with the smallest Hamming distance (normalized by m).

The procedure from Cryptopals challenge 6 is this. For each candidate m, take several pairs of consecutive m-byte blocks, compute the Hamming distance, divide by m to normalize, and average. The m with the smallest average is the best candidate. Always average many pairs, because a single pair is noisy.

### Crib dragging: when you know a piece of plaintext

A crib is a piece of plaintext you believe is in the message, for example `flag{`, `the `, `GET /`, `<?xml`. With XOR, if the crib really sits at position i, then XORing the crib with the ciphertext there reveals the key bytes at that position:

```
k = c xor p   (since c = p xor k)
```

Crib dragging slides the crib along the ciphertext and at each position XORs out a candidate key segment. If that segment looks meaningful (with repeating-key XOR the key is often a readable word), or if XORing it into another part of the ciphertext gives readable text, you have a hit. It is especially strong when the key is a meaningful string, or when two messages share a keystream (two-time pad, Lesson 3.2).

### Three questions to answer

1. What does correct use look like: if the keystream is truly random and never repeats, XOR is secure (that is OTP, Lesson 3.2).
2. Where does it fail: the key is too short (single-byte: 256 possibilities) or repeats (repeating-key leaks structure by column).
3. How is it exploited: brute-force 256, or find the key length and break each column, or crib dragging when there is a guessable plaintext.

## Demo

### Single-byte XOR brute force

```python
# xor_single.py: break single-byte XOR with a 256-key brute force + English scoring
def xor_bytes(data, key_byte):
    return bytes(b ^ key_byte for b in data)

def score_english(data):
    # score by the frequency of characters common in English text; high = looks like real text
    weights = {
        **{ord(c): 3 for c in "ETAOIN SHRDLU"},          # common letters + space
        **{ord(c.lower()): 3 for c in "ETAOINSHRDLU"},
    }
    score = 0
    for b in data:
        if b in weights:
            score += weights[b]
        elif 0x20 <= b < 0x7f:                            # other printable character: small reward
            score += 1
        else:
            score -= 5                                    # control byte: heavy penalty
    return score

ciphertext = bytes.fromhex(
    "1b37373331363f78151b7f2b783431333d78397828372d363c78373e783a393b3736")
best = max(range(256), key=lambda k: score_english(xor_bytes(ciphertext, k)))
print("Key byte  :", best, hex(best))
print("Plaintext :", xor_bytes(ciphertext, best).decode(errors="replace"))
```

Output:

```
Key byte  : 88 0x58
Plaintext : Cooking MC's like a pound of bacon
```

The key has only 256 possibilities, so this is instant. The scoring function decides everything. With good scoring the real plaintext is top 1 right away. When stuck, print the top 3 candidates and look at them by eye.

### Repeating-key XOR: encryption

```python
# xor_repeating.py: repeating-key encryption (also used in the lab)
import itertools

def xor_repeating(data, key):
    return bytes(b ^ k for b, k in zip(data, itertools.cycle(key)))

pt = b"Burning 'em, if you ain't quick and nimble"
key = b"ICE"
ct = xor_repeating(pt, key)
print("Ciphertext hex:", ct.hex())
print("Decrypted back:", xor_repeating(ct, key).decode())
```

`itertools.cycle(key)` repeats the key forever and `zip` cuts it to the length of the data. Because XOR is self-inverse, the same function also decrypts.

### Find the key length with Hamming distance, then break each column

```python
# xor_break.py: break repeating-key XOR end to end, like Cryptopals challenge 6
import itertools

def hamming(a, b):
    # number of differing bits between two byte strings of equal length
    return sum(bin(x ^ y).count("1") for x, y in zip(a, b))

def xor_bytes(data, key_byte):
    return bytes(b ^ key_byte for b in data)

def score_english(data):
    weights = {**{ord(c): 3 for c in "ETAOIN SHRDLU"},
               **{ord(c.lower()): 3 for c in "ETAOINSHRDLU"}}
    s = 0
    for b in data:
        if b in weights: s += 3
        elif 0x20 <= b < 0x7f: s += 1
        else: s -= 5
    return s

def guess_keysizes(ct, lo=2, hi=40, max_blocks=12):
    scores = []
    for ks in range(lo, hi + 1):
        nblocks = min(max_blocks, len(ct) // ks)          # use as many blocks as the data allows
        if nblocks < 2:
            continue
        chunks = [ct[i*ks:(i+1)*ks] for i in range(nblocks)]
        # average Hamming over ALL block pairs to reduce noise
        dists = [hamming(a, b) / ks
                 for a, b in itertools.combinations(chunks, 2)
                 if len(a) == len(b) == ks]
        if dists:
            scores.append((sum(dists) / len(dists), ks))
    scores.sort()                                         # smallest normalized Hamming first
    return scores

def break_single(column):
    best_k = max(range(256), key=lambda k: score_english(xor_bytes(column, k)))
    return best_k

def break_repeating(ct):
    ks = guess_keysizes(ct)[0][1]                         # take the best key length
    # split ct into ks columns: column j holds the bytes at positions j, j+ks, j+2ks, ...
    columns = [ct[j::ks] for j in range(ks)]
    key = bytes(break_single(col) for col in columns)
    plaintext = bytes(b ^ key[i % len(key)] for i, b in enumerate(ct))
    return key, plaintext

# Build demo data: encrypt a long English passage with the key "CRYPTO"
# (the passage must be LONG ENOUGH for stable Hamming statistics, a few hundred bytes or more)
sample = (b"We hold these truths to be self-evident, that all men are created equal, "
          b"that they are endowed by their creator with certain unalienable rights, "
          b"that among these are life, liberty and the pursuit of happiness. Whenever "
          b"any form of government becomes destructive of these ends, it is the right "
          b"of the people to alter or to abolish it, and to institute new government.")
demo_key = b"CRYPTO"
demo_ct = bytes(b ^ demo_key[i % len(demo_key)] for i, b in enumerate(sample))

print("Top 5 key lengths:", [(round(d,3), k) for d,k in guess_keysizes(demo_ct)[:5]])
key, pt = break_repeating(demo_ct)
print("Key found        :", key)
print("Plaintext        :", pt.decode(errors="replace")[:60], "...")
```

Output:

```
Top 5 key lengths: [(2.386, 6), (2.463, 18), (2.515, 24), (2.519, 12), (2.531, 36)]
Key found        : b'CRYPTO'
Plaintext        : We hold these truths to be self-evident, that all men are cr ...
```

The flow is to guess the key length with normalized Hamming distance (the true length gives the smallest value), split the ciphertext into columns by that length, break each column as single-byte, join the bytes into the key, and decrypt. In the top 5, 6 is correct and first, but the multiples 12, 18, 24, 36 follow close behind (they also make the key cancel). That is why, when the recovered key turns out to be repeated, the real length is a divisor of it. This is the skeleton of Cryptopals challenge 6.

### Crib dragging

```python
# crib_drag.py: drag a crib along the ciphertext and reveal candidate key segments
def crib_drag(ct, crib):
    crib = crib.encode() if isinstance(crib, str) else crib
    for i in range(len(ct) - len(crib) + 1):
        segment = ct[i:i+len(crib)]
        key_guess = bytes(c ^ p for c, p in zip(segment, crib))
        # only print positions where the candidate key is all printable (a sign of a hit)
        if all(0x20 <= b < 0x7f for b in key_guess):
            print(f"pos {i:3d}: key='{key_guess.decode()}'")

import itertools
pt = b"the secret password is hunter2, keep it safe"
key = b"LONGKEY"
ct = bytes(b ^ k for b, k in zip(pt, itertools.cycle(key)))
# Suppose we guess the message contains the word "password"
crib_drag(ct, "password")
```

Output:

```
pos  11: key='KEYLONGK'
```

The crib `password` sits at position 11 of the plaintext, and exactly there the candidate key segment shows up as `KEYLONGK`, which is a slice of the key `LONGKEY` wrapped around (starting partway through). When the key is a meaningful string, the eye spots the correct key slice among the garbage right away. Most wrong positions contain non-printable bytes and are filtered out.

## Lab

- Task: the file `cipher.hex` (you create it yourself following the demo) holds a long English passage encrypted with repeating-key XOR, with a key of 2 to 10 bytes. Recover the key and the plaintext. The plaintext contains a flag in the form `flag{...}`.
- Provided file: generate it with `xor_repeating` from the demo, inserting a flag into the plaintext before encrypting.
- Hint 1: do not guess the key first. Guess the key length first with normalized Hamming distance. Average many block pairs, since one pair is noisy.
- Hint 2: once you have the key length, each column is a single-byte problem. Brute-force 256 and score each column independently.
- Hint 3: if a few key bytes are wrong (short columns, noisy statistics), use the crib `flag{` or ` the ` to fix those positions by hand.
- Done when: you print the key and a readable plaintext containing the flag.

As an extension, take the real data of Cryptopals challenge 6 (the base64 file on cryptopals.com), decode the base64 into bytes, and run `break_repeating`. The real key is a famous lyric, so you can check whether you got it right.

## Key takeaways

- XOR is self-inverse, so the same operation is used to encrypt and decrypt.
- `a xor a = 0`: with a shared key, XORing two ciphertexts removes the key.
- Single-byte XOR: 256 keys, brute-force them all and score for English.
- Repeating-key XOR is Vigenere on bytes: find the key length, then break each single-byte column.
- The smallest normalized Hamming distance points to the true key length.
- Crib dragging reveals key segments when you guess a piece of the plaintext correctly.

## Common pitfalls

- A scoring function that is too crude (only counting printable characters). Many wrong keys still give all printable characters. Reward common letter frequencies and the space, and penalize control bytes, so the results separate clearly.
- Forgetting that the space is the most common character in English text. Giving the space a high weight makes top 1 much more reliable.
- Using only one block pair when guessing the key length. The Hamming distance of one pair is very noisy, so average many pairs.
- Picking a multiple of the key length by mistake. As with Vigenere, 2m and 3m also give a low Hamming distance. If the recovered key repeats (for example `ICEICE`), the real length is a divisor of it.
- Slicing columns with the wrong index. `ct[j::ks]` is column j (the bytes XORed with the same key byte). Do not cut into consecutive blocks.
- Calling `.decode()` while strange bytes remain raises an error. Use `errors="replace"` while exploring, and decode strictly only when you are sure the key is right.
- Mixing up lengths when XORing two arrays of different length. `zip` cuts to the shorter array and can drop the tail of the data silently.

## Further reading

- Cryptopals set 1, challenge 3 (single-byte XOR), 5 (repeating-key encrypt), 6 (break repeating-key XOR): the source of everything here, worth doing in full.
- CryptoHack, XOR section: a series from the XOR properties to crib dragging, well organized.
- The `xortool` tool (guesses the key length and the most frequent byte automatically) to compare against your manual result.
- Continue with Lesson 3.2 (one-time pad) to see why repeating-key breaks while OTP is perfectly secure, and what happens when a key is reused.
