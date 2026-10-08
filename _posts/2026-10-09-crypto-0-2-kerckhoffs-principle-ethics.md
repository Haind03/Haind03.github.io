---
title: "Lesson 0.2: Kerckhoffs's Principle and Ethics"
image:
  path: /assets/img/covers/crypto-0-2-kerckhoffs-principle-ethics.webp
  alt: "Kerckhoffs's Principle and Ethics"
date: 2026-10-09 08:10:00 +0700
categories: ["Cryptography", "Crypto · Getting Started"]
tags: [cryptography, kerckhoffs, obscurity, ethics]
render_with_liquid: false
---

This lesson answers a question many beginners get backwards: where does the secret of a cryptosystem live? After reading it you will know why hiding the algorithm gives no real protection, why you should never invent your own cipher, and where the line is that you must not cross when attacking.

![Kerckhoffs's Principle and Ethics](/assets/img/crypto/crypto-0-2-kerckhoffs-principle-ethics.svg)
_Under Kerckhoffs's principle the attacker knows everything about the system except the key._

Part: 0 (Getting Started) | Time: about 20 minutes | Difficulty: easy

**Prerequisites:** Lesson 0.1 (what cryptography is).

**Tools:** none, this lesson is about mindset. There is a short Python script at the end if you want to run it.

## Goals

After this lesson you can state Kerckhoffs's principle and explain why the secret must be the key and not the algorithm. You can tell security through obscurity apart from real security and name a few real failures. You can explain why "don't roll your own crypto" is more than a slogan. You also know the scope and ethics of attacking, and what responsible disclosure is.

## 1. Theory

### What Kerckhoffs said

In 1883 Auguste Kerckhoffs wrote "La cryptographie militaire" for the French army. In it he set out six requirements for a practical cryptosystem. Summarized, they are:

1. The system must be secure in practice, even if it cannot be proven secure in theory.
2. Revealing how the system works must not harm its users. This is the best known requirement.
3. The key must be memorable without writing it down, and easy to change.
4. The ciphertext must be transmittable by telegraph.
5. The equipment must be portable and operable by one person.
6. The system must be easy to use, without requiring the user to remember a long list of rules.

Requirement 2 is the one that has survived to this day. Claude Shannon later restated it more briefly, in a sentence every cryptographer knows: "the enemy knows the system". You must design assuming the attacker has the complete algorithm description, the source code, the hardware, everything except the key.

So the whole secret is concentrated in the key. The algorithm can be treated as if it were printed in a newspaper for the world to read. If your system is still secure in that situation, then it is really secure.

This feels counterintuitive at first. Beginners often think "the more I hide, the harder it is to break". But consider it carefully: an algorithm is very hard to keep secret. It sits in a binary shipped to millions of machines, in a chip sold in shops, in the heads of the people who built it. A key is the opposite: short, replaceable in a second, and different for every user. Putting the secret in the thing that is easy to protect is sound engineering.

### Security through obscurity

Security through obscurity is the opposite of Kerckhoffs: betting the safety of the system on the attacker not knowing how it works. The problem is that "not knowing" is not a stable state. A reverse engineer who is skilled and patient enough will remove the whole layer of obscurity.

History is full of systems that relied on secrecy and failed:

- A5/1, the GSM call encryption algorithm, was designed in secret in the 1980s. When it leaked and was published, researchers broke it in a very short time, to the point that precomputed rainbow tables later allowed near instant decryption.
- CSS, the DVD copy protection scheme. It was kept secret, then reversed, and the code to break it (DeCSS) was so short that people printed it on T-shirts.
- Crypto-1, the algorithm in MIFARE Classic cards (the kind of card used for elevators and buses everywhere). NXP kept the design secret. Researchers inspected the chip, reverse engineered the algorithm, and showed it was badly weak. Millions of access control systems were affected.
- The German Enigma in World War II: part of its collapse came from the Allies learning how the machine was built, and the rest from operator mistakes.

What they have in common is that when the mechanism is the only protection, a single leak (and it always leaks) kills the whole system at once, and it cannot be patched quickly, because you cannot "change the algorithm" as easily as you change a key.

In CTFs this is even clearer. A decent crypto challenge usually gives you the source code. The author is not afraid of you reading the code, because the safety (if there is any) does not depend on you being in the dark. If a challenge is only "hard" because you do not know what it does, it is a reverse engineering challenge in disguise, not a crypto challenge.

### Don't roll your own crypto

"Don't roll your own crypto" is advice repeated until it is tiresome, but it is correct enough to repeat once more.

The reason is not that you are not smart. The reason is that doing crypto correctly is hard in a counterintuitive way. A homemade cipher looks complicated and "strong" to its author, but it has never gone through the most important process: being examined by thousands of cryptographers for decades who tried to break it. AES, SHA-2, RSA and Curve25519 all survived that. The cipher you wrote last night has not been attacked by anyone, so you have no basis to trust it.

Homemade ciphers often fail in places you do not expect:

- Side channels: the algorithm is mathematically correct, but its running time, power use or cache behavior leaks information about the key.
- Subtly wrong math: a poorly chosen constant, a permutation that does not mix enough, a linear part you did not notice.
- A missing security property you did not know you needed, for example failing IND-CPA because the encryption is deterministic.

Many people also overlook that the protocol and implementation layers count too. Even if you use standard AES correctly, combining it wrongly still breaks it. ECB mode leaks patterns. Reusing a nonce in CTR or GCM leaks plaintext. A badly done MAC-then-encrypt design opens the door to a padding oracle. A standard primitive is a building block, and a badly built house still collapses.

The practical conclusion: in production, use a verified library designed to be hard to misuse, for example libsodium with its AEAD APIs (authenticated encryption, which encrypts and also protects against modification). Do not invent at the primitive level. The place to be creative is the system architecture, not how a matrix is multiplied inside an S-box.

### The CTF learner's paradox

Is this not a contradiction? I just said not to write your own cipher, and now the whole series has you write weak ciphers and then break them?

It is not a contradiction, because these are two different activities. To know where a lock is weak, you have to break it by hand a few times. Writing a toy RSA and breaking it with a small exponent attack is a way to learn, like a locksmith practicing on old locks to understand the mechanism. That is completely different from using your own RSA to protect real user data. When learning to understand and break things, build whatever you like. When deploying for others to trust, use standard components. Keep this boundary in mind.

### Scope and ethics

The skill of breaking crypto cuts both ways, so this section is not a formality. A few rules you must not cross:

- Attack only what you have the right to attack: your own systems, public CTF challenges and wargames, or a target for which you have written permission with a clear scope (the rules of engagement, which define the scope and rules of a pentest). If you have none of these three, stop.
- Understand that the legal consequences are real. Decrypting, accessing or interfering with other people's data without permission is illegal almost everywhere, even if you were "just curious".
- If you happen to find a real vulnerability in a product that is running, do responsible disclosure: report it privately to the responsible party, give them time to patch, and only then publish. Do not sell it, do not exploit it, and do not show it off publicly while it is still open.

The spirit of this field is learning to break things so you know how to build them solidly. You break the cheap lock in the lab so that later nobody puts that cheap lock into a real system. That is the reason to get good at crypto.

## 2. Hands-on (demo)

This part does not do any serious encryption. I show a silly "homemade cipher" of the kind beginners come up with, then show how it breaks, to make the point that hiding the algorithm saves nothing.

Suppose someone confidently announces: "I encrypt by XORing each byte with a repeating secret key. I keep the key secret and the algorithm secret, so it is safe." That is exactly repeating-key XOR.

The problem is that as soon as the attacker guesses (or knows) a piece of plaintext, called known-plaintext, a piece of the key is exposed. Knowing a piece of a repeating XOR key gives the whole key, and then everything decrypts. Obscurity is useless here because the XOR mechanism is so simple that guessing it is only a matter of time.

```python
# homemade_break.py: illustrates why hiding the algorithm does not save a weak cipher
# Standard library only, runs as is.

def xor_encrypt(plaintext: bytes, key: bytes) -> bytes:
    # "Homemade cipher": repeating-key XOR. The author thinks hiding the key and the algorithm is safe.
    return bytes(p ^ key[i % len(key)] for i, p in enumerate(plaintext))

def recover_key(ciphertext: bytes, known_plaintext: bytes) -> bytes:
    # The attacker only needs to know a leading piece of plaintext (for example a fixed header like "FLAG{" or "POST ").
    # XOR of the ciphertext with the known plaintext reveals the matching piece of the key.
    return bytes(c ^ p for c, p in zip(ciphertext, known_plaintext))

def main():
    secret_key = b"s3cr3t"  # the "secret" key
    message = b"POST /login HTTP/1.1 user=admin password=hunter2"

    ct = xor_encrypt(message, secret_key)
    print("Ciphertext (hex):", ct.hex())

    # Suppose the attacker knows the message starts with "POST /login" (very common).
    crib = b"POST /login"
    leaked = recover_key(ct, crib)
    print("Key fragment leaked from known plaintext:", leaked)

    # Because the XOR repeats, this key fragment repeats. Taking exactly one period is enough to decrypt everything.
    period = len(secret_key)
    guessed_key = leaked[:period]
    print("Guessed key:", guessed_key)

    recovered = xor_encrypt(ct, guessed_key)  # XOR once more to decrypt
    print("Decrypted:", recovered)

if __name__ == "__main__":
    main()
```

The output looks like this:

```
Key fragment leaked from known plaintext: b's3cr3ts3cr3'
Guessed key: b's3cr3t'
Decrypted: b'POST /login HTTP/1.1 user=admin password=hunter2'
```

Notice that I did not need anyone to tell me the algorithm is XOR. In practice an attacker who looks at a few pairs will guess it quickly, because XOR leaves very characteristic traces. Once the mechanism is guessed, keeping it secret has no value. Under Kerckhoffs's principle this cipher should be secure even with the algorithm public, but it is not, because it is weak at the root. Hiding it only delays you learning that fact by a few days.

## 3. Lab

There is no accompanying file. This is a thinking exercise. Suppose a chat app advertises "end-to-end encryption, our proprietary algorithm". By reversing it, you reconstruct how it works:

- Each message is XORed with a fixed key derived from the sender's phone number (a public value).
- The algorithm uses no nonce or IV, so sending the same message twice gives the same ciphertext.
- The vendor claims "since nobody knows the algorithm, nobody can break it".

Task: write an analysis that lists every way this system violates Kerckhoffs's principle and every reason it is insecure. You do not need to break it for real, only name the flaws and explain them.

Hints, step by step (read them one at a time when stuck):

- Hint 1: if the key is derived from public information, is it still a secret?
- Hint 2: which security standard from Lesson 0.1 does deterministic encryption (no nonce) violate?
- Hint 3: how long does "nobody knows the algorithm" survive against a reverse engineer, and once it leaks, what is left for the whole system to rely on?

Done when: you point out at least three independent flaws (the key is not secret, deterministic encryption fails IND-CPA, reliance on obscurity), and you can say how a correct system differs.

## 4. Key takeaways

- [ ] The secret of a cryptosystem must be in the key, not the algorithm (Kerckhoffs, "the enemy knows the system").
- [ ] Security through obscurity always fails because the mechanism leaks eventually, and when it does it cannot be patched quickly.
- [ ] Don't roll your own crypto: use standard, verified primitives and libraries. Be creative in the architecture, not in the primitive.
- [ ] Even standard primitives used wrongly (ECB, nonce reuse) still collapse, so the implementation layer is part of crypto.
- [ ] Attack only what you have the right to attack, and use responsible disclosure when you find a real vulnerability.

## 5. Common pitfalls

- Thinking "closed source is more secure". Open or closed does not decide security, design does. Open source software with standard crypto is usually more secure than a closed homemade one.
- Writing your own cipher because you believe you are smarter than everyone else. Almost certainly you are not, and the cost is real user data.
- Confusing obfuscation (making code hard to read) with encryption. Obfuscation only slows the reader down and has no mathematical guarantee. It is obscurity, not security.
- Going beyond the permitted scope while testing. "I was just trying" is not a valid excuse when you touch a system that is not yours.

## 6. Further reading

- Auguste Kerckhoffs, "La cryptographie militaire" (1883), the origin of the principle. An English translation is easy to find.
- Bruce Schneier has written many posts on security through obscurity on his blog Schneier on Security.
- "Don't roll your own crypto": search for the well-known summaries from the community (StackExchange Cryptography, cryptographers' blogs) on this topic.
- libsodium documentation: a model example of a crypto library designed to be hard to misuse.
- OWASP has guidance on vulnerability disclosure, worth reading to understand the standard responsible disclosure process.
