---
title: "Lesson 9.1: PRNG vs CSPRNG and Mersenne Twister"
image:
  path: /assets/img/covers/crypto-9-1-prng-csprng-mersenne-twister.webp
  alt: "PRNG vs CSPRNG and Mersenne Twister"
date: 2023-10-28 20:30:00 +0700
categories: ["Cryptography", "Crypto · Randomness"]
tags: [cryptography, prng, csprng, mersenne-twister]
render_with_liquid: false
---

Many crypto vulnerabilities are not in the encryption algorithm. They are in the way random numbers are generated. Password reset tokens, session ids, session keys and nonces all need randomness that nobody can predict. If a developer uses Python's `random` or C's `rand()` by mistake, the "random" value is really a deterministic sequence that an attacker can predict. This lesson separates PRNG from CSPRNG, explains the seed, covers what Mersenne Twister (MT19937) is and why it is unsafe for security, and runs a demo that predicts a token when the seed can be guessed.

![PRNG with a small seed vs CSPRNG](/assets/img/crypto/crypto-9-1-prng-csprng-mersenne-twister.svg)
_A PRNG seeded from a small space can be rebuilt from the seed. A CSPRNG draws entropy from the OS and has no small seed._

Part 9 (Randomness) | Time: about 30 minutes | Difficulty: medium

**Prerequisites:** None required. Basic Python is enough. Lesson 1.5 (entropy) helps.

**Tools:** Python 3 (`random`, `secrets`, `time` from the standard library).

## Goals

By the end of this lesson you can tell PRNG and CSPRNG apart and say which extra properties a CSPRNG needs. You understand what a seed is and why the same seed gives the same sequence. You know that Python's `random` uses MT19937 and why that is unsafe for crypto. You can run the demo showing that a known seed is predictable, and that a small seed space can be brute-forced. You can spot a system that uses a PRNG in the wrong place and replace it with a CSPRNG.

## 1. Theory

### PRNG: pseudo-random, actually deterministic

A PRNG (pseudo-random number generator) is a deterministic algorithm. It keeps an internal state. Each call changes the state with a fixed formula and returns a number. It is "pseudo" random because the output looks even and shows no obvious pattern, but it is fully deterministic, so the same initial state always gives the same sequence.

The initial state comes from a seed, a value we feed in to initialize the generator. With the same seed, a PRNG produces exactly the same sequence. This is a feature when you want reproducible results for debugging and tests. It is also fatal for security, because anyone who knows the seed knows the whole sequence, past and future.

### CSPRNG: extra conditions against prediction

A CSPRNG (cryptographically secure PRNG) is a PRNG that also meets two requirements:

- Next-bit unpredictability: no matter how much earlier output you have seen, no efficient method guesses the next bit better than a coin flip.
- State compromise resistance: even if the state leaks at one point in time, past output cannot be recovered.

An ordinary PRNG such as MT19937 fails the first condition. With enough output you can rebuild the state and predict everything that follows (Lesson 9.2 does exactly this). A CSPRNG does not. In practice a CSPRNG takes its entropy (real randomness) from the operating system (`/dev/urandom`, `getrandom`, `CryptGenRandom`) and has no small guessable seed.

### MT19937, the generator behind random()

Mersenne Twister is the default PRNG in many places: Python's `random` module, PHP's `mt_rand`, and several C++ libraries. The common version is MT19937, named after its huge period `2^19937 - 1`. Its state is 624 words of 32 bits. On each call it takes one state word, passes it through a reversible transform called temper, and returns the result. When all 624 words are used, it "twists" to refresh the whole array.

MT19937 is very good for simulation, games and statistics: it has a good distribution, a long period and it is fast. It is not safe for cryptography, for two reasons:

1. The temper step is reversible. Seeing 624 consecutive outputs lets you recover the full state and predict every future number.
2. The seed is often small or guessable. If the code seeds with the time (`random.seed(time.time())`), the seed space is only a few billion values around the current time, which can be brute-forced almost instantly.

### When this is dangerous

Using an ordinary PRNG for any of the following is a vulnerability: password reset tokens, session ids, OTPs, keys, IVs, nonces, one-time salts, invite codes, transaction numbers, or anything an attacker must not guess. Signs in code or in a challenge: `random.`, `rand()`, `mt_rand` or `Math.random()` used to produce a security value, or a seed that is the time, a PID or a constant.

The fix is always a CSPRNG. In Python use `secrets` (tokens, numbers, safe choices) or `os.urandom`. They take entropy from the operating system and expose no small seed.

## 2. Demo

The script below shows three things. The same seed gives the same sequence (a PRNG is deterministic). Knowing the seed means being able to predict. When a server seeds a PRNG with the time, we can brute-force the seed and predict the next token. At the end is the correct approach with `secrets`.

```python
# prng_predict.py: knowing the seed means being able to predict, and why random() is not safe
import random, secrets, time

# 1. same seed -> same sequence. A PRNG is deterministic, not truly "random"
random.seed(1337)
a = [random.randint(0, 10**9) for _ in range(3)]
random.seed(1337)
b = [random.randint(0, 10**9) for _ in range(3)]
print("seed 1337, run 1:", a)
print("seed 1337, run 2:", b)
print("identical? ", a == b)

# 2. the server generates tokens with a time-based seed -> small seed space, brute-forceable
def make_token(seed):
    r = random.Random(seed)
    return r.getrandbits(64)

now = int(time.time())
secret_seed = now - 4321          # the server seeds with a recent timestamp
token = make_token(secret_seed)
print()
print("token leaked by server:", hex(token))

found = None
for guess in range(now - 20000, now + 1):   # scan a reasonable time window
    if make_token(guess) == token:
        found = guess
        break
print("brute-forced seed:", found, "| correct?", found == secret_seed)

# with the seed -> clone the PRNG -> predict the NEXT token the server will generate
r = random.Random(found)
_ = r.getrandbits(64)                         # token already leaked
print("predicted next token:", hex(r.getrandbits(64)))

# 3. done right: use a CSPRNG (secrets / os.urandom), there is no guessable seed
print()
print("secrets.token_hex (CSPRNG):", secrets.token_hex(16))
```

Running it gives this output (the time-based values change on every run, but the conclusion always holds):

```
seed 1337, run 1: [663307072, 993786078, 572589545]
seed 1337, run 2: [663307072, 993786078, 572589545]
identical?  True

token leaked by server: 0x9bbaebe1043b0660
brute-forced seed: 1791395052 | correct? True
predicted next token: 0xfe9e825aa98b448c

secrets.token_hex (CSPRNG): 5eed081962d60241072fca36255134b9
```

Reading the output: two runs with seed `1337` give identical sequences, which shows that a PRNG is deterministic and the "randomness" is only on the surface. The second part simulates a server that seeded with the time. We scan a window of twenty thousand seconds, find the exact seed `1791395052`, clone the PRNG and predict the next token the server will generate. None of this breaks an algorithm. It works only because the seed lies in a small space. The last line uses `secrets`, which has no seed to guess, so this attack does not apply.

## 3. Lab

- Task: A web service issues password reset tokens with `random.seed(int(time.time())); token = random.getrandbits(128)` as soon as it receives a request. You know roughly when you sent your request (from the `Date` header of the response). Predict the token of another request sent at the same time.
- Files: build a small server that seeds with the time and issues tokens, then write a client that brute-forces the seed around the response time.
- Hints, step by step:
  1. Take the timestamp from the server response (the `Date` header). It is the center of the brute-force window.
  2. For each candidate seed in a window of a few seconds, rebuild the token and compare it with the token you observed for your own request, to check the method.
  3. Once a known token matches, use the same seed to predict the token of a victim whose request was sent at about the same time.
  4. If the token is longer than 64 bits, remember the order in which `getrandbits` generates bits so that the match is exact.
- Done when: you predict a token you never received directly, using only the timing.

## 4. Key takeaways

- A PRNG is deterministic: the same seed gives the same sequence, and nothing is truly random.
- A CSPRNG adds next-bit unpredictability and state compromise resistance, and takes entropy from the operating system.
- MT19937 (behind Python's `random`) is good for simulation and not safe for crypto.
- MT19937 has two weak points: a reversible temper (Lesson 9.2) and small guessable seeds.
- Using a PRNG for tokens, keys, nonces or sessions is a vulnerability. Use `secrets` or `os.urandom`.
- Warning signs: `random.`, `rand()`, `mt_rand`, `Math.random()` producing security values, or a seed that is the time or a PID.

## 5. Common pitfalls

- Thinking `random.random()` is random enough because the numbers look chaotic. Chaotic to a human eye does not mean unpredictable to an attacker who knows the algorithm.
- Seeding a CSPRNG with the time to make it reproducible. Reproducibility is the weakness. If you need it for tests, keep it separate and do not use it for security.
- Calling `random.seed()` once and assuming that is safe. The problem is not how often you seed. MT19937 itself is predictable once enough output is visible.
- Mixing up `secrets` and `random`. `random.randint` and `secrets.randbelow` look similar, but one is predictable and the other is not. Pick by purpose.
- Believing JavaScript's `Math.random()` is safer. It is also an ordinary PRNG (usually xorshift128+) and is not safe for crypto. Use `crypto.getRandomValues`.
- Using a CSPRNG and then cutting its entropy, for example taking a token and keeping only a few characters. Keep the full length.

## 6. Further reading

- The Python `secrets` module documentation, which states when to use it instead of `random`.
- The original Matsumoto and Nishimura paper on Mersenne Twister (1998), if you want to understand the design.
- OWASP, "Insecure Randomness", which lists mistakes of using a PRNG in the wrong place in real applications.
- Lesson 9.2 (recovering MT19937 and breaking LCG), to see how far "predictable" really goes.
