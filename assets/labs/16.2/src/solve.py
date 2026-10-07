#!/usr/bin/env python3
# Solution: recognize and solve all three samples. Run: python3 solve.py

# ---------- 1. XOR multi-byte ----------
# The flag starts with "flag{" -> known plaintext to recover the key.
ct1 = bytes.fromhex("34295353293d5d460d2c416b373357462b325a5120204f")
known = b"flag{"
key_guess = bytes(ct1[i] ^ known[i] for i in range(len(known)))
# key_guess repeats: extract the real key
# Try increasing key lengths until the key repeats cleanly
def find_key(ct, known):
    raw = bytes(ct[i] ^ known[i] for i in range(len(known)))
    for klen in range(1, len(raw) + 1):
        if all(raw[i] == raw[i % klen] for i in range(len(raw))):
            return raw[:klen]
    return raw
key1 = find_key(ct1, known)
pt1 = bytes(b ^ key1[i % len(key1)] for i, b in enumerate(ct1))
print("[XOR] key =", key1, "-> plaintext =", pt1.decode())

# ---------- 2. RC4 (symmetric, you only need the key) ----------
def rc4(key, data):
    S = list(range(256)); j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xFF
        S[i], S[j] = S[j], S[i]
    out = bytearray(); i = j = 0
    for b in data:
        i = (i + 1) & 0xFF; j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        out.append(b ^ S[(S[i] + S[j]) & 0xFF])
    return bytes(out)
ct2 = bytes.fromhex("ff0e15f7a4b880dcaef6bffa2e815a19c83db06649fea703c7b292b03442d2")
# The key "s3cr3t" can be read from the binary (for example in the KSA setup code).
pt2 = rc4(b"s3cr3t", ct2)
print("[RC4] plaintext =", pt2.decode())

# ---------- 3. Base64 custom ----------
import base64
STD = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
CUSTOM = b"ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvutsrqponmlkjihgfedcba9876543210+/"
ct3 = b"AncsA6gqwCM9y78uBnUaAGB9C7UhxTssBnE9uJ=="
# Map back to the standard alphabet, then decode normally.
trans = bytes.maketrans(CUSTOM, STD)
pt3 = base64.b64decode(ct3.translate(trans))
print("[B64] plaintext =", pt3.decode())
