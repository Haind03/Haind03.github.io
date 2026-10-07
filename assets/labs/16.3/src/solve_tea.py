#!/usr/bin/env python3
"""
solve_tea.py - reverses TEA to recover the password of tea_lock.c

After reversing: the algorithm is TEA (recognized through the delta 0x9E3779B9),
key = {0x11223344, 0x55667788, 0x9ABCDEF0, 0x0F1E2D3C},
expected ciphertext = (0xBBAAD475, 0x2E138704).

TEA is symmetric, so decrypting means running 32 rounds backward, subtracting delta instead of adding it.
"""
import struct

DELTA = 0x9E3779B9
MASK = 0xFFFFFFFF
KEY = [0x11223344, 0x55667788, 0x9ABCDEF0, 0x0F1E2D3C]
CIPHER = (0xBBAAD475, 0x2E138704)


def tea_decipher(v0, v1, k):
    s = (DELTA * 32) & MASK
    for _ in range(32):
        v1 = (v1 - (((v0 << 4) + k[2]) ^ (v0 + s) ^ ((v0 >> 5) + k[3]))) & MASK
        v0 = (v0 - (((v1 << 4) + k[0]) ^ (v1 + s) ^ ((v1 >> 5) + k[1]))) & MASK
        s = (s - DELTA) & MASK
    return v0, v1


if __name__ == "__main__":
    v0, v1 = tea_decipher(CIPHER[0], CIPHER[1], KEY)
    pw = struct.pack("<II", v0, v1)
    print("Password:", pw.decode("latin1"))
