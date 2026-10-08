#!/usr/bin/env python3
# gen.py: sinh challenge custom-PRNG stream cipher
import os

MASK = 0xFFFFFFFF

def xorshift32(x):
    x ^= (x << 13) & MASK
    x ^= (x >> 17)
    x ^= (x << 5) & MASK
    return x & MASK

def keystream_byte(state):
    state = xorshift32(state)
    return state, (state >> 24) & 0xFF

def encrypt(pt, seed):
    state = seed
    out = bytearray()
    for b in pt:
        state, ks = keystream_byte(state)
        out.append(b ^ ks)
    return bytes(out)

if __name__ == "__main__":
    flag = b"flag{z3_cr4ck5_cu5t0m_prng_1n_0ne_sh0t}"
    seed = 0xC0FFEE42
    ct = encrypt(flag, seed)
    print("seed    =", hex(seed))
    print("ct_hex  =", ct.hex())
    with open("ct.hex", "w") as f:
        f.write(ct.hex())
