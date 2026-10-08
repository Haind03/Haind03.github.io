#!/usr/bin/env python3
# solve_xor.py: pha repeating-key XOR tron goi (giong Cryptopals set 1, challenge 6)
import base64
import itertools
import sys

ENG_FREQ = {
    'a': .0817, 'b': .0150, 'c': .0278, 'd': .0425, 'e': .1270, 'f': .0223,
    'g': .0202, 'h': .0609, 'i': .0697, 'j': .0015, 'k': .0077, 'l': .0403,
    'm': .0241, 'n': .0675, 'o': .0751, 'p': .0193, 'q': .0010, 'r': .0599,
    's': .0633, 't': .0906, 'u': .0276, 'v': .0098, 'w': .0236, 'x': .0015,
    'y': .0197, 'z': .0007, ' ': .1800,
}

_LUT = [0.0] * 256
for _b in range(256):
    _ch = chr(_b).lower()
    if _ch in ENG_FREQ:
        _LUT[_b] = ENG_FREQ[_ch]
    elif not (0x20 <= _b < 0x7f):
        _LUT[_b] = -0.05

def score_english(data):
    return sum(_LUT[b] for b in data)

def hamming(a, b):
    return sum(bin(x ^ y).count("1") for x, y in zip(a, b))

def xor_repeat(data, key):
    return bytes(b ^ k for b, k in zip(data, itertools.cycle(key)))

def guess_keysizes(ct, lo=2, hi=40):
    scores = []
    for ks in range(lo, hi + 1):
        nblocks = len(ct) // ks
        if nblocks < 2:
            continue
        chunks = [ct[i*ks:(i+1)*ks] for i in range(nblocks)]
        dists = [hamming(a, b) / ks for a, b in itertools.combinations(chunks, 2)]
        scores.append((sum(dists) / len(dists), ks))
    scores.sort()
    return scores

def break_single_byte(column):
    return max(range(256), key=lambda k: score_english(bytes(b ^ k for b in column)))

def minimal_period(key):
    for p in range(1, len(key) + 1):
        if len(key) % p == 0 and key == key[:p] * (len(key) // p):
            return key[:p]
    return key

def solve(ct, try_top=3):
    candidates = [ks for _, ks in guess_keysizes(ct)[:try_top]]
    ks = min(candidates)
    columns = [ct[j::ks] for j in range(ks)]
    key = bytes(break_single_byte(col) for col in columns)
    key = minimal_period(key)
    return key, xor_repeat(ct, key)

if __name__ == "__main__":
    ct = base64.b64decode(open(sys.argv[1], "rb").read())
    key, pt = solve(ct)
    print("Do dai khoa:", len(key))
    print("Khoa       :", key)
    print("Ban ro     :")
    print(pt.decode(errors="replace"))
