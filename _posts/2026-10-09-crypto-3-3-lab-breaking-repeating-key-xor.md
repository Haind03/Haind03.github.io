---
title: "Lesson 3.3: Lab on Breaking Repeating-Key XOR"
image:
  path: /assets/img/covers/crypto-3-3-lab-breaking-repeating-key-xor.webp
  alt: "Lab on Breaking Repeating-Key XOR"
date: 2026-10-09 11:15:00 +0700
categories: ["Cryptography", "Crypto · XOR and OTP"]
tags: [cryptography, xor, cryptopals, lab]
render_with_liquid: false
---

This lab combines all of Part 3: breaking repeating-key XOR from start to finish, exactly like Cryptopals challenge 6. You assemble Hamming distance, column splitting, single-byte brute force, and scoring into one solve script that outputs both the key and the plaintext in a single run. The Lab section has the complete Python solver and the challenge data so you can run it right away.

![Pipeline for breaking repeating-key XOR: keysize, columns, single-byte, key](/assets/img/crypto/crypto-3-3-lab-breaking-repeating-key-xor.svg)
_Four steps: guess the keysize, split into columns, break each column, rebuild the key and decrypt._

Level: medium to hard, about 60 minutes. Prerequisites: Lesson 3.1 (single/multi-byte XOR, Hamming distance, crib dragging) and Lesson 2.2 (frequency scoring). This is a hands-on lesson that puts everything together. Tools: Python 3 with the standard library (only `base64` and `itertools`).

## Goals

You will write a complete repeating-key XOR solver that runs from ciphertext to plaintext. You will understand why guessing the key length is the hardest step and how to make it stable. You will know the trick of reducing the key to its smallest period when you picked a multiple of the key length. You will solve the sample challenge with an embedded flag and be ready for Cryptopals challenge 6 itself.

## Theory

This lesson adds no new theory. It shows how to join the pieces of Lesson 3.1 into a complete pipeline. Here is the path again, since the order matters:

1. Guess the key length (keysize). For each candidate length m, cut the ciphertext into m-byte blocks, compute the Hamming distance between pairs of blocks, and divide by m to normalize. Blocks aligned with the same key offset differ in fewer bits, so the true length (and its multiples) give a small normalized Hamming distance.
2. Split by column. With m known, column j holds the bytes at positions j, j+m, j+2m, ... Each column is XORed with exactly one key byte.
3. Break each column as single-byte XOR. Brute-force 256 values per column, score how English-like the decrypted column is, and keep the best key byte.
4. Assemble the key and decrypt. Join the key bytes and XOR the repeating key over the whole ciphertext.

The only hard part is step 1. One fact avoids a lot of trouble. The best-scoring keysize candidates are almost always multiples of the true length, and not always the true length itself. The reason is that if m is a multiple of the true length, m-byte blocks still align with the key, so the Hamming distance stays small. The true length often is not even top 1 because of statistical noise.

Two practical consequences:

- Decrypting with a multiple of the true length still gives the correct plaintext, as long as each column has enough bytes for a reliable single-byte brute force. Each column of a multiple keysize still corresponds to a single key byte.
- Take the smallest keysize candidate among the top group (the most bytes per column, so the most stable single-byte step), and at the end reduce the recovered key to its smallest period. For example if you recover the key `b'STRIKESTRIKE'`, its smallest period is `b'STRIKE'`.

These are the two places where beginners make the script fail and then wrongly blame the algorithm.

## Demo

Before the lab, run each piece on a small example to see how they fit.

For the first piece, check the Hamming function with the classic Cryptopals pair. The Hamming distance between `this is a test` and `wokka wokka!!!` must be exactly 37.

```python
def hamming(a, b):
    return sum(bin(x ^ y).count("1") for x, y in zip(a, b))

print(hamming(b"this is a test", b"wokka wokka!!!"))   # must give 37
```

If you get 37 the function is right. A wrong number is the classic bug: forgetting to count bits, or comparing bytes instead of bits.

Second piece, run the whole pipeline on an English passage of almost 400 bytes encrypted with the key `LIME` (4 bytes), using the `solve` from the Lab section:

```python
# assume solve, guess_keysizes, break_single_byte were imported from solve_xor.py in the Lab section
demo_pt = ("the index of coincidence tells you whether a cipher is monoalphabetic, but for a "
"repeating key xor over raw bytes we lean on the hamming distance instead. split the "
"ciphertext into blocks the size of the key, and blocks that line up with the same key "
"bytes will differ in fewer bits than random data would, which is exactly the signal we "
"use to pick the keysize before we ever touch a single column.").encode()
ct = bytes(b ^ b"LIME"[i % 4] for i, b in enumerate(demo_pt))

print("keysize top6:", [(round(d,3), k) for d,k in guess_keysizes(ct)[:6]])
key, pt = solve(ct)
print("key   :", key)
print("pt    :", pt.decode()[:70])
```

Output:

```
keysize top6: [(2.502, 25), (2.553, 8), (2.557, 24), (2.56, 20), (2.562, 12), (2.563, 36)]
key   : b'LIME'
pt    : the index of coincidence tells you whether a cipher is monoalphabetic,
```

Look closely at the keysize table to see the trap mentioned in the theory. The real length is 4, yet top 1 is 25 (noise), while 8, 24, 20, 12, 36 in the top group are all multiples of 4. The script does not trust top 1 blindly. It takes the smallest candidate in the top group (here 8, a multiple of 4), splits into 8 columns that are all long enough, breaks out `b'LIMELIME'`, and reduces it to `b'LIME'`. This is why the smallest-period step matters.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 3.3</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/3.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/3.3/gen_challenge.py" download><i class="fa-solid fa-file-code"></i>gen_challenge.py</a>
<a class="lab-file" href="/assets/labs-crypto/3.3/solve_xor.py" download><i class="fa-solid fa-file-code"></i>solve_xor.py</a>
</div>
</div>

This is the main part. The goal is to get the flag from a ciphertext encrypted with repeating-key XOR.

The lab files are `solve_xor.py`, `challenge.b64`, `gen_challenge.py`, and `transcript.txt` (the real output, with the flag `flag{h4mming_distance_unlocks_the_keysize}`). Run `python3 solve_xor.py challenge.b64` to get the result.

### Task

Below is a ciphertext encrypted with repeating-key XOR and then base64-encoded (the same data format as Cryptopals challenge 6). The plaintext contains a flag in the form `flag{...}`. Recover the key and the plaintext.

Save this base64 block to a file named `challenge.b64`:

```
BDw3J2s8PCFyEQQXczVyOSckOjomLDMxczU1KCIrICByKGs3NiQ3KD8sPTNyIi48f3QmIS5lMD0iIS43JzEqPWs2Jz0+JWsmMiYgIC42cyA6LGs2OzUiLGsqNXQmIS5lPzU8Lj4kNDFyPCUhNiY8LCoxO3Q7PWVlFiI3OzJlMDs+PCYrcyA6KD9lPz08LDhlJiRyPiIxO3Q9Jy5lMS0mLGsqNXQmIS5lODEraSI2czo9PSMsPTNyJCQ3NnQmISorczVyOiIrNDg3aSk8JzFyEQQXf3QzJy9lMnQhICUiPzFyKzIxNnQKBhllOidyPTksJT0zJSc8czYgJiAgPXQwMGsxIS07JyxlMjg+aT8yPHQ6PCUhITE2aSorN3Q0IC0xKnQhIDNlIzshOiInOjg7PSIgIHQzJy9lIDc9OyIrNHQmIS5lITEhPCcxfXQGIS5lPDo+MGs3NjU+aT83Ojc5aSI2czI7Lj43Ojo1aSQwJ3Q6JjxlPzs8LmsxOzFyIi48cz0hZWskPTByPSMgcxwzJCYsPTNyLSI2JzU8Ki5lMTEmPi4gPXQwJSQmOCdyISorNydyPSMkJ3QmJms8PCFyKCcoPCcmaS0qIXQ0Oy4gfXQ0JSoiKDxmJCYsPTMNLSI2JzU8Ki4aJjo+JiguIAsmIS4aODErOiI/NilyAi4gI3QmIS5lJzEqPWspPDo1aS4rPCE1IWskPTByPSMgcycmKD8sICA7KjhlJD0+JWskPyMzMDhlJD08aSIrcyA6LGsgPTB+aS4zNiYraTgsPTM+LGsxOjk3Zw==
```

If you want to regenerate the challenge (for example to get a different flag), here is the script that builds it:

```python
# gen_challenge.py: build a repeating-key XOR challenge with an embedded flag
import base64, itertools

plaintext = (
"When you XOR a plaintext against a repeating key, the ciphertext still carries the "
"shape of the language underneath it. Every column that lines up with one byte of the "
"key is nothing more than a single byte XOR, and a single byte XOR is trivially broken "
"by trying all two hundred and fifty six possibilities and scoring the result. The only "
"real trick is figuring out how long the key is, and the Hamming distance between blocks "
"hands that to you almost for free. flag{h4mming_distance_unlocks_the_keysize} Keep the "
"text long enough and the statistics will always win in the end, every single time.").encode()

key = b"STRIKE"
ct = bytes(b ^ k for b, k in zip(plaintext, itertools.cycle(key)))
open("challenge.b64", "wb").write(base64.b64encode(ct))
print("Wrote challenge.b64, key length", len(key), ", ct length", len(ct))
```

### Guide

Follow the pipeline in the theory. A suggested order when writing it yourself:

- Hint 1: write and check the `hamming` function first with the test value 37 from the demo. If this function is wrong, the whole lab is wrong.
- Hint 2: write `guess_keysizes` using all blocks (not just the first few) and average the normalized Hamming distance over every pair. Print the top few candidates and notice that they are multiples of each other.
- Hint 3: take the smallest keysize in the top group (not always top 1). Split columns with `ct[j::ks]` and break each one as single-byte, like Lesson 3.1, with the frequency scorer.
- Hint 4: if the plaintext comes out nearly right but with a repeated structure (for example the key comes out as `STRIKESTRIKE`), reduce the key to its smallest period and decrypt again.

### Full solver

Save it as `solve_xor.py` and run `python3 solve_xor.py challenge.b64`.

```python
#!/usr/bin/env python3
# solve_xor.py: break repeating-key XOR end to end (like Cryptopals set 1, challenge 6)
import base64
import itertools
import sys

# Frequencies of letters + space in English (ratios). Used to score "looks like English".
ENG_FREQ = {
    'a': .0817, 'b': .0150, 'c': .0278, 'd': .0425, 'e': .1270, 'f': .0223,
    'g': .0202, 'h': .0609, 'i': .0697, 'j': .0015, 'k': .0077, 'l': .0403,
    'm': .0241, 'n': .0675, 'o': .0751, 'p': .0193, 'q': .0010, 'r': .0599,
    's': .0633, 't': .0906, 'u': .0276, 'v': .0098, 'w': .0236, 'x': .0015,
    'y': .0197, 'z': .0007, ' ': .1800,
}

# Lookup table of scores for each byte (0..255) for fast scoring.
_LUT = [0.0] * 256
for _b in range(256):
    _ch = chr(_b).lower()
    if _ch in ENG_FREQ:
        _LUT[_b] = ENG_FREQ[_ch]
    elif not (0x20 <= _b < 0x7f):
        _LUT[_b] = -0.05            # control byte: heavy penalty

def score_english(data):
    return sum(_LUT[b] for b in data)

def hamming(a, b):
    """Number of differing bits between two byte strings of equal length."""
    return sum(bin(x ^ y).count("1") for x, y in zip(a, b))

def xor_repeat(data, key):
    return bytes(b ^ k for b, k in zip(data, itertools.cycle(key)))

def guess_keysizes(ct, lo=2, hi=40):
    """Guess the key length with normalized Hamming distance, sorted ascending."""
    scores = []
    for ks in range(lo, hi + 1):
        nblocks = len(ct) // ks
        if nblocks < 2:
            continue
        chunks = [ct[i*ks:(i+1)*ks] for i in range(nblocks)]   # use ALL the blocks
        dists = [hamming(a, b) / ks for a, b in itertools.combinations(chunks, 2)]
        scores.append((sum(dists) / len(dists), ks))
    scores.sort()
    return scores

def break_single_byte(column):
    """The key byte that makes this column look most like English (brute force 256)."""
    return max(range(256), key=lambda k: score_english(bytes(b ^ k for b in column)))

def minimal_period(key):
    """Reduce the key to its smallest period: b'STRIKESTRIKE' -> b'STRIKE'."""
    for p in range(1, len(key) + 1):
        if len(key) % p == 0 and key == key[:p] * (len(key) // p):
            return key[:p]
    return key

def solve(ct, try_top=3):
    # The best-scoring key length candidates are almost always MULTIPLES of the true length.
    # Take the SMALLEST one in the top group: the most bytes per column, the most stable single-byte step.
    candidates = [ks for _, ks in guess_keysizes(ct)[:try_top]]
    ks = min(candidates)
    columns = [ct[j::ks] for j in range(ks)]      # column j: the bytes XORed with the same key byte
    key = bytes(break_single_byte(col) for col in columns)
    key = minimal_period(key)                     # if we picked a multiple, this folds it back to the original key
    return key, xor_repeat(ct, key)

if __name__ == "__main__":
    ct = base64.b64decode(open(sys.argv[1], "rb").read())
    key, pt = solve(ct)
    print("Key length:", len(key))
    print("Key       :", key)
    print("Plaintext :")
    print(pt.decode(errors="replace"))
```

### Expected output

```
Key length: 6
Key       : b'STRIKE'
Plaintext :
When you XOR a plaintext against a repeating key, the ciphertext still carries the shape
of the language underneath it. ... flag{h4mming_distance_unlocks_the_keysize} ...
```

Done when: you print the key `STRIKE` and a readable plaintext containing `flag{h4mming_distance_unlocks_the_keysize}`.

### Next exercise

Do Cryptopals challenge 6 itself. Download the base64 file from cryptopals.com, save it, and run this exact `solve_xor.py`. Their file has line breaks. Strip the newlines before `b64decode`, or use `base64.b64decode(data)`, which already skips whitespace. The real key is a famous lyric, 29 characters long. If you get that sentence you have mastered the whole procedure. Also try challenge 3 (single-byte) and challenge 5 (encrypt) to close the XOR part of set 1.

## Key takeaways

- The pipeline has four steps: guess keysize, split columns, break each column as single-byte, assemble and decrypt.
- The Hamming distance of `this is a test` and `wokka wokka!!!` must be 37, which is the check for your function.
- The best keysize candidate is often a multiple of the true length, so do not trust top 1 blindly.
- Take the smallest keysize in the top group so each column keeps many bytes and the single-byte step stays reliable.
- Reduce the key to its smallest period to get the original key when you picked a multiple.
- The longer the ciphertext, the more reliable every statistical step is.

## Common pitfalls

- Counting Hamming wrongly. You must count differing bits (`bin(x ^ y).count("1")`), not differing bytes. Check with the number 37.
- Missing normalization by forgetting to divide the Hamming distance by the keysize. Without it a large keysize always has a large total, and the comparison is meaningless.
- Using only the first two blocks to measure Hamming. It is very noisy and easily picks the wrong keysize. Use as many block pairs as possible and average.
- Trusting the top 1 keysize completely. It is often a multiple or noise. Look at the first few candidates and prefer the small one.
- Cutting columns as consecutive blocks. It must be `ct[j::ks]` (step ks) to gather exactly the bytes that share one key byte.
- A scorer that is too weak, so the single-byte step picks the wrong byte in a few columns. Give the space a high weight, penalize control bytes, and make sure the columns are long enough.
- A keysize that is too large compared to the ciphertext length leaves only a few bytes per column and the single-byte statistics collapse. You need a longer ciphertext or a smaller keysize.
- Forgetting that `base64.b64decode` needs clean data. The Cryptopals file has line breaks. Read the whole file and decode it (it ignores whitespace), do not decode line by line.

## Further reading

- All of Cryptopals set 1, especially challenges 3, 5, 6: the origin of this lab, and doing all of it gives a firm grip on XOR.
- Lessons 3.1 and 3.2 in this series: the theory behind this script, especially the Hamming and crib dragging parts.
- The `xortool` tool: compare your manual result with an automatic tool and see how it guesses the keysize and the frequent byte.
- CryptoHack, XOR section: more practice with different data shapes and traps.
- Move on to Part 4 (symmetric encryption) to see that modern stream ciphers such as ChaCha20 are still XOR with a keystream, and why every attack here stops working when it is done correctly.
