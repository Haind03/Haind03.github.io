---
title: "Lesson 5.3: MAC, HMAC, and Timing Attacks on Tag Comparison"
image:
  path: /assets/img/covers/crypto-5-3-mac-hmac-timing-attacks-tag-comparison.webp
  alt: "MAC, HMAC, and Timing Attacks on Tag Comparison"
date: 2026-10-09 13:15:00 +0700
categories: ["Cryptography", "Crypto · Hashes and MACs"]
tags: [cryptography, hmac, mac, timing-attack]
render_with_liquid: false
---

A hash tells us whether data was modified, but not who produced it, because anyone can compute a hash. To both detect tampering and prove that someone holding a key produced the data, we need a MAC (message authentication code). HMAC is the most common correct way to build a MAC. But building the MAC correctly is not enough. If the server checks the tag with an ordinary comparison that stops at the first wrong byte, it leaks timing, and an attacker can recover the tag one byte at a time without knowing the key. This lesson explains how a MAC differs from a hash, how HMAC is built, and then runs a working timing attack that recovers a tag just by measuring time.

![MAC, HMAC, and timing attacks on tag comparison](/assets/img/crypto/crypto-5-3-mac-hmac-timing-attacks-tag-comparison.svg)
_An early-exit comparison takes longer for each extra matching byte, which lets the attacker lock in the tag byte by byte._

Part 5 (Hashes, MACs and passwords) | Time: about 40 minutes | Difficulty: medium

**Prerequisites:** Lesson 5.1 (hashes) and Lesson 5.2 (why `H(secret || msg)` is wrong, so you can see that HMAC fixes it).

**Tools:** Python 3 (`hmac`, `hashlib`, `time` from the standard library).

## Goals

After this lesson you can tell hash, MAC and digital signature apart (which has a key, symmetric or asymmetric), draw the HMAC structure and say why it blocks length extension, explain what a timing side-channel is and why an early-exit comparison leaks information, run a timing attack that recovers a tag byte by byte without the key, and use constant-time comparison as the defense and recognize this bug.

## 1. Theory

### Hash, MAC, signature: three different things

- Hash: `H(msg)`, no key. Anyone can compute it, so it only protects against random errors, not against an active attacker (an attacker modifies msg and recomputes the hash).
- MAC: `MAC(k, msg)`, with a symmetric key `k`. Only someone who knows `k` can create and verify the tag. The sender and receiver (both know `k`) use it to be sure the message was not changed and really came from a key holder.
- Digital signature: uses asymmetric keys. The signer uses the private key and anyone verifies with the public key. Unlike a MAC it gives non-repudiation: only the owner of the private key could sign, so the signer cannot deny it.

This lesson focuses on MACs.

### How HMAC is built, and why it is correct

In Lesson 5.2 we saw that the homemade MAC `H(secret || msg)` is vulnerable to length extension. HMAC fixes exactly that by hashing twice:

```
HMAC(k, m) = H( (k xor opad) || H( (k xor ipad) || m ) )
```

Here `ipad` is the byte `0x36` repeated and `opad` is the byte `0x5c` repeated, each as long as the hash block. The inner hash produces a digest, and the outer hash wraps that digest. What the attacker sees (the tag) is the output of the outer hash, not a state that matches `k || m`, so there is no state to continue from and length extension is off. HMAC stays secure even when the underlying hash has some weaknesses, so HMAC-SHA256 is widely trusted.

### Side-channel: information leaking outside the main channel

A cryptosystem can be correct mathematically and still leak secrets through a side-channel such as running time, power use, sound, different error messages. A timing attack uses the time channel. The classic scenario is a server comparing the tag a user sends with the correct tag.

Most languages compare strings or bytes by walking through each element and returning `False` at the first element that differs. This is good for performance and bad for security, because the comparison time grows with the number of leading bytes that match. If my guess has the first byte right, the comparison runs one step longer before stopping, slightly slower than a guess that is wrong at the first byte.

### Recovering the tag byte by byte with a clock

Suppose the tag is `L` bytes long. I fix the bytes I already know and let the byte under test run through 256 values. For each value I send a forged tag and measure how long the server takes to answer. The value that makes the server slowest is the one that matches one more byte, because it pushes the stopping point of the comparison loop one step later. I lock that byte and move to the next one. Going left to right, I rebuild the whole tag without ever knowing the key.

Cost: at most `256 * L` measurements, multiplied by the number of repeats used to filter noise. This is much cheaper than brute-forcing the whole tag (`256^L`). The time difference of one byte must be larger than the measurement noise, so in practice people measure each candidate thousands of times and use statistics (the median, or the minimum value because noise pushes times up).

### Defense: constant-time comparison

The simple fix is to compare the two tags completely, in time that does not depend on the position of the wrong byte. In Python that is `hmac.compare_digest`. It goes through every byte and combines the result by OR-ing the differences, without stopping early. Whether the first byte or only the last byte is wrong, the time is the same, so there is no signal left to exploit.

## 2. Demo

The script below builds a tag comparison oracle that is NOT constant time (it stops early at a wrong byte), then runs a timing attack that recovers the first four bytes of an HMAC-SHA256 tag without using the key. To keep the signal stable on a desktop machine, the per-byte processing cost is simulated with a busy-wait. The mechanism is the same as in a real system, only the noise differs. At the end the script also measures `compare_digest` to show that the correct approach does not leak time.

```python
# timing_mac.py: timing attack recover a MAC tag via a non-constant-time comparison
import hmac, hashlib, os, time

KEY = os.urandom(16)                       # the attacker does NOT know this
WORK_US = 280.0                            # each matching byte costs ~280us (simulated with a spin loop)
TAGLEN = 4                                 # recover the first 4 bytes to keep the demo fast

def real_tag(msg):
    return hmac.new(KEY, msg, hashlib.sha256).digest()

def _spin(us):
    end = time.perf_counter() + us/1e6
    while time.perf_counter() < end:
        pass

# server: compares byte by byte, STOPS EARLY on a wrong byte -> timing leak
def insecure_verify(msg, guess):
    correct = real_tag(msg)
    for i in range(min(len(guess), len(correct))):
        if guess[i] != correct[i]:
            return False
        _spin(WORK_US)                      # each matching byte adds time
    return guess == correct

# attacker: measures time, takes the min over many runs to cut noise
def time_call(msg, guess, trials=8):
    best = float("inf")
    for _ in range(trials):
        t0 = time.perf_counter()
        insecure_verify(msg, guess)
        dt = time.perf_counter() - t0
        best = min(best, dt)
    return best

def attack(msg, taglen):
    rec = bytearray()
    for _ in range(taglen):
        best_t, best_b = -1.0, 0
        for b in range(256):
            g = bytes(rec) + bytes([b]) + b"\x00"*(taglen - len(rec) - 1)
            t = time_call(msg, g)
            if t > best_t:                  # correct byte = slowest (one more byte matches)
                best_t, best_b = t, b
        rec.append(best_b)
    return bytes(rec)

msg = b"amount=100&to=alice"
t0 = time.time()
rec = attack(msg, TAGLEN)
print("recovered:", rec.hex())
print("tag that :", real_tag(msg)[:TAGLEN].hex())
print("match?   :", rec == real_tag(msg)[:TAGLEN], "(%.1fs)" % (time.time()-t0))

# constant-time comparison leaks nothing
a = real_tag(msg)
b = bytearray(a); b[-1] ^= 1               # wrong last byte
c = b"\x00"*len(a)                         # wrong first byte
def ns(x, y, n=200000):
    best = float("inf")
    for _ in range(n):
        t0 = time.perf_counter(); hmac.compare_digest(x, y); best = min(best, time.perf_counter()-t0)
    return best*1e9
print("compare_digest wrong last byte: %.0f ns" % ns(a, bytes(b)))
print("compare_digest wrong first byte : %.0f ns" % ns(a, c))
```

Running it gives this output (absolute times depend on the machine, but the recovered value always matches):

```
recovered: 2ae7ca80
tag that : 2ae7ca80
match?   : True (3.7s)
compare_digest wrong last byte: 61 ns
compare_digest wrong first byte : 60 ns
```

Reading the output, the `attack` function never touches `KEY`. It only calls `insecure_verify` and times it. It recovers the first four bytes `2ae7ca80` correctly. To get all 32 bytes, increase `TAGLEN`, at the cost of more time. The last two lines show that `compare_digest` takes 60 and 61 ns whether the wrong byte is the last one or the first one. The difference is within error, so there is no longer a signal that grows with the number of matching bytes, and the attack does not work.

## 3. Lab

- Task: An endpoint `POST /verify` takes `msg` and `tag`, returns `200` if the tag is correct and `403` if not, and it compares the tag with an early-exit loop. Recover a valid tag for a `msg` of your choice (for example `role=admin`) only by measuring response time, without the key.
- Files: write a self-contained `solve.py` with the oracle, the timing function, and the recovery loop. A good run recovers the first six bytes.
- Hints, step by step:
  1. Write a `measure(msg, tag)` function that calls the oracle many times and returns a representative time. Use the minimum over many runs to reduce noise.
  2. Probe the first byte by running byte 0 from 0 to 255, keep the rest at 0, and pick the value with the largest time.
  3. Lock the byte you found and probe the next one. Repeat for the whole tag length.
  4. Over a network the noise is much larger, so increase the number of measurements per candidate, consider running in parallel, and filter outliers.
- Done when: you recover a tag long enough for the server to accept it, or you show that you recover the full tag correctly in a test environment.

## 4. Key takeaways

- A hash has no key, a MAC has a symmetric key, and a signature uses asymmetric keys and gives non-repudiation.
- HMAC hashes in two layers with `ipad`/`opad`, blocks length extension, and is the standard way to make a MAC from a hash.
- An early-exit tag comparison leaks time proportional to the number of matching leading bytes.
- A timing attack recovers the tag byte by byte: pick the byte that makes the response slowest. The cost is `256 * L` instead of `256^L`.
- In practice you must measure many times and filter noise, using statistics (minimum or median).
- Defense: constant-time comparison (`hmac.compare_digest`), and never `==` on a tag or password.

## 5. Common pitfalls

- Using `==` or `!=` to compare tags, tokens, or passwords. This is the bug itself. Always use a constant-time comparison.
- Believing timing attacks are only theory. On a LAN or on the same virtual host, microsecond differences can still be measured if you repeat enough. Several real vulnerabilities (Lucky Thirteen, some JWT libraries) are timing issues.
- Measuring once and trusting it. Operating system noise is larger than the signal, so repeat and use statistics. The mean is easily pulled by outliers, so the minimum or the median is steadier.
- Confusing a MAC with encryption. A MAC gives integrity and authentication and does not hide the content. To hide and authenticate, use AEAD (Lesson 4.2) or encrypt-then-MAC.
- Building a MAC as `H(secret || msg)` because it is quick. It is vulnerable to length extension (Lesson 5.2). Use HMAC.
- Using a constant-time comparison but still returning early when the lengths differ. Length checks should also avoid leaking, and the best option is to compare fixed-length values.

## 6. Further reading

- RFC 2104, "HMAC: Keyed-Hashing for Message Authentication", the original specification.
- The Python documentation for `hmac.compare_digest`, which explains why and when to use it.
- Cryptopals Set 4, Challenges 31 and 32 (implement and break HMAC with a timing leak), exercises on exactly this topic.
- Lucky Thirteen (AlFardan and Paterson, 2013), a real timing attack on TLS, worth reading to see the scale.

## Lab

<div class="lab-box">
<div class="lab-head"><b>LAB 5.3</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/5.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/5.3/solve.py" download><i class="fa-solid fa-file-code"></i>solve.py</a>
</div>
</div>
