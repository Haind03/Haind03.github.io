#!/usr/bin/env python3
# Keygen for level3: recreates the gen() algorithm and prints an 8-character hex serial.
import sys

def gen(name: str) -> int:
    acc = 0x1337
    for ch in name.encode():
        acc = (acc * 33 + ch) & 0xFFFFFFFF
    acc ^= 0xC0FFEE
    return acc & 0xFFFFFFFF

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "reverser"
    print("%08X" % gen(name))
