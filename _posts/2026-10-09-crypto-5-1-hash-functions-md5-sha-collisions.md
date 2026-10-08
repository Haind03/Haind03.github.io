---
title: "Lesson 5.1: Hash Functions, MD5/SHA, and Collisions"
image:
  path: /assets/img/covers/crypto-5-1-hash-functions-md5-sha-collisions.webp
  alt: "Hash Functions, MD5/SHA, and Collisions"
date: 2023-06-22 12:08:00 +0700
categories: ["Cryptography", "Crypto · Hashes and MACs"]
tags: [cryptography, hash, md5, collision]
render_with_liquid: false
---

A hash function turns a message of any length into a short, fixed-size string, a fingerprint of the data. A hash that is usable for crypto has to satisfy a few strict properties, and when one of them breaks, every system built on it breaks too. This lesson covers the four properties, separates the three attacks that are often confused (collision, preimage, second-preimage), reviews which of MD5, SHA-1, SHA-2 and SHA-3 are still usable, and then runs a pair of colliding MD5 inputs so you can see what "broken collision resistance" means in practice.

![Hash functions, MD5/SHA, and collisions](/assets/img/crypto/crypto-5-1-hash-functions-md5-sha-collisions.svg)
_Preimage, second-preimage and collision attacks on an n-bit hash, and where each common hash stands._

Part 5 (Hashes, MACs and passwords) | Time: about 35 minutes | Difficulty: medium

**Prerequisites:** Lesson 1.5 (birthday paradox) helps explain why collisions are cheaper than you expect, but it is optional. Knowing hex and bytes is enough.

**Tools:** Python 3 (only `hashlib` from the standard library).

## Goals

After this lesson you can state the four properties of a cryptographic hash, tell collision, preimage and second-preimage apart, say how broken MD5 and SHA-1 are and where SHA-2 and SHA-3 stand, run code that shows two different inputs with the same MD5, and spot a challenge or system that relies on a broken hash property.

## 1. Theory

### What a hash does

A hash function `H` takes an input of any length and returns an output of fixed length called a digest. MD5 gives 128 bits, SHA-1 gives 160 bits, SHA-256 gives 256 bits. The same input always gives the same digest. Changing one bit of the input changes almost the whole digest, which is called the avalanche effect.

A hash is different from encryption. Encryption has a key and can be reversed. A hash is one way, has no key, and cannot really be "decrypted" because it compresses information, since infinitely many inputs map into a finite digest space. Hashes are used to check integrity (was the file modified), to store password fingerprints, and as the base for digital signatures and MACs.

### The four properties of a cryptographic hash

1. Deterministic: the same input gives the same output, always, on every machine.
2. Preimage resistance: given a digest `h`, you cannot find an input `m` with `H(m) = h`. This is the one-way property.
3. Second-preimage resistance: given a specific input `m1`, you cannot find a different `m2` with `H(m1) = H(m2)`.
4. Collision resistance: you cannot find any pair of different `m1`, `m2` with `H(m1) = H(m2)`. The attacker chooses both, so this is the hardest requirement to guarantee.

### Three attacks that are easy to confuse

The three names sound alike but differ a lot in difficulty:

- Preimage attack: you know `h` and look for any `m` with `H(m) = h`. For an `n`-bit hash the theoretical cost is `2^n`.
- Second-preimage attack: you know `m1` and look for `m2 != m1` with the same digest. Also about `2^n`.
- Collision attack: you choose both `m1` and `m2` freely. Because of the birthday paradox (in a group of only 23 people, two share a birthday with good probability), the cost drops to about `2^(n/2)`.

The gap between `2^(n/2)` and `2^n` is why collision resistance always breaks first. For 128-bit MD5 a birthday collision costs `2^64`, which has been within reach for a long time, and differential cryptanalysis makes it much cheaper. The point to remember is that MD5 and SHA-1 are broken for collisions, but nobody has published a practical preimage attack on them. So "give me the password that matches this MD5 hash" is still a hard preimage problem, while "create two different files with the same MD5" takes seconds.

### Which hash functions to use

- MD5 (128 bit): broken for collisions. Wang et al. published a collision in 2004, and today a laptop makes one almost instantly. Never use it for signatures, certificates, or tamper protection. It is only acceptable as a checksum against random errors, not against an attacker.
- SHA-1 (160 bit): also broken for collisions. In 2017 Google and CWI published SHATTERED, two different PDF files with the same SHA-1. In 2019 a chosen-prefix collision appeared (a collision for two prefixes the attacker picks in advance, which is stronger and far more dangerous), enough to forge certificates and attack protocols. Stop using it.
- SHA-2 (SHA-224/256/384/512): still safe, no practical collision known. A reasonable default. It has its own weakness, length extension, covered in Lesson 5.2.
- SHA-3 (Keccak): a standard since 2015, built on a sponge construction that differs from SHA-2, so it is immune to length extension. Use it for diversity or when you want sponge properties.

### Why collisions are a disaster

If I can build two files with the same hash, I can ask you to sign the harmless one and then swap in the malicious one. The signature still matches because it signs the hash. Software distribution, TLS certificates, blockchains and digital contracts all assume that the same hash means the same content. That assumption is collision resistance. When it breaks, the trust breaks.

## 2. Demo

The script below computes several hashes of a message, shows the avalanche effect after changing one character, and then loads the classic MD5 collision pair by Wang et al. (2004) to show that two different byte strings have the same MD5.

```python
# hash_demo.py: compute hashes and demonstrate an MD5 collision
import hashlib

msg = b"attack at dawn"
print("input:", msg)
print("md5    :", hashlib.md5(msg).hexdigest())
print("sha1   :", hashlib.sha1(msg).hexdigest())
print("sha256 :", hashlib.sha256(msg).hexdigest())
print("sha3_256:", hashlib.sha3_256(msg).hexdigest())

# change 1 bit: avalanche effect
msg2 = b"attack at dawm"   # change n -> m at the end
print()
print("change 1 character, sha256 changes completely:")
print("  ", hashlib.sha256(msg).hexdigest())
print("  ", hashlib.sha256(msg2).hexdigest())

# classic MD5 collision pair (Wang et al. 2004): two different 128-byte blocks, same MD5
m1 = bytes.fromhex(
"d131dd02c5e6eec4693d9a0698aff95c2fcab58712467eab4004583eb8fb7f89"
"55ad340609f4b30283e488832571415a085125e8f7cdc99fd91dbdf280373c5b"
"d8823e3156348f5bae6dacd436c919c6dd53e2b487da03fd02396306d248cda0"
"e99f33420f577ee8ce54b67080a80d1ec69821bcb6a8839396f9652b6ff72a70")
m2 = bytes.fromhex(
"d131dd02c5e6eec4693d9a0698aff95c2fcab50712467eab4004583eb8fb7f89"
"55ad340609f4b30283e4888325f1415a085125e8f7cdc99fd91dbd7280373c5b"
"d8823e3156348f5bae6dacd436c919c6dd53e23487da03fd02396306d248cda0"
"e99f33420f577ee8ce54b67080280d1ec69821bcb6a8839396f965ab6ff72a70")
print()
print("are the two messages DIFFERENT?", m1 != m2)
print("differing byte positions:", [i for i in range(len(m1)) if m1[i] != m2[i]])
print("md5(m1):", hashlib.md5(m1).hexdigest())
print("md5(m2):", hashlib.md5(m2).hexdigest())
print("same MD5?   ", hashlib.md5(m1).hexdigest() == hashlib.md5(m2).hexdigest())
print("sha256 still different?", hashlib.sha256(m1).hexdigest() != hashlib.sha256(m2).hexdigest())
```

Running it gives this output:

```
input: b'attack at dawn'
md5    : fa961e42a869e6e045cae5f9fd20cadc
sha1   : e91fbe6fe58c9c0a57b26f1b82577769afdaf960
sha256 : d502810c71aeb17e5ea1cbf930b46b87bb645a75df45f500230d061992aeb90a
sha3_256: c1de7b316cafd5e88072c73ce2dc7541649f0dc2d87e5d2374adeba52654d444

change 1 character, sha256 changes completely:
   d502810c71aeb17e5ea1cbf930b46b87bb645a75df45f500230d061992aeb90a
   0067b7c9fb0c725b602d7a7ca582fb11daee7ff83e70faff5f0c93ff9f174210

are the two messages DIFFERENT? True
differing byte positions: [19, 45, 59, 83, 109, 123]
md5(m1): 79054025255fb1a26e4bc422aef54eb4
md5(m2): 79054025255fb1a26e4bc422aef54eb4
same MD5?    True
sha256 still different? True
```

Reading the output: `m1` and `m2` differ at six byte positions (19, 45, 59, 83, 109, 123), yet their MD5 values are both `79054025255fb1a26e4bc422aef54eb4`, equal character for character. This is not luck. The pair was built with differential cryptanalysis and published in 2004. The SHA-256 values of the two strings are still different, so SHA-256 is not affected by this attack. The first part of the output also shows the avalanche effect: changing `dawn` to `dawm` (one bit) changes almost the whole SHA-256 digest.

An important note is that this byte pair is a collision only for demonstration, and its content has no meaning. The dangerous version is the chosen-prefix collision, which lets an attacker build two meaningful files (a harmless PDF and a malicious PDF) with the same hash. That is what SHATTERED did for SHA-1.

## 3. Lab

- Task: You are given two binary files `good.bin` and `evil.bin` that differ but have the same MD5. A function `register(file)` accepts a file if its MD5 matches an allowlist that contains the MD5 of `good.bin`. Submit `evil.bin` and show that it passes the check even though its content is different.
- Files: build them yourself from the collision pair in the demo. Write `m1` to `good.bin`, `m2` to `evil.bin`, then write a `register` function that uses an MD5 allowlist.
- Hints, step by step:
  1. Confirm the two files differ in content but `hashlib.md5` gives the same digest.
  2. Write `register` so that it checks the MD5 against the allowlist. Submit `good.bin` and see it pass, which is correct behavior.
  3. Submit `evil.bin` and it also passes, although the content differs. That is the vulnerability. Change `register` to SHA-256 and watch `evil.bin` get blocked.
- Done when: you can explain why `evil.bin` passes an MD5 allowlist but is blocked with SHA-256, and why this breaks every system that trusts "same hash means same file".

## 4. Key takeaways

- Four properties: deterministic, preimage resistant, second-preimage resistant, collision resistant.
- Collisions are cheaper than preimages because of the birthday paradox: `2^(n/2)` versus `2^n`.
- MD5 and SHA-1 are broken for collisions. MD5 since 2004, SHA-1 with SHATTERED in 2017 and the chosen-prefix attack in 2019.
- Preimages of MD5 and SHA-1 are still not practically broken, so do not confuse them with collisions.
- SHA-2 is still safe but has length extension (Lesson 5.2). SHA-3 uses a sponge and is immune.
- With a broken hash, the same hash no longer means the same content. This is the root of forgery attacks.

## 5. Common pitfalls

- Confusing collision with preimage. After hearing "MD5 is broken" it is easy to think you can recover a password from an MD5 hash with math. You cannot. Recovering a password from a hash is a preimage problem (still hard in theory). People crack hashes because passwords are weak and the hash is fast, which is the topic of Lesson 5.4.
- Treating a hash as encryption. A hash has no key and cannot be reversed. "Decrypting MD5" is a wrong phrase. It really means a table lookup or brute-forcing the preimage.
- Using MD5 or SHA-1 for tamper protection because they are still seen everywhere. Common does not mean safe. Against an attacker, use SHA-256 at minimum.
- Assuming a longer hash is always proportionally safer. Length matters, but the design decides: SHA-1 at 160 bits was broken in theory before some shorter hashes because its structure has weaknesses.
- Forgetting that truncating a good hash lowers its strength exponentially: cut SHA-256 to 64 bits and a collision costs only `2^32`, which is found in moments.

## 6. Further reading

- Wang and Yu, "How to Break MD5 and Other Hash Functions", 2005, the work that started practical MD5 collisions.
- SHATTERED (shattered.io), Stevens et al. 2017, the first SHA-1 collision with two PDF files.
- "SHA-1 is a Shambles", Leurent and Peyrin 2020, a low-cost chosen-prefix collision for SHA-1.
- NIST FIPS 180-4 (SHA-2) and FIPS 202 (SHA-3) for the original specifications.
- CryptoHack, Hashes section, the introductory MD5/SHA challenges.
