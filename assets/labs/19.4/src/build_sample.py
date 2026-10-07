#!/usr/bin/env python3
# Builds a FAKE (completely harmless) C2 config blob for extraction practice.
# No network connection, no harmful behavior. It is just static data.
import json, struct

# A fake config for a made-up "sample" used for learning. All of it is fake.
config = {
    "c2": ["cdn.example-fake.test", "203.0.113.45"],   # TEST-NET-3, not routable
    "port": 8443,
    "campaign": "DEMO-2024-01",
    "mutex": "Global\\FakeMwDemoMutex",
    "sleep": 60,
    "rc4_marker": "cfg",
}
plain = json.dumps(config, separators=(",", ":")).encode()

# Layer 1: XOR every byte with a 1-byte key
XOR_KEY = 0x6B
def xor(data, k):
    return bytes(b ^ k for b in data)

# Layer 2: RC4 with a string key (like real malware often does: a light XOR, then RC4)
RC4_KEY = b"s3cr3t_campaign_key"
def rc4(key, data):
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xFF
        S[i], S[j] = S[j], S[i]
    out = bytearray()
    i = j = 0
    for b in data:
        i = (i + 1) & 0xFF
        j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        out.append(b ^ S[(S[i] + S[j]) & 0xFF])
    return bytes(out)

blob = rc4(RC4_KEY, xor(plain, XOR_KEY))

# Pack it like a data section in a binary: magic + len + blob
# The magic "CFG0" helps recognize the blob when scanning a file.
packed = b"CFG0" + struct.pack("<I", len(blob)) + blob

with open("config_blob.bin", "wb") as f:
    f.write(packed)

print("Created config_blob.bin, size:", len(packed), "bytes")
print("Original plaintext (printed for comparison only, a real binary does NOT have this line):")
print(" ", plain.decode())
print("XOR key 1 byte:", hex(XOR_KEY))
print("RC4 key:", RC4_KEY.decode())
