#!/usr/bin/env python3
# Generates three encrypted samples: multi-byte XOR, RC4, and custom Base64.
# Run: python3 make_data.py   (prints three hex/text strings for the learner to solve)

# ---------- 1. XOR multi-byte (rolling key) ----------
def xor_enc(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

flag1 = b"flag{xor_is_everywhere}"
key1 = b"RE24"
ct1 = xor_enc(flag1, key1)

# ---------- 2. RC4 ----------
def rc4(key: bytes, data: bytes) -> bytes:
    S = list(range(256))
    j = 0
    for i in range(256):                 # KSA
        j = (j + S[i] + key[i % len(key)]) & 0xFF
        S[i], S[j] = S[j], S[i]
    out = bytearray()
    i = j = 0
    for b in data:                       # PRGA
        i = (i + 1) & 0xFF
        j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        k = S[(S[i] + S[j]) & 0xFF]
        out.append(b ^ k)
    return bytes(out)

flag2 = b"flag{rc4_has_no_magic_constant}"
key2 = b"s3cr3t"
ct2 = rc4(key2, flag2)

# ---------- 3. Base64 with a shuffled alphabet ----------
import base64
STD = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
CUSTOM = b"ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvutsrqponmlkjihgfedcba9876543210+/"
flag3 = b"flag{custom_base64_alphabet}"
std_b64 = base64.b64encode(flag3)
trans = bytes.maketrans(STD, CUSTOM)
ct3 = std_b64.translate(trans)

if __name__ == "__main__":
    print("XOR ciphertext (hex):", ct1.hex())
    print("RC4 ciphertext (hex):", ct2.hex())
    print("Custom-Base64 ciphertext:", ct3.decode())
