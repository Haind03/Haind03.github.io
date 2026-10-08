---
title: "Lesson 6.1: How RSA Works"
image:
  path: /assets/img/covers/crypto-6-1-rsa-works.webp
  alt: "How RSA Works"
date: 2023-07-26 17:34:00 +0700
categories: ["Cryptography", "Crypto · RSA"]
tags: [cryptography, rsa, public-key, factoring]
render_with_liquid: false
---

RSA is the first public-key cryptosystem you need to know well before you try to break it. This lesson rebuilds the whole life of an RSA key, from generation (p, q, n, phi, e, d), encryption, decryption, digital signatures, and, most important, why its security rests on a single hard problem, factorization.

![How RSA works](/assets/img/crypto/crypto-6-1-rsa-works.svg)
_Key generation from two primes, encryption with the public key, decryption with the private key, and the factoring attack._

Part 6 (RSA) | Time: about 35 minutes | Difficulty: easy

**Prerequisites:** Lesson 1.1 (modular arithmetic: fast exponentiation, inverses) and Lesson 1.2 (primes, Euler's phi, Euler's theorem). If modular inverses are still unclear, reread them first, because this whole lesson revolves around them.

**Tools:** Python 3 + PyCryptodome + gmpy2. Quick install: `pip install pycryptodome gmpy2`.

## Goals

After this lesson you can generate an RSA key pair by hand with small numbers and know what each of p, q, n, phi, e, d means, explain why `(m^e)^d = m mod n` by Euler's theorem instead of memorizing it, tell encryption from signing (which uses which key, and why the roles swap), and say exactly which problem must be hard for RSA to be secure and what an attacker needs to break it.

## 1. Theory

### 1.1. The original idea

Before RSA, every cryptosystem was symmetric: both sides had to share one secret key in advance. That is a chicken-and-egg problem, since exchanging a key securely needs a secure channel to begin with. RSA (Rivest, Shamir, Adleman, 1977) changes this, since everyone has a key pair, one public that everyone sees and one private that stays secret. Anyone can lock a box addressed to you, but only you can open it.

The foundation is a trapdoor one-way function, which is easy to compute forward and extremely hard to compute backward unless you hold a secret trapdoor. For RSA the forward direction is modular exponentiation, and the trapdoor is knowing how to factor n into p times q.

### 1.2. Key generation

The steps to generate an RSA key:

1. Choose two large distinct primes p and q (in practice 1024 bits or more each).
2. Compute the modulus `n = p * q`. The number n is public and sets the key length (RSA-2048 means n is 2048 bits long).
3. Compute Euler's phi function (the count of positive integers below n that are coprime with n). Since n is a product of two primes, `phi = (p-1)*(q-1)`.
4. Choose a public exponent e with `1 < e < phi` and `gcd(e, phi) = 1`. In practice it is almost always `e = 65537` (the Fermat prime F4, whose binary form 10000000000000001 has only two 1 bits, so exponentiation is fast).
5. Compute the private exponent `d = e^(-1) mod phi`, the modular inverse of e modulo phi. This is where the extended Euclidean algorithm is needed.

The public key is the pair `(n, e)`. The private key is `d` (usually stored together with p and q to decrypt faster using CRT, see Lesson 1.3).

### 1.3. Encryption and decryption

For a plaintext that is an integer m in the range `0 <= m < n`:

- Encrypt: `c = m^e mod n` (using the public key).
- Decrypt: `m = c^d mod n` (using the private key).

Why does decryption return m? We need `(m^e)^d = m^(e*d) = m mod n`. By how d was chosen, `e*d = 1 mod phi`, which means `e*d = 1 + k*phi` for some integer k. When `gcd(m, n) = 1`, Euler's theorem gives `m^phi = 1 mod n`, so:

```
m^(e*d) = m^(1 + k*phi) = m * (m^phi)^k = m * 1^k = m  (mod n)
```

If m is divisible by p or q, check it with the Chinese Remainder Theorem (CRT). The result is still correct, so the formula holds for every m in the range.

### 1.4. Digital signatures

A digital signature swaps the roles of the two keys. To prove that a message really is yours:

- Sign: `s = h^d mod n`, where h is the hash of the message (signing the raw m directly is wrong, see section 5). This uses the private key.
- Verify: anyone computes `h' = s^e mod n` with the public key, then compares h' with the hash of the message they received. If they match, the signature is valid.

The logic is the same as encryption with the keys reversed, so only the holder of d can create s, while everyone can verify with e. Encryption gives confidentiality, and signing gives authentication and integrity.

### 1.5. Three questions to be able to answer

1. What does the correct mechanism look like? One modular exponentiation going out and one coming back, with the two exponents e and d being inverses of each other modulo phi.
2. Where can it go wrong? e too small, no padding, p and q generated carelessly (close together, or from a weak RNG), a shared n, d too small. The remaining lessons in this part cover each of these failures.
3. How is it exploited when it goes wrong? If an attacker can factor `n = p*q`, they can compute phi, then d, and so have the private key. Every attack on RSA either finds a way to factor n, or avoids factoring by using some other implementation flaw.

## 2. Demo

### 2.1. RSA with small numbers, by hand

This is the classic textbook example, small enough that you can recheck each step on a calculator.

```python
# rsa_toy.py: RSA with small numbers to see every parameter clearly
from Crypto.Util.number import inverse

p, q = 61, 53            # two small primes
n = p * q                # modulus
phi = (p - 1) * (q - 1)  # phi Euler = 60 * 52
e = 17                   # choose e coprime with phi
d = inverse(e, phi)      # d = e^(-1) mod phi

print(f"n   = {n}")       # 3233
print(f"phi = {phi}")     # 3120
print(f"e   = {e}, d = {d}")  # e=17, d=2753

m = 65                    # plaintext is a number < n
c = pow(m, e, n)          # encrypt
print(f"c = {c}")         # 2790
print(f"decrypt = {pow(c, d, n)}")  # 65, equal to m

# Signature (sign directly on an assumed hash value = 1234)
h = 1234
s = pow(h, d, n)          # sign with the private key
print(f"signature s = {s}")  # 1512
print(f"verify = {pow(s, e, n)}")  # 1234, matches h
```

Output:

```
n   = 3233
phi = 3120
e   = 17, d = 2753
c = 2790
decrypt = 65
signature s = 1512
verify = 1234
```

Read the numbers closely. `e*d = 17 * 2753 = 46801 = 1 + 15*3120`, which is indeed `1 mod phi`. Encrypting m=65 gives c=2790, and decrypting c=2790 gives 65 again. The signature 1512 verified with e gives back 1234. Everything matches because d is the inverse of e.

Note the fatal point. In this example you only need to know `n = 3233` and you factor it at once into `61 * 53`, then compute phi and d. Small RSA is insecure because factoring is too easy.

### 2.2. A real key and using a library

When doing this for real, do not generate primes by hand. Use a tested library.

```python
# rsa_real.py: generate real keys and encrypt/decrypt with a library
from Crypto.Util.number import getPrime, inverse, bytes_to_long, long_to_bytes

bits = 1024                  # each prime is 1024 bits -> n is about 2048 bits
p = getPrime(bits)
q = getPrime(bits)
n = p * q
phi = (p - 1) * (q - 1)
e = 65537
d = inverse(e, phi)

msg = b"RSA by hand key generation"
m = bytes_to_long(msg)       # convert bytes to an integer
assert m < n                 # the message must be smaller than n

c = pow(m, e, n)
rec = pow(c, d, n)
print(long_to_bytes(rec))    # b'RSA by hand key generation'
```

Here `bytes_to_long` joins the message bytes into one large integer (big-endian). This is how any text message becomes the m that goes into RSA.

Note that the demo above is "textbook RSA", raw encryption without padding. It shows the mechanism but must never be used for real, because it is deterministic (the same m gives the same c) and falls to many attacks in the next lessons. For real use, use OAEP:

```python
# rsa_oaep.py: encrypt the right way with OAEP (random padding)
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

key = RSA.generate(2048)
pub = key.publickey()

c = PKCS1_OAEP.new(pub).encrypt(b"secret message")
m = PKCS1_OAEP.new(key).decrypt(c)
print(m)  # b'secret message'
```

Why padding matters is left for Lesson 6.5. For now, remember that textbook RSA is for learning and OAEP is for use.

## 3. Lab

- Task: generate a key pair by hand where p and q are two 4-digit primes (for example with `sympy.randprime(1000, 9999)`). Encrypt the string `b"CTF"` (convert it with `bytes_to_long`), then pretend you forgot d and only have `(n, e, c)`. Factor n by hand (or with `sympy.factorint`) to recompute d and recover the plaintext.
- Side goal: sign the string `b"hello"` (take the SHA-256 hash as 32 bytes, then `bytes_to_long`), then change one bit of the message and check that the signature is no longer valid.
- Hints, step by step: (1) remember `d = inverse(e, (p-1)*(q-1))`; (2) `factorint(n)` returns a dict of the factors; (3) if signature verification does not match, print both `s^e mod n` and the hash and compare them byte by byte.
- Done when: you recover the correct plaintext from `(n, e, c)` alone, when n is small enough to factor.

## 4. Key takeaways

- The public key is `(n, e)`, the private key is `d`, with `d = e^(-1) mod phi` and `phi = (p-1)*(q-1)`.
- Encrypt `c = m^e mod n`, decrypt `m = c^d mod n`. Signing reverses it: `s = h^d`, verify `h = s^e`.
- Decryption is correct because `e*d = 1 mod phi` together with Euler's theorem.
- The security of RSA equals the difficulty of factoring n. If you can factor n, you also have d.
- Textbook RSA is for learning only. For real use, OAEP for encryption and PSS for signatures.

## 5. Common pitfalls

- Mixing up the roles of the two keys: encryption uses the recipient's public key, signing uses the sender's private key. Swapping them is wrong for both security and logic.
- Signing the raw message instead of its hash. This limits the length (m must be smaller than n) and also opens the door to existential forgery through RSA's multiplicative property. Always hash before signing.
- Forgetting the condition `m < n`: a message longer than n is reduced modulo n and cannot be recovered. RSA is not used to encrypt long data directly. It encrypts a symmetric key (hybrid encryption).
- Assuming textbook RSA is secure. It is deterministic and purely multiplicative (homomorphic under multiplication), and is open to small e, common modulus, Hastad, and chosen ciphertext attacks. The following lessons show each one.
- Using a very small e (for example e=3) without padding: it falls at once to the cube root attack (Lesson 6.2).

## 6. Further reading

- Rivest, Shamir, Adleman, "A Method for Obtaining Digital Signatures and Public-Key Cryptosystems" (1978), the original paper, to see the first form of the idea.
- "A Graduate Course in Applied Cryptography" (Boneh, Shoup), the chapter on trapdoor permutations and RSA.
- CryptoHack, the "RSA" track, Starter section, to get used to handling large number inputs.
