---
title: "Lesson 3.2: One-Time Pad and Key Reuse"
image:
  path: /assets/img/covers/crypto-3-2-one-time-pad-key-reuse.webp
  alt: "One-Time Pad and Key Reuse"
date: 2023-04-15 01:17:00 +0700
categories: ["Cryptography", "Crypto · XOR and OTP"]
tags: [cryptography, otp, xor, two-time-pad, nonce-reuse]
render_with_liquid: false
---

OTP (one-time pad) is the only cipher proven to be perfectly secure. This lesson explains the intuition for why it cannot be broken, the three conditions that must hold for that promise to stay valid, and why a single key reuse (a two-time pad) collapses the whole scheme. It includes a demo that recovers two plaintexts from two ciphertexts.

![Two ciphertexts under one key: XOR cancels the key and leaves p1 xor p2](/assets/img/crypto/crypto-3-2-one-time-pad-key-reuse.svg)
_Reusing a key makes c1 xor c2 equal to p1 xor p2, which crib dragging can pull apart._

Level: medium, about 35 minutes. Prerequisite: Lesson 3.1 (XOR, crib dragging). The whole lesson stands on the property `a xor a = 0`. Tools: Python 3 with the standard library, and the `secrets` module for secure random keys.

## Goals

You will state OTP and its three conditions for perfect security. You will explain the intuition of perfect secrecy without heavy math. You will see why OTP is nearly useless in practice even though it is perfectly secure. You will build the two-time pad attack yourself: from two ciphertexts under the same key, recover both plaintexts. You will also recognize that nonce reuse in a stream cipher (CTR, ChaCha20) is a two-time pad in disguise.

## Theory

### What OTP is

OTP takes a truly random key k, exactly as long as the plaintext, and XORs it:

```
c = p xor k        # encrypt
p = c xor k        # decrypt
```

This sounds identical to repeating-key XOR from Lesson 3.1. The critical difference is the key. With OTP the key is fully random, as long as the message, and used exactly once. Those three conditions are what turn a trivial XOR into an unbreakable cipher.

### Perfect secrecy: the intuition

Shannon proved in 1949 that OTP has perfect secrecy, meaning the ciphertext leaks no information about the plaintext. More precisely, the probability that a given plaintext is the original, after seeing the ciphertext, is exactly its probability before seeing it. The ciphertext is useless to the attacker.

The intuition needs no formula. Suppose the ciphertext is the 8 bits `11010010`. The attacker wants the plaintext. For any 8-bit plaintext he guesses, there is exactly one 8-bit key that turns that plaintext into this ciphertext (the key is `c xor p`). Is the plaintext `00000000`? The key `11010010` fits. Is it some other 8-bit message? Exactly one key fits that as well. Because the key is uniformly random, every key is equally likely, so every plaintext is equally likely. The ciphertext does not favor any plaintext. It says nothing.

This is a real difference from every other cipher. AES and RSA are secure only because the attacker cannot do enough computation (computational security). OTP is secure even against an attacker with unlimited computing power (information-theoretic security). Searching all keys only produces every possible plaintext, with no way to tell which one is real.

### Why OTP is useless in practice

It is perfectly secure, so why does nobody use it? Because the three conditions are very expensive:

- The key is as long as the message. To send 1 GB securely you must already have 1 GB of key. But if you can already move 1 GB of secret key securely, you could just move the message.
- The key must be truly random. Using a PRNG (pseudo-random number generator) to produce the key breaks the promise. Security is then only as strong as the difficulty of predicting the PRNG, and it is no longer absolute. That is a stream cipher, not OTP.
- The key is used only once. This is the condition violated most often, and it is the rest of this lesson.

So OTP appears only where absolute security is worth more than the inconvenience, such as diplomatic lines and Cold War spies with paper key pads. In CTFs, OTP appears almost always as someone breaking one of the three conditions.

### Two-time pad: reusing the key is fatal

Suppose someone is lazy and uses the same key k for two messages:

```
c1 = p1 xor k
c2 = p2 xor k
```

The attacker XORs the two ciphertexts together. The key cancels (thanks to `k xor k = 0`):

```
c1 xor c2 = (p1 xor k) xor (p2 xor k) = p1 xor p2
```

The key disappears completely. The attacker now holds `p1 xor p2`, the XOR of the two plaintexts, with no key involved. This is the crib dragging problem from Lesson 3.1, but easier because both sides are now human-language plaintext.

To exploit this, guess a common word in p1 (for example `the `, `flag{`) and XOR it into `p1 xor p2` at some position. If the guess is right, the result is the matching piece of p2. If p2 reads as words, you have just recovered a piece of both messages at once, because the piece of p1 is the crib you guessed and the piece of p2 just appeared. Keep extending both messages in turn, and each readable piece suggests the next one. This works because natural language has redundancy.

With more messages (three or four ciphertexts under the same key) it gets easier and almost automatic, using the space character trick. In English text the space is very common, and XORing a letter with a space (0x20) only flips the 6th bit, turning uppercase into lowercase and the reverse. Look at each column: where XORing two ciphertexts gives an ASCII letter, one of the two plaintexts there is likely a space, and from that you can derive the keystream at that column.

### Nonce reuse: the same disease

Do not think "I am not using OTP." Every stream cipher (RC4, ChaCha20) and the CTR mode of a block cipher works like OTP: it generates a keystream from (key, nonce) and XORs. The keystream is only safe as long as each (key, nonce) is used exactly once. A nonce (number used once) that repeats under the same key produces exactly the same keystream, and two ciphertexts under the same keystream are a two-time pad. The whole attack above applies unchanged. This is one of the most common real-world mistakes, and it comes back in Part 4 (CTR nonce reuse) and Part 8 (ECDSA nonce reuse, which is worse because it leaks the private key).

### Three questions to answer

1. What does correct use look like: a truly random key, as long as the message, used once, and the ciphertext leaks nothing.
2. Where does it fail: key reuse, or a PRNG instead of true randomness, or a key shorter than the message that then repeats.
3. How is it exploited: XOR two ciphertexts to remove the key, then crib dragging or the space trick to recover both plaintexts in parallel.

## Demo

### OTP done right: nothing leaks

```python
# otp_correct.py: OTP with a truly random key, as long as the message, used once
import secrets

def otp(data, key):
    return bytes(a ^ b for a, b in zip(data, key))

msg = b"attack at dawn"
key = secrets.token_bytes(len(msg))   # secure random key, EXACTLY as long as the message
ct = otp(msg, key)
print("Ciphertext:", ct.hex())
print("Decrypted :", otp(ct, key).decode())

# Demonstrate perfect secrecy: for EVERY plaintext we guess (same length), exactly one key matches ct
guess = b"defend the gap"           # another plaintext, EXACTLY as long as msg (14 bytes)
fake_key = otp(ct, guess)           # a fake key that turns 'guess' into exactly this ct
print("Ct from guess + fake_key:", otp(guess, fake_key).hex())
print("Matches the real ct?    :", otp(guess, fake_key) == ct)
```

Output (the ciphertext and key change on every run because they are random):

```
Ciphertext: 7e1c... (different on every run)
Decrypted : attack at dawn
Ct from guess + fake_key: 7e1c... (matches the real ct)
Matches the real ct?    : True
```

The last lines show perfect secrecy in a nutshell. For that ciphertext, the plaintext `defend the gap` also fits perfectly under a different key. The attacker has no way to know whether it was really `attack at dawn` or `defend the gap`, and every plaintext of the same length is equally possible. Note the condition "same length": OTP still reveals the message length. It only hides the content.

### Two-time pad: recover two plaintexts from two ciphertexts

```python
# two_time_pad.py: key reuse -> break with crib dragging
import secrets
import string

GOOD = set((string.ascii_letters + " ").encode())   # strict filter: letters and spaces only

def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))

p1 = b"the launch code is alpha nine zero"
p2 = b"meet me behind the old oak at seven"
key = secrets.token_bytes(max(len(p1), len(p2)))   # BUG: one key used for both

c1 = xor(p1, key)
c2 = xor(p2, key)

# The attacker only has c1, c2. XOR them together and the key cancels
combined = xor(c1, c2)             # = p1 xor p2

# Crib dragging: guess a word in p1, drag it along 'combined', see whether the p2 that appears is readable
def drag(combined, crib):
    crib = crib.encode()
    for i in range(len(combined) - len(crib) + 1):
        out = xor(combined[i:i+len(crib)], crib)
        if all(b in GOOD for b in out):           # keep only positions that give all letters + space
            print(f"  pos {i:2d}: if p1 has '{crib.decode()}' then p2 has '{out.decode()}'")

print("Try the short crib 'the ' (noisy):")
drag(combined, "the ")
print("Try the long crib 'launch ' (cleaner):")
drag(combined, "launch ")
```

Output:

```
Try the short crib 'the ' (noisy):
  pos  0: if p1 has 'the ' then p2 has 'meet'
  pos 12: if p1 has 'the ' then p2 has 'uh t'
  pos 15: if p1 has 'the ' then p2 has ' is '
  pos 17: if p1 has 'the ' then p2 has 'bhk '
  pos 19: if p1 has 'the ' then p2 has 'zhqh'
  pos 28: if p1 has 'the ' then p2 has 'ehl '
Try the long crib 'launch ' (cleaner):
  pos  4: if p1 has 'launch ' then p2 has ' me beh'
```

Read the result by the crib dragging lesson. The short crib `the ` gives many positions that pass the filter, most of them noise (`uh t`, `bhk `, `zhqh`), but position 0 gives `meet`, which looks like English. The longer crib `launch ` leaves only one position: pos 4 reveals ` me beh`, which immediately suggests the word `behind`. The lesson is that the longer and more distinctive the crib, the fewer false alarms. From ` me beh` you extend the crib `me behind` back into p1, which reveals more of p1, and you alternate until both plaintexts are rebuilt. You never need to know the key.

### The space trick with many ciphertexts

```python
# space_trick.py: many messages under one key -> derive the keystream with the space trick
import secrets

msgs = [
    b"the quick brown fox jumps over the lazy dog while",
    b"we attack the eastern gate exactly at midnight so",
    b"please remember to bring the keys and the papers ",
    b"cryptography is the study of secure communication",
    b"never reuse a one time pad key or everything fails",
    b"the meeting has been moved to the second basement",
    b"send reinforcements we are going to advance south",
    b"all your secrets are belong to statistics and xor",
    b"a stream cipher is just a fancy keystream over xor",
    b"keep the plaintext short and the key truly random ",
    b"the password for the vault is written on the wall",
    b"do not trust any channel that you cannot verify ok",
]
L = min(len(m) for m in msgs)
msgs = [m[:L] for m in msgs]
key = secrets.token_bytes(L)                 # BUG: one shared key for all
cts = [bytes(a ^ b for a, b in zip(m, key)) for m in msgs]

def recover_keystream(cts):
    n = min(len(c) for c in cts)
    ks = bytearray(n)
    for col in range(n):
        best_k, best_score = 0, -10**9
        for i in range(len(cts)):
            cand = cts[i][col] ^ 0x20        # assume message i has a space at this column
            score = 0
            for c in cts:
                p = c[col] ^ cand            # decrypt every message at this column under that assumption
                if p == 0x20 or (65 <= p <= 90) or (97 <= p <= 122):
                    score += 1               # a letter or space came out: a sign of a hit
                elif not (0x20 <= p < 0x7f):
                    score -= 1               # a control byte came out: penalty
            if score > best_score:
                best_score, best_k = score, cand
        ks[col] = best_k
    return bytes(ks)

rk = recover_keystream(cts)
for c in cts:
    print(bytes(a ^ b for a, b in zip(c, rk)).decode(errors="replace"))
```

Output (the wrong cells change on every run because the key is random, while the readable part is stable):

```
 he qui1k 'row  fox jumps over the laz  dog while
#e atta1k 1he +astern gate exactly at 4idnight so
$lease  em mbe< to bring the keys and -he papers 
7ryptog ap-y i= the study of secure co4munication
:ever r7us  a !ne time pad key or ever thing fail
 he mee&in" ha= been moved to the seco7d basement
...
```

The idea is that the space (0x20) is the most common character in English text, and XORing a letter with 0x20 only flips the 6th bit and gives a letter again (case swap). At each column we assume each message in turn has a space, derive the matching keystream byte, and decrypt every message at that column. A correct assumption (the other message really has a space there) makes most of the other messages come out as letters, so it gets the highest score. With about a dozen messages most columns are recovered correctly, and only a few columns fail where no message has a space there. Those cells are guessed from context. This is the automated version of crib dragging, and it is also how real-world nonce reuse is broken.

## Lab

- Task: you get two hex ciphertexts. They are two English sentences encrypted with OTP but using the same key. Recover both plaintexts. One of the two sentences contains a flag in the form `flag{...}`.
- To build the challenge yourself: choose p1 with an embedded flag, p2 as another English sentence, generate a random key with `secrets.token_bytes`, and print `c1.hex()` and `c2.hex()`. Then solve it again from those two hex strings only.
- Provided files: save the generated hex strings in files of your own if you want to keep them.
- Hint 1: XOR the two ciphertexts first to remove the key, which gives `p1 xor p2`.
- Hint 2: the crib `flag{` is very valuable. Drag it along `p1 xor p2`. The position where the other side comes out as readable text is the flag position.
- Hint 3: each readable piece of one message is a crib for the other. Extend back and forth a few characters at a time.
- Done when: you rebuild both plaintexts completely and read the flag.

As an extension, find a nonce-reuse challenge (for example AES-CTR with a reused nonce) on CryptoHack or picoCTF. Collect several ciphertexts under the same keystream and apply `space_trick.py` to recover them. This shows that OTP and CTR nonce reuse are the same problem.

## Key takeaways

- OTP is perfectly secure (information-theoretic), not only hard to compute against.
- Three vital conditions: a truly random key, as long as the message, used exactly once.
- Perfect secrecy: every plaintext of the same length is equally possible given a ciphertext.
- Reusing a key makes the key cancel when you XOR two ciphertexts: `c1 xor c2 = p1 xor p2`.
- Recover with crib dragging or the space trick, without knowing the key.
- Nonce reuse in stream ciphers and CTR is a two-time pad in disguise, with the same attack.

## Common pitfalls

- Thinking repeating-key XOR is OTP. A repeating key, or a key shorter than the message, is no longer OTP. It is a weak stream cipher, breakable as in Lesson 3.1.
- Using an ordinary PRNG (for example Python's `random`, a Mersenne Twister) to produce an OTP key. Security is then only as strong as the difficulty of predicting the PRNG, and the absolute guarantee is lost. Use `secrets` or `os.urandom` when you need cryptographic randomness.
- Reusing the key "just once for convenience". One time is enough to be broken: two messages leak `p1 xor p2`.
- Forgetting that nonce reuse is also key reuse. The same (key, nonce) gives the same keystream, with the same disaster.
- Giving up on crib dragging too early. Many positions giving garbage is normal. Filter for "all printable characters" and extend the crib back and forth patiently.
- Mixing up lengths: when two messages differ in length, `c1 xor c2` is only valid up to the shorter length, and the tail of the longer message still carries the key.

## Further reading

- Shannon, Communication Theory of Secrecy Systems (1949): the original proof of perfect secrecy, worth reading for the roots.
- Cryptopals set 1 challenge 6 and set 3 challenges 19 and 20 (break fixed-nonce CTR): these are the two-time pad attack at the scale of many messages.
- CryptoHack, XOR and Symmetric sections, the nonce reuse challenges.
- The history of the VENONA project: the US broke Soviet cables because OTP pages were reused, an expensive real-world example.
- Continue with Lesson 3.3: a combined lab that breaks repeating-key XOR in Cryptopals style, where you assemble everything from Part 3 into one complete solve script.
