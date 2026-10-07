#!/usr/bin/env python3
"""
keygen.py  -  Lab 3.6: reference keygen (solution)

Generates a valid serial for any username, based on the algorithm read
from the validate() function in keygenme.c.

Usage:
    python3 keygen.py <username>
Example:
    python3 keygen.py alice
"""
import sys

# Copied as is from the SEED array in keygenme.c
SEED = [0x1337, 0xBEEF, 0xCAFE, 0x5A5A]


def make_serial(user: str) -> str:
    blocks = []
    for k in range(4):
        acc = SEED[k]
        for i, ch in enumerate(user):
            acc += (ord(ch) + 1) * (i + 1 + k)
        blocks.append(acc & 0xFFFF)
    # Format: 4 hex blocks of 4 digits, separated by '-'
    return "-".join(f"{b:04X}" for b in blocks)


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <username>")
        sys.exit(1)
    user = sys.argv[1]
    print(make_serial(user))


if __name__ == "__main__":
    main()
