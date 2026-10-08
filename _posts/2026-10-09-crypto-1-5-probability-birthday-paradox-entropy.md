---
title: "Lesson 1.5: Probability, the Birthday Paradox and Entropy"
image:
  path: /assets/img/covers/crypto-1-5-probability-birthday-paradox-entropy.webp
  alt: "Probability, the Birthday Paradox and Entropy"
date: 2023-03-03 06:30:00 +0700
categories: ["Cryptography", "Crypto · Math Foundations"]
tags: [cryptography, birthday-attack, entropy, hash]
render_with_liquid: false
---

This lesson explains why a 128-bit hash only resists collisions at the 64-bit level, and how many bits a key needs to be safe. After it you can estimate the cost of finding a collision, read the real entropy of a random source, and treat a short nonce as a likely collision risk.

![Birthday bound: collision costs 2^(n/2), preimage costs 2^n](/assets/img/crypto/crypto-1-5-probability-birthday-paradox-entropy.svg)
_For an n-bit hash, a collision needs about 2^(n/2) tries while a preimage needs about 2^n._

Part: 1 (Math Foundations) | Time: about 35 minutes | Difficulty: medium

**Prerequisites:** Lesson 0.1 (what cryptography is).

**Tools:** Python 3 (`hashlib`, `random` and `math` are built in).

## Goals

By the end of this lesson you can compute the birthday paradox and explain why it gives collisions around the square root of the space. You can separate collision resistance (2^(n/2)) from preimage resistance (2^n) of a hash. You understand that entropy is measured on the distribution and not on the length, and you know what min-entropy is. You can estimate the key length you need and recognize a short nonce as a warning sign.

## 1. Theory

### Just enough probability

You only need a space of possible outcomes, an event, and its probability. When trials are independent, the probability that several events all happen is the product of their probabilities. One trick used constantly in this lesson is that to compute the probability of "at least one match", you compute the probability of "no match at all" (easier) and subtract it from 1. This is the key to the birthday paradox.

### The birthday paradox

The familiar question is how many people a room needs so that the chance of two sharing a birthday is above 50 percent (ignoring leap years, 365 days). Intuition often guesses around a hundred. The surprising answer is just 23.

Here is the calculation. With k people, the probability that NO ONE shares a birthday is:

```
P(no match) = 365/365 * 364/365 * 363/365 * ... * (365-k+1)/365
```

The first person is free (365/365), the second must avoid 1 taken day (364/365), the third avoids 2 days (363/365), and so on. For k = 23 this product is about 0.493, so P(match) is about 0.507, already above half.

Why is intuition wrong? We compare "23 people against 365 days" and see a small number. But what matters is not the number of people, it is the number of pairs. 23 people form `C(23, 2) = 253` pairs, and each pair is a chance for a match. With 253 chances over 365 days a match is no longer rare.

### In general: collisions near the square root

Replace 365 by any space of N possibilities. The number of samples needed for about a 50 percent chance of a collision (two equal samples) is about `1.1774 * sqrt(N)`, roughly `sqrt(N)`. The approximate formula for k samples is:

```
P(collision) ≈ 1 - e^(-k^2 / (2N))
```

The point to remember is that the cost of finding a collision is proportional to the square root of the space, not to the whole space. Everything about collisions is "half the bits cheaper" than you would expect.

### Consequences for hashes

A hash function with n output bits has `N = 2^n` possible outputs. By the birthday bound, finding two different inputs with the same output (a collision) costs about `sqrt(2^n) = 2^(n/2)` trials, NOT 2^n.

Concrete consequences:

- MD5 outputs 128 bits, so collisions theoretically cost about 2^64 (in practice MD5 is already broken and collisions are much cheaper, almost instant).
- SHA-1 outputs 160 bits, so collisions theoretically cost about 2^80 (and it was really broken in 2017, the SHAttered attack).
- To resist collisions at a safety level of k bits, the hash must be 2k bits long. For 128-bit collision safety you need SHA-256.

Keep these two notions strictly apart, since their costs differ:

- Preimage resistance: given a hash h, find any input that hashes to exactly h. The cost is about `2^n` (you must try nearly the whole space).
- Collision resistance: find any two different inputs with the same hash. The cost is only `2^(n/2)` because of the birthday bound.

The birthday attack is used widely: forging signatures (find two messages with the same hash, one benign and one malicious, then swap them), exploiting collisions in short nonces or tokens, and so on.

### Entropy

Entropy measures the uncertainty of a source, in bits. The Shannon entropy of a distribution with probabilities p_i is:

```
H = - sum (p_i * log2(p_i))
```

Concrete examples start with a fair coin (p = 0.5 per side) has `H = -(0.5*log2(0.5) + 0.5*log2(0.5)) = 1` bit, exactly one bit of uncertainty. A biased coin (p = 0.9 for heads, 0.1 for tails) has `H = -(0.9*log2(0.9) + 0.1*log2(0.1)) ≈ 0.469` bit, clearly less uncertain, because guessing "heads" is right most of the time. A password chosen uniformly from 2^k possibilities has k bits of entropy.

The core point is that entropy is measured on the real distribution of the source, NOT on the string length. "Password123!" looks 12 characters long, but its entropy is very low, because it is on the guess list of every cracking tool and is likely to be tried early. In contrast, 16 bytes from a truly random source carry 128 bits of entropy even though they look shorter.

For crypto there is a stricter measure than Shannon, min-entropy, based on the most predictable outcome:

```
H_inf = - log2(p_max)
```

where p_max is the probability of the most likely value. For example the 0.9/0.1 biased coin has `H_inf = -log2(0.9) ≈ 0.152` bit, much lower than the Shannon value (0.469). Why does crypto prefer min-entropy? An attacker who guesses aims at the easiest value first, so the guessing resistance of the source is decided by that easiest value, not by the average. When you evaluate a key generation source, min-entropy is the number to trust.

### Key length and key space

A k-bit key has `2^k` possible keys, called the key space. Brute force on average has to try half the space, `2^(k-1)`, before it succeeds.

- DES uses 56 bits, so 2^56 keys. Today dedicated hardware can exhaust it in a short time, so DES is dead.
- A 128-bit symmetric key gives 2^128 keys, out of reach of any classical computer in the foreseeable future. This is the standard safety level today.
- 256 bits is the extra margin, even against quantum computers. Grover's algorithm in theory reduces the cost of searching a symmetric key to about the square root, so 256 bits drops to about 2^128 effective, still safe (only a brief mention, details are left to Part 10).

One very easy mistake: for hashes you need double the bits because of the birthday bound (collision 2^(n/2)). For brute-forcing a symmetric key there is NO such halving, because finding the right key is a preimage-style problem (2^k), not a collision. Do not apply the birthday "half rule" to key length.

### Takeaway for CTFs

When a challenge shows a nonce, IV or token of only 32 or 48 bits, the first reflex is that collisions are feasible, since 2^16 or 2^24 operations are within reach. When you see a "random" value produced from a low-entropy source (`time()`, a PID, a guessable seed), the reflex is that it can be brute-forced. This connects to the PRNG part (Part 9), where we exploit exactly these weak randomness sources.

## 2. Demo

The Python below computes the birthday probability, simulates it to check, finds a real collision on a truncated hash, then computes entropy. It uses only the standard library.

```python
# birthday_entropy.py - birthday paradox, collision on a truncated hash, and entropy
import hashlib, os, math, random

def p_birthday(k, N=365):
    # Probability of at least one matching pair, over N possibilities, with k samples.
    p_no = 1.0
    for i in range(k):
        p_no *= (N - i) / N
    return 1 - p_no

def find_collision(bits=32):
    # Find two different inputs giving the same SHA-256 truncated to 'bits' bits.
    seen = {}
    tries = 0
    while True:
        x = os.urandom(8)
        h = hashlib.sha256(x).digest()[: bits // 8]
        tries += 1
        if h in seen and seen[h] != x:
            return seen[h], x, h, tries
        seen[h] = x

def shannon(ps):
    return -sum(p * math.log2(p) for p in ps if p > 0)

def main():
    for k in (23, 50, 70):
        print(f"P(birthday, {k} people) = {p_birthday(k):.4f}")

    # Monte Carlo simulation for k=23 to check the ~0.507 figure
    trials, hit = 20000, 0
    for _ in range(trials):
        days, coll = set(), False
        for _ in range(23):
            d = random.randrange(365)
            if d in days:
                coll = True
                break
            days.add(d)
        hit += coll
    print(f"Simulation k=23: {hit/trials:.3f}")

    # Real collision on a 32-bit hash: expect ~2^16 = 65536 tries
    a, b, h, tries = find_collision(32)
    print(f"32-bit collision after {tries} tries (expected ~2^16 = 65536)")
    print(f"  a = {a.hex()}  b = {b.hex()}  digest = {h.hex()}")

    # Entropy of a biased coin 0.9 / 0.1
    print(f"Shannon H(0.9/0.1) = {shannon([0.9, 0.1]):.3f} bit")
    print(f"Min-entropy        = {-math.log2(0.9):.3f} bit")

if __name__ == "__main__":
    main()
```

Output (the collision count changes on every run because it is random, but it stays around the expectation):

```
P(birthday, 23 people) = 0.5073
P(birthday, 50 people) = 0.9704
P(birthday, 70 people) = 0.9992
Simulation k=23: 0.514
32-bit collision after 86515 tries (expected ~2^16 = 65536)
  a = cf4d9f951487f09d  b = b14c9291358e7050  digest = 46fc78db
Shannon H(0.9/0.1) = 0.469 bit
Min-entropy        = 0.152 bit
```

In the output, the theoretical probability for 23 people is 0.507, and the Monte Carlo simulation gives about 0.51, which matches. The most useful part is that a collision on the 32-bit hash was found after only some tens of thousands of tries, around the birthday expectation `2^(32/2) = 2^16 = 65536`, while a preimage would need about `2^32 ≈ 4 billion` tries, a difference of tens of thousands of times. This is the "half rule" in practice. Finally, the biased coin has Shannon entropy 0.469 bit but min-entropy only 0.152 bit, which shows that min-entropy is stricter and is the number to use when you worry about guessing.

## 3. Lab

- Task: a service generates session tokens of 24 random bits (3 bytes). (a) Estimate how many tokens must be issued before the chance of two users getting the same token exceeds 50 percent. (b) Actually simulate issuing tokens until the first collision, and compare with your estimate. (c) Also compute the entropy of a "password policy" of 8 characters chosen uniformly from a 62-character alphabet (uppercase, lowercase, digits), and conclude whether it is strong or weak compared with a 128-bit key.
- Files: none, build it yourself.
- Hints, in steps:
  - Hint 1: with 24 bits, N = 2^24. The 50 percent collision threshold is about `1.1774 * sqrt(2^24) = 1.1774 * 2^12 ≈ 4823` tokens.
  - Hint 2: simulate by drawing `random.randrange(2**24)` repeatedly, keep a `set`, and stop when a value repeats.
  - Hint 3: the entropy of an 8-character password from 62 characters is `8 * log2(62) ≈ 47.6` bits, far below 128 bits. That means it is not safe for purposes that need key-level strength.
- Done when: the estimate and the simulation agree in order of magnitude, and you compute the password entropy correctly and draw the conclusion.

## 4. Key takeaways

- Collisions appear around `sqrt(N) = 2^(n/2)`, not N. The cost is birthday, not linear.
- An n-bit hash resists collisions only at n/2 bits. For k-bit collision safety you need a 2k-bit hash.
- Preimage is 2^n and collision is 2^(n/2). Do not mix them up.
- Entropy is measured on the distribution, not on string length. Min-entropy is the measure of resistance to guessing.
- A 128-bit symmetric key is safe against classical attackers. Brute force is 2^k, not 2^(k/2).
- Short nonces and tokens (32-bit, 48-bit) invite collisions.

## 5. Common pitfalls

- Thinking a 128-bit hash resists collisions up to 128 bits. It is only 64 bits, because of the birthday bound.
- Confusing collision with preimage. A collision is much cheaper (the square root of the space).
- Judging entropy by the number of characters. A long string can still have low entropy if it is predictable.
- Using Shannon entropy for a skewed distribution and feeling safe. The attacker targets the easiest value, so min-entropy reflects the real guessing resistance.
- Thinking a random 64-bit nonce is "infinite". If you generate enough of them you still hit collisions, and for a stream cipher a repeated nonce is a disaster (Part 4).
- Applying the birthday "half rule" to key brute force. Brute-forcing a symmetric key is 2^k, not reduced to 2^(k/2).

## 6. Further reading

- "Serious Cryptography" (Jean-Philippe Aumasson), the chapters on randomness and on hashes.
- "Handbook of Applied Cryptography", the birthday attack section in the hash functions chapter.
- The SHAttered announcement (shattered.io), the first practical SHA-1 collision, to see theory turn into reality.
- NIST SP 800-90B, on assessing entropy sources, where min-entropy is central.
- CryptoHack (cryptohack.org), the challenges on hashes and randomness.
