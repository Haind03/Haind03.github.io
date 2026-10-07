#!/usr/bin/env python3
# Config extractor: pulls the C2 config out of config_blob.bin.
# Assumes you have reversed the algorithm: RC4(key) then XOR(1 byte), so we undo it in reverse.
import json, struct, sys

XOR_KEY = 0x6B
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

def unxor(data, k):
    return bytes(b ^ k for b in data)

def extract(path):
    raw = open(path, "rb").read()
    off = raw.find(b"CFG0")
    if off < 0:
        print("Magic CFG0 not found"); return
    length = struct.unpack_from("<I", raw, off + 4)[0]
    blob = raw[off + 8: off + 8 + length]
    # Undo in reverse: RC4 first (RC4 is symmetric), then remove the XOR.
    plain = unxor(rc4(RC4_KEY, blob), XOR_KEY)
    cfg = json.loads(plain)
    print("[+] Extracted C2 config:")
    print(json.dumps(cfg, indent=2, ensure_ascii=False))
    print("\n[+] IOCs extracted:")
    for h in cfg.get("c2", []):
        print("   C2:", h)
    print("   Port:", cfg.get("port"))
    print("   Mutex:", cfg.get("mutex"))
    print("   Campaign:", cfg.get("campaign"))

if __name__ == "__main__":
    extract(sys.argv[1] if len(sys.argv) > 1 else "config_blob.bin")
