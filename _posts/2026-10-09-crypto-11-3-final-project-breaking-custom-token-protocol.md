---
title: "Lesson 11.3: Final Project Breaking a Custom Token Protocol"
image:
  path: /assets/img/covers/crypto-11-3-final-project-breaking-custom-token-protocol.webp
  alt: "Final Project Breaking a Custom Token Protocol"
date: 2026-10-09 19:15:00 +0700
categories: ["Cryptography", "Crypto · Real-World Practice"]
tags: [cryptography, aes-ctr, bit-flipping, malleability]
render_with_liquid: false
---

This lesson wraps up the whole series. Instead of breaking a single primitive, you read a complete home-made crypto protocol (a session token system) and find where it falls apart. Real vulnerabilities are rarely in the algorithm. They are in how the pieces are combined: using ECB, a fixed nonce, no MAC, a custom RNG. The lesson gives a process to follow, a flawed sample protocol, and a working exploit that takes over the admin role and gets the flag.

![Bit-flipping a CTR token with no MAC](/assets/img/crypto/crypto-11-3-final-project-breaking-custom-token-protocol.svg)
_The attacker XORs the known bytes `guest` with `admin` into the token, and the server decrypts it as an admin role._

Part: 11 (Real-World Practice) | Time: about 120 minutes | Difficulty: hard

**Prerequisites:** Lesson 4.2 (ECB, CTR), Lesson 4.4 (CBC bit flipping, missing integrity), Lesson 4.5 (nonce reuse in stream ciphers), Lesson 5.3 (MAC). This is a synthesis lesson with no new theory, only a combination of what you have already learned.

**Tools:** Python 3 and PyCryptodome. The protocol and exploit files are in the Lab section below.

## Goals

By the end you have a process for reading a home-made protocol and narrowing down the crypto bugs. You can spot four classic design errors: ECB leaking patterns, a fixed nonce, no MAC (malleable data), and a custom RNG. You understand why encryption without integrity protection invites forgery, and you can write a bit-flipping exploit that takes admin on an AES-CTR token with no MAC.

## Theory

### The bug is in the composition, not the algorithm

AES is not broken. SHA-256 is not broken. But a system that uses AES still falls apart if it is assembled wrongly. In practice and in CTFs, most crypto bugs are design errors at the protocol level:

- Wrong mode: using ECB so identical plaintext shows through (Lesson 4.2), or using a stream mode and reusing the keystream.
- Wrong nonce or IV: fixed, predictable, or reused. Stream ciphers and CTR break as soon as the keystream repeats (Lesson 4.5).
- No integrity check: data is encrypted but has no MAC, so an attacker can modify the ciphertext without the server noticing (Lesson 4.4).
- Wrong MAC use: a loose MAC-then-encrypt, a MAC comparison that is not constant time (timing), or a MAC that leaves out an important field.
- Custom RNG: a home-made generator for tokens, nonces, or keys. It is almost always predictable (Part 9).

### Process for reading a home-made protocol

When you get a challenge with the server source, read it in this order:

1. Identify the asset. What condition guards the flag? It is usually "role == admin", "is_authenticated", or an endpoint that needs a privilege.
2. Follow the data flow. What does the client send, how does the server transform it, and what does it return? Draw it on paper if needed.
3. Find the crypto primitives. Which mode, where are the key and nonce, is there a MAC, where does the RNG come from.
4. Ask three classic questions. (a) Can the ciphertext be modified without detection (no MAC)? (b) Is any value repeated that should be unique (nonce, IV)? (c) Does the server blindly trust the data after decryption?
5. Build an attack hypothesis and test it with code. The bug usually shows up at step 4.

### Malleability: encryption is not authentication

This is the core of the sample project. Many people assume encryption makes data "impossible to modify". That is wrong. Encryption only hides the content, it does not lock it. For stream ciphers and CTR, the relation is:

```
ciphertext = plaintext XOR keystream
```

Because it is XOR, if the attacker knows (or guesses) the plaintext at some position, they can flip the ciphertext there to turn the plaintext into anything of the same length, without knowing the key:

```
ct'[i] = ct[i] XOR old[i] XOR new[i]
```

The server decrypts to `new` instead of `old`, and without a MAC to detect the modification it trusts the result. This is malleability. The only cure is integrity protection: attach a MAC (or use an AEAD such as AES-GCM) and reject every ciphertext with a wrong MAC. The rule is Encrypt-then-MAC, and check the MAC before decrypting.

## Demo

### The sample protocol and its flaws

This is a home-made session token system. The server encrypts the string `user=<name>&role=guest` with AES-CTR and gives it to the client as a token. When the client sends the token back, the server decrypts it, parses it, and returns the flag if `role=admin`.

```python
# server.py: home-made session token protocol, many design flaws
from Crypto.Cipher import AES

_KEY = b"an_example_key!!"          # secret, kept on the server
_NONCE = b"\x00" * 8                 # FLAW 1: fixed nonce for every token
FLAG = "flag{m4lle4ble_ctr_n0_m4c_equals_g4me_0ver}"

def _ctr():
    return AES.new(_KEY, AES.MODE_CTR, nonce=_NONCE)   # identical keystream every time

def issue_token(username):
    assert "&" not in username and "=" not in username  # blocks field injection, but...
    plaintext = f"user={username}&role=guest".encode()
    return _ctr().encrypt(plaintext)                     # FLAW 2: no MAC

def is_admin(token):
    data = _ctr().decrypt(token)
    try:
        fields = dict(kv.split("=", 1) for kv in data.decode().split("&"))
    except Exception:
        return False, None
    if fields.get("role") == "admin":                    # FLAW 3: blindly trusts the data after decryption
        return True, FLAG
    return False, None
```

Reading it with the process above, the asset is the flag behind the condition `role == admin`. For the flow, the client asks for a token (always role=guest), sends it back, and the server decrypts and checks the role. The primitive is AES-CTR with a fixed key, a fixed nonce, and no MAC. On the three questions, (a) there is no MAC, so the ciphertext can be changed without the server knowing, which is a hit. (b) The nonce is fixed, so the keystream repeats across tokens, another hit. (c) The server blindly trusts the role after decryption, a third hit. This protocol fails in all three places.

### The fixed nonce leaks information

Before the main exploit, here is a demo of the fixed nonce flaw. Two tokens with the same nonce share the same keystream, so XORing two ciphertexts equals XORing two plaintexts, and the parts that are the same show up:

```python
# nonce_reuse_demo.py
from server import issue_token
t1 = issue_token("alice")
t2 = issue_token("bob12")
x = bytes(a ^ b for a, b in zip(t1, t2))     # = pt1 XOR pt2
print("ct1 XOR ct2 (hex):", x.hex())
print("zero bytes in XOR :", x.count(0), "/", len(x))
```

Output:

```
ct1 XOR ct2 (hex): 000000000003030b52570000000000000000000000
zero bytes in XOR : 16 / 21
```

The zero bytes are where the two plaintexts match (`user=` at the start and `&role=guest` at the end). Only 5 bytes differ, which is the username. The repeated keystream exposed the structure. In a real challenge, this is how you confirm that the nonce is fixed and also read the plaintext layout to prepare the main attack.

### Main exploit: bit-flipping to become admin

We are only a normal user and do not know the key. But because CTR is malleable and there is no MAC, we flip the ciphertext bytes at the position of the word `guest` to turn it into `admin` (the same 5 characters, so the length does not change):

```python
# solve.py: exploit the token protocol
from server import issue_token, is_admin

def flip(ct, offset, old, new):
    out = bytearray(ct)
    for i in range(len(old)):
        out[offset + i] ^= old[i] ^ new[i]   # ct'[i] = ct[i] XOR old[i] XOR new[i]
    return bytes(out)

token = issue_token("bob")                   # request a valid token for ourselves
plain_known = b"user=bob&role=guest"         # we KNOW this plaintext structure
print("original token (hex):", token.hex())
print("current role       :", is_admin(token))

off = plain_known.index(b"guest")            # position of the word "guest"
forged = flip(token, off, b"guest", b"admin")

ok, flag = is_admin(forged)                  # send the forged token
print("forged token (hex):", forged.hex())
print("result             :", (ok, flag))
print("FLAG               :", flag)
```

Output:

```
original token (hex): 1d74ebc119606bfe3ea46ea451c325881435fe
current role       : (False, None)
forged token (hex): 1d74ebc119606bfe3ea46ea451c323991c2fe4
result             : (True, 'flag{m4lle4ble_ctr_n0_m4c_equals_g4me_0ver}')
FLAG               : flag{m4lle4ble_ctr_n0_m4c_equals_g4me_0ver}
```

The flag is `flag{m4lle4ble_ctr_n0_m4c_equals_g4me_0ver}`. The original token is guest and is rejected. We flip 5 ciphertext bytes at the position of `guest` (without touching the rest and without knowing the key), the server decrypts `role=admin` and hands over the flag. Notice that the `assert` that blocks `&` and `=` in the username only stops field injection when the token is requested. It does nothing against a later change to the ciphertext. The big lesson is that checking the input at the plaintext layer cannot replace integrity protection at the ciphertext layer.

### Fixing the protocol

To see what was missing, here is the root fix:

1. Use an AEAD instead of bare CTR: `AES.new(key, AES.MODE_GCM, nonce=...)`, with a random nonce per token sent along with it. GCM both encrypts and attaches an authentication tag.
2. When decrypting, check the tag first (GCM does this itself, and a wrong tag raises an error). A token with one bit changed breaks the tag and the server rejects it at once.
3. The nonce must be unique each time and come from a CSPRNG (`os.urandom`), never fixed.

With these three fixes the bit-flipping attack is dead, because any change to the ciphertext makes the tag wrong, and the nonce reuse flaw is gone.

## Lab (final project)

This is the capstone project. If you complete all of it, you have gone the full way from zero to breaking a real protocol.

- Part A, exploit: run `python3 solve.py` to get the flag, and `python3 nonce_reuse_demo.py` to see the nonce flaw. Read `server.py` closely and point out each flaw by line.
- Part B, patch it yourself: write `server_fixed.py` using AES-GCM with a random nonce, then run `solve.py` against it. Show that the exploit is blocked (the modified token breaks the tag and `is_admin` returns False).
- Part C, extend the attack: the sample protocol also has an ECB flaw if you switch CTR to ECB. Write a variant `server_ecb.py` that uses ECB, then do an ECB cut-and-paste to assemble blocks that form `role=admin`. Compare the two classes of flaw.
- Part D, write the writeup: following the frame from Lesson 11.2, write a full writeup for the project. Describe the protocol, list the vulnerabilities, present the exploit, and propose the patch. This is the final deliverable.
- Hints, step by step: (1) start from the question "what condition guards the flag"; (2) check whether there is a MAC, and if not think about malleability; (3) use `nonce_reuse_demo` to read the plaintext layout; (4) for bit flipping, keep the length and only change content of the same length; (5) to patch, always use Encrypt-then-MAC or an AEAD.
- Done when: you got the flag (part A), showed the patch blocks the exploit (part B), and submitted a full writeup (part D).

<div class="lab-box">
<div class="lab-head"><b>LAB 11.3</b>Download the lab files</div>
<div class="lab-files">
<a class="lab-file lab-all" href="/assets/labs-crypto/11.3.zip" download><i class="fa-solid fa-file-zipper"></i>Download all (.zip)</a>
<a class="lab-file" href="/assets/labs-crypto/11.3/nonce_reuse_demo.py" download><i class="fa-solid fa-file-code"></i>nonce_reuse_demo.py</a>
<a class="lab-file" href="/assets/labs-crypto/11.3/server.py" download><i class="fa-solid fa-file-code"></i>server.py</a>
<a class="lab-file" href="/assets/labs-crypto/11.3/solve.py" download><i class="fa-solid fa-file-code"></i>solve.py</a>
</div>
</div>

## Key takeaways

- Real crypto vulnerabilities live in the composition, not in the algorithm: ECB, a fixed nonce, no MAC, a custom RNG.
- Encryption is not authentication. CTR and stream ciphers are malleable, so knowing the plaintext lets you flip the ciphertext without the key.
- A fixed nonce repeats the keystream, and XORing two ciphertexts exposes the structure of the plaintext.
- Without a MAC the server blindly trusts a modified ciphertext. Always use Encrypt-then-MAC or an AEAD (GCM).
- Checking input at the plaintext layer cannot replace integrity protection at the ciphertext layer.
- Process for reading a protocol: find the asset, follow the data flow, inspect the primitives, ask the three questions, test the exploit.

## Common pitfalls

- Thinking that an `assert` blocking special characters in the username is enough. It only stops injection at the plaintext, and does nothing against ciphertext modification.
- Flipping bytes in a way that changes the plaintext length. Replace with a string of the same length (`guest` with 5 characters becomes `admin` with 5 characters). A different length breaks the parse.
- Flipping at the wrong offset. Count the exact position in the known plaintext. Off by one byte damages the wrong place.
- Patching by switching to a random nonce but still leaving out the MAC. A random nonce stops the reuse flaw but not malleability. Integrity protection is needed.
- Using MAC-then-encrypt or encrypt-and-MAC loosely. Prefer Encrypt-then-MAC, check the MAC before decrypting, or just use an AEAD.
- Forgetting that ECB and CTR break in different ways. ECB leaks patterns and allows block cut-and-paste, while CTR allows byte-level bit flipping. Identify the mode correctly to choose the right attack.

## Further reading

- Lesson 4.4 (CBC bit flipping) and Lesson 4.5 (nonce reuse) in this series are the direct basis for this project.
- Cryptopals set 2 (challenge 13 ECB cut-and-paste, challenge 16 CBC bit flipping) and set 3 (challenge 26 CTR bit flipping) cover exactly the attacks in this project, for more practice.
- "Cryptography Engineering" by Ferguson, Schneier, and Kohno, the chapter on modes of operation and why authentication is always needed.
- Moxie Marlinspike, "The Cryptographic Doom Principle", a short classic on why checking the MAC after decryption is a mistake.
- The whole TechCrypto series. This project is where it all comes together, so if anything is unclear, go back to that exact part.
