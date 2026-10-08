#!/usr/bin/env python3
# solve.py: Bleichenbacher padding oracle attack cho Bai 6.5.
# Chi dung n, e, k, c_target, oracle() tu server. KHONG dung private key.
# Khoa 256 bit (trong server.py) chay trong khoang 15-20 giay, vai tram nghin truy van.
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import server
from Crypto.Util.number import long_to_bytes

n, e, k = server.n, server.e, server.k
B = 2 ** (8 * (k - 2))

_calls = [0]


def oracle(c):
    _calls[0] += 1
    return server.oracle(c)


def ceildiv(a, b):
    return -(-a // b)


def attack(c):
    # Buoc 1: tim s dau tien lam oracle noi yes
    s = ceildiv(n, 3 * B)
    while not oracle((c * pow(s, e, n)) % n):
        s += 1
    M = [(2 * B, 3 * B - 1)]
    s_i = s
    while True:
        if len(M) > 1:
            s_i += 1
            while not oracle((c * pow(s_i, e, n)) % n):
                s_i += 1
        else:
            a, b = M[0]
            r = ceildiv(2 * (b * s_i - 2 * B), n)
            found = False
            while not found:
                s_lo = ceildiv(2 * B + r * n, b)
                s_hi = (3 * B + r * n) // a
                s_i = s_lo
                while s_i <= s_hi:
                    if oracle((c * pow(s_i, e, n)) % n):
                        found = True
                        break
                    s_i += 1
                if not found:
                    r += 1
        newM = set()
        for (a, b) in M:
            r_lo = ceildiv(a * s_i - 3 * B + 1, n)
            r_hi = (b * s_i - 2 * B) // n
            for r in range(r_lo, r_hi + 1):
                na = max(a, ceildiv(2 * B + r * n, s_i))
                nb = min(b, (3 * B - 1 + r * n) // s_i)
                if na <= nb:
                    newM.add((na, nb))
        M = list(newM)
        if len(M) == 1 and M[0][0] == M[0][1]:
            return M[0][0]


def main():
    t0 = time.time()
    m = attack(server.c_target)
    dt = time.time() - t0
    em = long_to_bytes(m, k)
    # tach thong diep: sau byte 00 phan cach dau tien (ke tu index 2)
    sep = em.index(b"\x00", 2)
    flag = em[sep + 1:]
    print("EM (hex)   :", em.hex())
    print("FLAG       :", flag)
    print(f"oracle calls: {_calls[0]}  time: {dt:.2f}s  (khoa {server.BITS} bit)")


if __name__ == "__main__":
    main()
