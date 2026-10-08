#!/usr/bin/env python3
# solve.py: pha discrete log cho DH co p-1 tron (smooth) bang Pohlig-Hellman.
# Khoa bi mat a chinh la flag o dang so. Khoi phuc a -> doi ra bytes -> flag.
# Tu chua, chi can: python3 solve.py   (yeu cau: pip install sympy)
import math
from sympy import factorint, isprime

# ====== De bai (public) ======
p = 7962994002710200590936746770260937501
g = 24
A = 1019641922916465058952932203248509729   # A = g^a mod p, a la khoa bi mat

def bsgs(base, target, p, order):
    # discrete log trong nhom con bac nho `order`: tim x sao cho base^x = target
    m = math.isqrt(order) + 1
    table = {}
    e = 1
    for j in range(m):
        table.setdefault(e, j)
        e = (e * base) % p
    step = pow(base, m * (p - 2), p)   # base^(-m) mod p (p nguyen to)
    gamma = target
    for i in range(m):
        if gamma in table:
            return i * m + table[gamma]
        gamma = (gamma * step) % p
    return None

def crt(residues, moduli):
    from math import prod
    N = prod(moduli)
    x = 0
    for r, n in zip(residues, moduli):
        Ni = N // n
        x += r * Ni * pow(Ni, -1, n)
    return x % N

def pohlig_hellman(g, h, p, order):
    # giai dlog theo tung luy thua nguyen to q^e cua `order`, roi ghep bang CRT
    residues, moduli = [], []
    for q, e in factorint(order).items():
        qe = q ** e
        gi = pow(g, order // qe, p)
        hi = pow(h, order // qe, p)
        x = 0
        gamma = pow(gi, q ** (e - 1), p)       # phan tu bac q
        gi_inv = pow(gi, -1, p)
        for k in range(e):
            hk = (hi * pow(gi_inv, x, p)) % p
            hk = pow(hk, q ** (e - 1 - k), p)
            d = bsgs(gamma, hk, p, q)           # chu so trong [0, q)
            x += d * (q ** k)
        residues.append(x % qe)
        moduli.append(qe)
    return crt(residues, moduli)

def long_to_bytes(n):
    return n.to_bytes((n.bit_length() + 7) // 8, "big")

if __name__ == "__main__":
    assert isprime(p)
    order = p - 1
    print("[*] p-1 =", factorint(order))
    a = pohlig_hellman(g, A, p, order)
    print("[*] khoi phuc a =", a)
    assert pow(g, a, p) == A, "dlog sai"
    print("[+] flag =", long_to_bytes(a).decode())
