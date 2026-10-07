#!/usr/bin/env python3
# Keygen for Level 2: reproduces the crackme's uint32 djb2 algorithm.
# Run: python3 keygen.py <username>
import sys

MASK = 0xFFFFFFFF

def serial_for(user: str) -> str:
    acc = 0x1505
    for ch in user.encode():          # ASCII/UTF-8 is fine for ordinary usernames
        acc = ((acc * 33) + ch) & MASK
    return "%08X" % acc

if __name__ == "__main__":
    user = sys.argv[1] if len(sys.argv) > 1 else "alice"
    print(f"{user} -> {serial_for(user)}")
