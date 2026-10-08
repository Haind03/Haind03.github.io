#!/usr/bin/env python3
# solve.py: Pohlig-Hellman tren EC khi bac nhom tron (smooth). Giai ECDLP -> decrypt flag.
# Tu chua. Yeu cau: pip install pycryptodome sympy
import math
import hashlib
from sympy import factorint
from Crypto.Cipher import AES

# ===== De bai: curve y^2 = x^3 + a*x + b mod p, bac nhom N =====
p, a, b = 10007, 3, 5
N = 10125                       # bac nhom = 3^4 * 5^3 (tron)
G = (1, 3)                      # base point
P = (5324, 8290)               # P = secret * G, can tim secret
ct  = bytes.fromhex("6ccea18b3c9363f1cba54e7da37fbbe2cf9f243231513ce398a30da278")
tag = bytes.fromhex("386000aa8e2359767ec48e6e732dbe70")

INF = None
def add(A, B):
    if A is INF: return B
    if B is INF: return A
    x1, y1 = A; x2, y2 = B
    if x1 == x2 and (y1 + y2) % p == 0: return INF
    if A == B:
        m = (3 * x1 * x1 + a) * pow(2 * y1, -1, p) % p
    else:
        m = (y2 - y1) * pow(x2 - x1, -1, p) % p
    x3 = (m * m - x1 - x2) % p
    y3 = (m * (x1 - x3) - y1) % p
    return (x3, y3)

def mul(k, A):
    R = INF; Q = A
    while k:
        if k & 1: R = add(R, Q)
        Q = add(Q, Q); k >>= 1
    return R

def neg(A):
    return INF if A is INF else (A[0], (-A[1]) % p)

def bsgs_ec(base, target, order):
    # k trong [0, order): k*base = target, baby-step giant-step tren EC
    m = math.isqrt(order) + 1
    table = {}
    cur = INF
    for j in range(m):
        table.setdefault(cur, j)
        cur = add(cur, base)
    step = neg(mul(m, base))
    gamma = target
    for i in range(m):
        if gamma in table:
            return i * m + table[gamma]
        gamma = add(gamma, step)
    return None

def crt(res, mod):
    from math import prod
    M = prod(mod); x = 0
    for r, n in zip(res, mod):
        Mi = M // n
        x += r * Mi * pow(Mi, -1, n)
    return x % M

def pohlig_hellman_ec(G, P, order):
    res, mod = [], []
    for q, e in factorint(order).items():
        qe = q ** e
        Gi = mul(order // qe, G)       # bac q^e
        Pi = mul(order // qe, P)
        res.append(bsgs_ec(Gi, Pi, qe))
        mod.append(qe)
    return crt(res, mod)

if __name__ == "__main__":
    print("[*] N =", N, "factor =", dict(factorint(N)))
    secret = pohlig_hellman_ec(G, P, N)
    print("[*] secret =", secret, "| kiem:", mul(secret, G) == P)
    key = hashlib.sha256(str(secret).encode()).digest()
    c = AES.new(key, AES.MODE_GCM, nonce=b"labnonce8x3!")
    flag = c.decrypt_and_verify(ct, tag)
    print("[+] flag =", flag.decode())
