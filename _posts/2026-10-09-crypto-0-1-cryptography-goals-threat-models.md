---
title: "Lesson 0.1: Cryptography Goals and Threat Models"
image:
  path: /assets/img/covers/crypto-0-1-cryptography-goals-threat-models.webp
  alt: "Cryptography Goals and Threat Models"
date: 2023-01-02 09:00:00 +0700
categories: ["Cryptography", "Crypto · Getting Started"]
tags: [cryptography, threat-model, confidentiality, integrity]
render_with_liquid: false
---

This opening lesson defines what cryptography protects, what "secure" means once you state it properly, and why almost every crypto challenge in a CTF does not ask you to break AES. It asks you to find the place where someone used AES wrongly.

![Cryptography Goals and Threat Models](/assets/img/crypto/crypto-0-1-cryptography-goals-threat-models.svg)
_Encryption covers confidentiality only; integrity and authentication need a MAC or authenticated encryption._

Part: 0 (Getting Started) | Time: about 25 minutes | Difficulty: easy

**Prerequisites:** none.

**Tools:** nothing to install, just reading. There is a short Python script at the end if you want to run it.

## Goals

After this lesson you can tell confidentiality, integrity and authentication apart, and you know that encryption only handles the first one. You understand why a claim of "secure" needs a threat model. You can separate symmetric from asymmetric crypto and know that real systems combine both (hybrid). You also know why CTF crypto is almost always an implementation bug and not a break of the original algorithm.

## 1. Theory

I will skip the usual "in the digital age, data is valuable" opening. Cryptography is a set of mathematical tools that let two parties exchange information while a third party listens in or interferes. Many people get one point wrong from the start, because encryption does not solve every security problem. It solves exactly one part. Knowing what it protects and what it does not protect is what lets you spot vulnerabilities later.

### The three security goals

When we talk about protecting a message, we care about three different things. Do not merge them into one.

- Confidentiality: only authorized people can read the content. If you send a private message, someone sitting in the same cafe who captures the Wi-Fi packets still reads nothing. Encryption handles this.
- Integrity: the content is not modified on the way without detection. If you transfer "pay A 10 thousand", a man in the middle must not be able to silently change it to "pay B 10 million" while the receiver still believes it is genuine.
- Authentication: you are sure the message really comes from the person you think it comes from, not from an impostor. When you log in, the server must trust that the request really comes from you.

A fourth goal is often mentioned with them, non-repudiation: the signer of a message cannot later deny having signed it. Digital signatures provide this. We leave it for now and meet it again in parts 5 and 6.

Now the most important point of this lesson: encryption gives you confidentiality only. It does NOT automatically give you integrity or authentication. Encrypting a message does not make it tamper-proof. This sounds counterintuitive, but it is true, and the belief that "encrypted means safe from everything" produces a large number of vulnerabilities. A classic example appears in part 4. CBC mode without an integrity check (a MAC) lets an attacker flip bits in the ciphertext to change the plaintext as they like, without knowing the key. That is CBC bit-flipping, and it exists because someone assumed encryption was enough.

### Basic vocabulary

Let us agree on terms first:

- Plaintext: the original, readable data.
- Ciphertext: the data after encryption, which looks like noise.
- Key: the secret used to encrypt and decrypt.
- Encryption / decryption: turning plaintext into ciphertext and back.
- Cipher: the encryption algorithm itself.

Three more things are often confused, and you will hear them throughout the series:

- Encoding (for example Base64, hex) only changes how data is represented. Anyone can reverse it without a key. It is not security. Seeing Base64 and thinking "this is encrypted" is wrong from the start (part 2 covers it in detail).
- Encryption needs a key to reverse, and its goal is confidentiality.
- Hashing is one-way and cannot be reversed. Its goal is to produce a fixed fingerprint of the data (part 5).

### Threat model: secure against whom?

This way of thinking is what separates you from a beginner. The question "is this system secure?" has no meaning until you answer who the system must be secure against, meaning an attacker who can do what? Describing the attacker's capabilities is called a threat model (or attacker model). Without one, every statement about security is just talk.

Cryptographers rank attacker power like this, from weak to strong:

- Ciphertext-only: the attacker only captures ciphertext and must work out the plaintext. This is the weakest level.
- Known-plaintext attack (KPA): the attacker has some (plaintext, ciphertext) pairs and uses them to recover the key or decrypt other ciphertexts.
- Chosen-plaintext attack (CPA): stronger. The attacker can choose any plaintext and see the matching ciphertext. It sounds unrealistic, but it happens all the time: when you send data to a server and it encrypts it and returns the result, you have just performed a CPA.
- Chosen-ciphertext attack (CCA): the strongest of the basic levels. The attacker can hand arbitrary ciphertext to the system for decryption and observe the reaction (success, an error, or the content). A server that decrypts what you send and leaks "bad padding" or "decrypt ok" is a decryption oracle, and it gives you CCA power. The padding oracle attack in part 4 depends on exactly this.

The modern security standard is stated as indistinguishability. The intuition behind IND-CPA: you give the system two messages m0 and m1 of your choice, it secretly encrypts one of them and returns the ciphertext. If you cannot guess which one it encrypted any better than a coin flip, the system is IND-CPA secure. IND-CCA is the same game, but the attacker may also query a decryption oracle. You do not need the formal definition now. The idea is that "secure" means the attacker learns nothing at all, not even "do these two ciphertexts contain the same message". A deterministic encryption scheme (the same plaintext always gives the same ciphertext) fails IND-CPA immediately, because you can tell the two apart. This is why serious encryption always includes randomness (an IV or a nonce).

In a CTF, the threat model usually shows up in the server the challenge gives you: what it lets you send, and what it returns. Recognizing that you have a CPA or CCA oracle gets you halfway to the solution.

### Symmetric and asymmetric

There are two large families:

- Symmetric: both sides use the same secret key to encrypt and decrypt. An example is AES. It is fast, very fast. The drawback is key distribution, because both sides must get the same key without it leaking in transit. This is hard when the two sides have never met.

- Asymmetric / public key: each person has a key pair, a public key (given to everyone) and a private key (kept secret). Anyone can encrypt with your public key, but only you can decrypt with your private key. Examples are RSA and ECC. This solves key distribution cleanly, since no secret channel is needed to share a key beforehand. The cost is that it is many times slower than symmetric crypto, and it depends on math problems believed to be hard (factoring large numbers for RSA, discrete log for Diffie-Hellman and ECC). "Hard" here means nobody knows a fast way to solve them, not that it is absolutely impossible.

In practice nobody picks just one. They are combined into a hybrid scheme: use asymmetric crypto so both sides agree on a shared secret key, then use that key with symmetric crypto to encrypt bulk data quickly. TLS, the small lock in your browser's address bar when you visit HTTPS, works exactly this way: the handshake uses public key crypto, then the page is delivered with AES.

### Why CTF crypto is almost always an implementation bug

This is the thesis of the whole series, so remember it. You will almost never break AES or RSA at the algorithm level. Standardized algorithms have been attacked by thousands of researchers for decades and they still stand. If you sit down and try to break AES by guessing the key, you will die of old age first.

What breaks, and what every crypto challenge targets, is how these algorithms are used. Some examples you will meet:

- Reusing a nonce (number used once) in a stream cipher or in CTR mode, which leaks plaintext.
- ECB mode, which leaks patterns in the data.
- RSA with a public exponent e that is too small and no padding, solvable with a cube root.
- ECDSA reusing a nonce while signing, which leaks the private key.
- Encryption without a MAC, which opens the door to bit-flipping and padding oracles.
- Random numbers generated from a predictable source (time, PID), so the key has no entropy.

In other words, the weak point of a cryptosystem is not its math but the people who implement it. Learning crypto from the attack side means learning to recognize where people tend to make mistakes. That is why this series has you rebuild these bugs in a lab and then break them yourself: so that next time you meet one in a real challenge, you recognize it quickly.

## 2. Hands-on (demo)

To make "encryption does not give integrity" concrete, here is a small demo in plain Python, with nothing to install. I use a fake keystream to simulate a stream cipher like AES-CTR: encryption is plaintext XOR keystream. What to watch for is that if the attacker flips one bit in the ciphertext, exactly one matching bit in the plaintext flips after decryption, and nothing raises an alarm. The attacker does not know the key and cannot read the content, yet they can still modify the content in a controlled way.

```python
# integrity_demo.py: shows that encryption does NOT automatically protect integrity
# Standard library only.
import os, hashlib

def keystream(key: bytes, length: int) -> bytes:
    # Simulate a stream cipher: generate a keystream from the key (here SHA256 serves as a simple PRF).
    out = b""
    counter = 0
    while len(out) < length:
        out += hashlib.sha256(key + counter.to_bytes(8, "big")).digest()
        counter += 1
    return out[:length]

def crypt(key: bytes, data: bytes) -> bytes:
    # Both encryption and decryption are XOR with the keystream (a symmetric stream cipher).
    ks = keystream(key, len(data))
    return bytes(d ^ k for d, k in zip(data, ks))

def main():
    key = os.urandom(16)                 # secret key, the attacker does NOT know it
    msg = b"user=guest&admin=0"
    ct = crypt(key, msg)
    print("Original plaintext:", msg)
    print("Ciphertext         :", ct.hex())

    # The attacker does NOT know the key, but knows the plaintext structure (position of the last "0" byte).
    # Goal: turn admin=0 into admin=1 by flipping ciphertext bits.
    # XOR of byte '0' (0x30) with '1' (0x31) = 0x01, which flips exactly 1 bit at that position.
    pos = len(ct) - 1
    forged = bytearray(ct)
    forged[pos] ^= (ord("0") ^ ord("1"))

    # When the victim decrypts the forged ciphertext with their own key:
    recovered = crypt(key, bytes(forged))
    print("After tampering  :", recovered)

if __name__ == "__main__":
    main()
```

Output:

```
Original plaintext: b'user=guest&admin=0'
Ciphertext         : (a random hex string, different every run)
After tampering  : b'user=guest&admin=1'
```

The attacker turned `admin=0` into `admin=1` without knowing the key. Why does it work? In a stream cipher, ciphertext = plaintext XOR keystream. When you flip one bit of the ciphertext, that bit decrypts to plaintext XOR keystream, so the plaintext bit flips at the same position. The keystream does not change, so the rest stays intact. The system has no way to know the data was touched, because it only provides confidentiality.

This is exactly why real systems do not use bare encryption but authenticated encryption (for example AES-GCM). It attaches a MAC, so if even one bit of the ciphertext is changed, decryption reports an error and rejects the message. Parts 4 and 5 rebuild all of this.

## 3. Lab

There is no accompanying file. This is a thinking exercise to apply what you just saw.

- Task: a server takes a cookie of the form `username=<name>;role=user`, encrypts it with a stream cipher (XOR keystream as in the demo above), and gives it to the client to hold. On each request the client sends the encrypted cookie back, and the server decrypts it and trusts the `role` field. You register with an ordinary name and receive the encrypted cookie. The goal is to modify the cookie so that `role=user` becomes `role=root` (or `admin`) and take over the privilege, without knowing the key.
- Files: none, build it yourself from the description to practice.
- Hints, step by step (read them one at a time when stuck):
  - Hint 1: you know your own original plaintext exactly (`role=user`), so you know which byte positions to change.
  - Hint 2: with a stream cipher, flipping a bit of the ciphertext flips exactly that bit of the plaintext. To change the character `u` into another character, XOR the matching ciphertext byte with `ord('u') ^ ord('new character')`.
  - Hint 3: if `user` and `root` have different lengths, watch the alignment. Pick a target of the same length so you do not need to shift bytes.
- Done when: you can explain (and do in code) why you can change `role` without the key, and state in one line what the system needs to stop this (hint: a MAC).

## 4. Key takeaways

- [ ] Three separate goals: confidentiality, integrity, authentication. Encryption only provides confidentiality.
- [ ] Encryption does not prevent modification. To prevent it you need integrity (a MAC, authenticated encryption).
- [ ] "Secure" is meaningless without a threat model. Always ask what the attacker can do (ciphertext-only, KPA, CPA, CCA).
- [ ] Deterministic encryption fails IND-CPA. Serious encryption needs randomness (an IV or a nonce).
- [ ] Symmetric is fast but hard to share keys for; asymmetric solves key sharing but is slow; real systems use hybrid.
- [ ] CTF crypto is about finding implementation bugs, not breaking the original algorithm.

## 5. Common pitfalls

- Treating encoding as encryption. Base64 and hex protect nothing, and anyone can reverse them without a key.
- Believing "encrypted" means safe from modification and forgery. It does not. That is integrity, and it needs its own mechanism.
- Calling a system "secure" without saying secure against whom. Without a threat model the statement is empty.
- Going after AES or RSA at the algorithm level. This is almost always hopeless, and the thing to look for is misuse.
- Thinking deterministic encryption is fine. The same plaintext giving the same ciphertext already leaks information (two messages are identical), and fails the security standard.

## 6. Further reading

- "Serious Cryptography" (Jean-Philippe Aumasson), chapter 1, which explains clearly what security means.
- "Cryptography Engineering" (Niels Ferguson, Bruce Schneier, Tadayoshi Kohno), the opening chapters on threat models and the engineering mindset.
- Cryptopals Crypto Challenges (cryptopals.com), sets 1 and 2, to get used to thinking like an attacker.
- CryptoHack (cryptohack.org), the Introduction and Encoding sections as a warm-up.
