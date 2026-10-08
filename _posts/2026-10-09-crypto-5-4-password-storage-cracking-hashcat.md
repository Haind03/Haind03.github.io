---
title: "Lesson 5.4: Password Storage and Cracking with hashcat"
image:
  path: /assets/img/covers/crypto-5-4-password-storage-cracking-hashcat.webp
  alt: "Password Storage and Cracking with hashcat"
date: 2026-10-09 13:20:00 +0700
categories: ["Cryptography", "Crypto · Hashes and MACs"]
tags: [cryptography, passwords, hashcat, bcrypt, argon2]
render_with_liquid: false
---

Storing user passwords is a problem everyone meets and many get wrong. Storing them in plain text is out of the question. Storing `MD5(password)` sounds safer, but it is almost useless against an attacker with a lookup table and a graphics card. This lesson explains why a fast hash is a weakness for password storage, what salt does, how bcrypt, scrypt and argon2 differ from ordinary hashes, and then builds some hashes so you can see the cracking speed yourself, with hashcat and john syntax to try on your own data.

![Password storage and cracking with hashcat](/assets/img/crypto/crypto-5-4-password-storage-cracking-hashcat.svg)
_A salted password goes through a slow KDF. Against a leaked database, MD5 allows millions of guesses per second and bcrypt only a few._

Part 5 (Hashes, MACs and passwords) | Time: about 40 minutes | Difficulty: medium

**Prerequisites:** Lesson 5.1 (hashes and their properties). Know that preimage differs from collision.

**Tools:** Python 3 with `bcrypt` and `argon2-cffi` (`pip install bcrypt argon2-cffi`); hashcat and john (the syntax is described, installing them is not required to read the lesson).

## Goals

After this lesson you can explain why storing `MD5(pw)` or `SHA256(pw)` is not safe enough, say what salt defends against (rainbow tables, duplicate hashes) and what it does not, understand that bcrypt/scrypt/argon2 are deliberately slow and memory hungry to slow the attacker down, create hashes of each kind and measure the speed gap, and write the basic hashcat/john commands: choose the mode, choose the attack mode, use a wordlist.

## 1. Theory

### Why not plain text, and why MD5 does not save us

If the database leaks (which happens often), plain text storage exposes every password. The first improvement is to store a hash: `MD5(pw)` or `SHA256(pw)`. At login, hash what the user typed and compare with the stored hash. If the database leaks, only hashes leak, not passwords. That sounds fine.

The problem is that hashes such as MD5 and SHA-256 are designed to be FAST. A modern GPU computes billions of MD5 per second. An attacker holding a list of hashes just tries common passwords one by one (`123456`, `password`, ...), hashes each, and compares with the list. Most passwords people choose are weak, so most hashes fall within seconds to minutes. A fast hash becomes a weapon for the attacker.

In addition, without salt two users with the same password have the same hash, so cracking one cracks the whole group. And rainbow tables exist (a precomputed table from password to hash, compressed cleverly to save memory), which let attackers reverse common hashes almost instantly.

### Salt

A salt is a random string, different for each user, joined to the password before hashing, and store `salt` and `H(salt || pw)`. The salt does not need to be secret, and it can be stored in the open next to the hash. It solves two things:

- Rainbow tables become useless: a table precomputed for `H(pw)` no longer matches `H(salt || pw)`. To use a table you would have to recompute it for every salt, which loses the benefit of precomputation.
- Two users with the same password get different hashes, so one crack does not give many.

But salt does NOT make the hash slower. The attacker still brute-forces each account at GPU speed. Salt blocks precomputation and duplication, and does not block targeted brute force. A second layer is needed.

### Slow KDFs: bcrypt, scrypt, argon2

The idea is to use a function that is deliberately slow and whose slowness is adjustable, called a password hashing function or KDF (key derivation function). They include a salt and have a cost parameter we can tune.

- bcrypt: based on Blowfish, with a cost parameter (the number of iterations as a power of 2, for example cost 12). Each increase of 1 doubles the time. It is old and well tested, with a 72-byte password limit.
- scrypt: deliberately uses a lot of memory (memory-hard), which makes it hard to parallelize on GPUs and ASICs because memory costs more than computation. Parameters are `N`, `r`, `p`.
- argon2: winner of the Password Hashing Competition in 2015 and the currently recommended choice. `argon2id` balances GPU resistance and side-channel resistance. Parameters are time (`t`), memory (`m`), and parallelism (`p`).

The shared reasoning is that if one password check takes 100 milliseconds, the user does not notice, but an attacker who wants to try a billion passwords needs a lifetime. We buy time by spending time on purpose. For passwords, slow is a feature.

### Cracking: hashcat and john

With a list of hashes (for example from a CTF or an authorized pentest), the two standard tools are hashcat (runs on GPU, extremely fast) and John the Ripper (john, flexible, good at detecting formats). Two concepts to know:

- Hash mode (hashcat calls it `-m`): tells hashcat what kind of hash this is. MD5 is `-m 0`, SHA-256 is `-m 1400`, SHA-512 is `-m 1700`, bcrypt is `-m 3200`, NTLM is `-m 1000`, md5crypt is `-m 500`, sha512crypt is `-m 1800`.
- Attack mode (`-a`): how candidates are generated. `-a 0` is straight (go through a wordlist), `-a 3` is brute force with a mask (a pattern of characters), `-a 6` is wordlist plus mask, `-a 1` combines two wordlists.

Rainbow tables are used less now because salt makes them useless and because GPU brute force is already very fast on unsalted hashes, but they still show up in old challenges or on unsalted hashes.

## 2. Demo

The script below hashes a password in several ways, shows that salt gives different hashes for the same password, measures the speed difference between MD5 and bcrypt, and then cracks an unsalted MD5 hash with a small dictionary.

```python
# password_demo.py: why fast MD5 is harmful, and how to store passwords correctly
import hashlib, os, time, bcrypt
from argon2 import PasswordHasher

pw = b"hunter2"

# 1. fast hash: same password -> same hash (no salt) -> rainbow tables work great
print("md5(hunter2)    :", hashlib.md5(pw).hexdigest())
print("sha256(hunter2) :", hashlib.sha256(pw).hexdigest())

# 2. salt: same password, 2 different salts -> 2 different hashes
salt1, salt2 = os.urandom(16), os.urandom(16)
print("sha256(salt1||pw):", hashlib.sha256(salt1 + pw).hexdigest())
print("sha256(salt2||pw):", hashlib.sha256(salt2 + pw).hexdigest())

# 3. slow KDF with automatic salt: bcrypt, argon2
bh = bcrypt.hashpw(pw, bcrypt.gensalt(rounds=12))
print("bcrypt          :", bh.decode())
print("bcrypt verify   :", bcrypt.checkpw(pw, bh))
ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
ah = ph.hash(pw.decode())
print("argon2id        :", ah)

# 4. why fast is harmful: measure the cracking speed
N = 300000
t0 = time.time()
for _ in range(N):
    hashlib.md5(pw)
md5_rate = N / (time.time() - t0)
t0 = time.time()
R = 10
for _ in range(R):
    bcrypt.hashpw(pw, bcrypt.gensalt(rounds=12))
bcrypt_rate = R / (time.time() - t0)
print()
print("md5    : %12.0f hashes/sec" % md5_rate)
print("bcrypt : %12.1f hashes/sec (cost=12)" % bcrypt_rate)
print("bcrypt is about %.0f times slower than MD5 on this very machine" % (md5_rate / bcrypt_rate))

# 5. real crack: unsalted MD5 vs a small dictionary
leaked = hashlib.md5(b"hunter2").hexdigest()
wordlist = [b"123456", b"password", b"admin", b"hunter2", b"letmein", b"qwerty"]
t0 = time.time()
cracked = None
for w in wordlist:
    if hashlib.md5(w).hexdigest() == leaked:
        cracked = w
        break
print()
print("leaked hashes:", leaked)
print("cracked   :", cracked, "after %.6f sec" % (time.time() - t0))
```

Running it gives this output (the salted hashes, bcrypt and argon2 change on every run because the salt is random; speeds depend on the machine):

```
md5(hunter2)    : 2ab96390c7dbe3439de74d0c9b0b1767
sha256(hunter2) : f52fbd32b2b3b86ff88ef6c490628285f482af15ddcb29541f94bcf526a3f6c7
sha256(salt1||pw): 9b0b59df6cab0b1ad23c231d5139860637f92b58192e426fd8f4488cdbf42807
sha256(salt2||pw): abcc14b1f1870ea859feb2e9730730af130b2a69ceaa7241b9eba35deb84bb9b
bcrypt          : $2b$12$2YBDFougoLKEhg.AciQkIufbv5qi6.P0z1W4W1NmvxO88qR.FFyR.
bcrypt verify   : True
argon2id        : $argon2id$v=19$m=65536,t=3,p=4$qSyTb/xZbAkx7fR+/hQomQ$FCWpZKhed0Rf12AVzQsQG2nP5aWYFB0TWwKbad3Hdrg

md5    :      5297734 hashes/sec
bcrypt :          4.2 hashes/sec (cost=12)
bcrypt is about 1263639 times slower than MD5 on this very machine
```

```
leaked hashes: 2ab96390c7dbe3439de74d0c9b0b1767
cracked   : b'hunter2' after 0.000016 sec
```

Reading the output, the same password `hunter2` gives two completely different hashes on the two `sha256(salt...)` lines, which is the effect of salt. The speed lines are the main point: on this machine MD5 runs over five million hashes per second, while bcrypt at cost 12 runs just over four per second, about a million times slower. On a GPU the gap is even larger. The bcrypt string `$2b$12$...` and the argon2 string `$argon2id$v=19$m=65536,t=3,p=4$...` carry the cost parameters and the salt inside them, so nothing extra needs to be stored. The crack section shows that an unsalted MD5 of a common password falls in 0.000016 seconds with only six words. That is why a fast hash cannot protect a weak password.

### Using hashcat and john in practice

Assume a file `hashes.txt` with one MD5 hash per line and a wordlist `rockyou.txt`:

```bash
# hashcat: -m 0 is MD5, -a 0 is a wordlist attack
hashcat -m 0 -a 0 hashes.txt rockyou.txt

# brute-force mask: 6 lowercase chars + digits (?l = a-z, ?d = 0-9)
hashcat -m 0 -a 3 hashes.txt ?l?l?l?l?d?d

# wordlist plus mask: append 2 digits to every word
hashcat -m 0 -a 6 hashes.txt rockyou.txt ?d?d

# bcrypt is -m 3200, SHA-256 is -m 1400, SHA-512 is -m 1700, NTLM is -m 1000
hashcat -m 3200 -a 0 bcrypt_hashes.txt rockyou.txt

# show the cracked results
hashcat -m 0 hashes.txt --show
```

```bash
# john the ripper: detects the format itself, simpler
john --wordlist=rockyou.txt hashes.txt
john --show hashes.txt

# force the format when needed
john --format=raw-md5 --wordlist=rockyou.txt hashes.txt
```

With a wrong `-m`, hashcat cracks nothing even if the password is in the wordlist, so identifying the hash type is always the first step. Tools such as `hashid` or `hash-identifier` help guess the type.

## 3. Lab

- Task: You have a file `leak.txt` with many `username:hash` lines, where the hash is an unsalted MD5 of passwords taken from a public wordlist. Crack as many as you can, then repeat with the same password list hashed with bcrypt at cost 12 and compare the time.
- Files: build them yourself. Take a dozen passwords from a small wordlist, hash them with MD5 into `leak_md5.txt`, and hash them with bcrypt into `leak_bcrypt.txt`.
- Hints, step by step:
  1. Crack `leak_md5.txt` with `hashcat -m 0 -a 0 leak_md5.txt wordlist.txt`. Record the time.
  2. Crack `leak_bcrypt.txt` with `hashcat -m 3200 -a 0 ...`. Observe that it is much slower with the same wordlist.
  3. Try adding salt to MD5 by writing a script that creates `H(salt || pw)` with a different salt per line, then try a rainbow table or an online lookup. See that it no longer matches.
  4. Draw a conclusion about what salt blocks, what cost blocks, and how the two complement each other.
- Done when: you crack most of `leak_md5.txt` within seconds, see that `leak_bcrypt.txt` is much slower, and correctly explain the role of salt compared with cost.

## 4. Key takeaways

- Never store plain text, and `MD5(pw)`/`SHA256(pw)` is also not enough because the hash is too fast.
- Salt defends against rainbow tables and duplicate hashes, but does not slow targeted brute force.
- Use a slow KDF with an adjustable cost: bcrypt, scrypt, or argon2id (the current recommendation).
- bcrypt/argon2 strings carry the cost and salt, so nothing extra needs to be stored.
- hashcat needs the right hash mode (`-m`) and attack mode (`-a`); identify the hash type first.
- For passwords, slow is a feature and not a weakness.

## 5. Common pitfalls

- Believing salt is enough. Salt blocks precomputation, and does not block GPU brute force against each account. You still need a slow KDF.
- Using SHA-256 because it is "stronger than MD5". It is stronger for collisions but still far too fast for password storage. Both are the wrong tool.
- Building a KDF by looping SHA-256 a few thousand times. The idea (slow it down) is right, but details are easy to get wrong and it lacks memory hardness. Use a mature library (PBKDF2 if you must, argon2 is better).
- Setting the cost too low to save performance. The cost should make one check take tens to hundreds of milliseconds on real hardware, and it should be raised over time.
- Picking the wrong `-m` in hashcat and concluding the password cannot be cracked. Always recheck the hash type.
- Confusing cracking a hash (a preimage of a weak password) with breaking the hash function (a collision). Password cracking works because of weak passwords and fast hashes, not because MD5 is broken for collisions.

## 6. Further reading

- OWASP Password Storage Cheat Sheet, the standard practical guidance and recommended cost parameters.
- The argon2 specification (RFC 9106) and the Password Hashing Competition page.
- The hashcat wiki, with the full list of hash modes and attack modes, and mask examples.
- John the Ripper documentation, the wordlist and incremental mode sections.
- "Speak Much, Remember Little" and other papers on memory-hard functions, if you want to understand why scrypt/argon2 resist GPUs.
