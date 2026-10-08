#!/usr/bin/env python3
# solve.py: hai tan cong cua Bai 6.3.
#   1) common modulus: cung n, hai e nguyen to cung nhau -> extended Euclid.
#   2) Hastad broadcast: cung m, cung e=3, ba modulus khac nhau -> CRT roi can bac e.
# Challenge sinh tai cho; ben tan cong khong dung bat ky d nao.
import gmpy2
from functools import reduce
from Crypto.Util.number import getPrime, bytes_to_long, long_to_bytes


def powmod_signed(base, exp, mod):
    if exp < 0:
        base = gmpy2.invert(base, mod)
        exp = -exp
    return pow(int(base), int(exp), int(mod))


def common_modulus():
    p, q = getPrime(512), getPrime(512)
    n = p * q
    flag = b"CTF{common_modulus_no_d_needed}"
    m = bytes_to_long(flag)
    e1, e2 = 3, 5                           # gcd(e1, e2) = 1
    c1, c2 = pow(m, e1, n), pow(m, e2, n)
    # tan cong
    g, a, b = gmpy2.gcdext(e1, e2)
    assert g == 1
    rec = (powmod_signed(c1, a, n) * powmod_signed(c2, b, n)) % n
    return long_to_bytes(int(rec))


def crt(residues, moduli):
    N = reduce(lambda x, y: x * y, moduli)
    total = 0
    for c, ni in zip(residues, moduli):
        Ni = N // ni
        total += c * Ni * int(gmpy2.invert(Ni, ni))
    return total % N


def hastad():
    e = 3
    flag = b"CTF{hastad_broadcast_crt_cube}"
    m = bytes_to_long(flag)
    mods, cs = [], []
    for _ in range(e):                      # can dung e ban ma
        N = getPrime(512) * getPrime(512)
        mods.append(N)
        cs.append(pow(m, e, N))
    X = crt(cs, mods)                       # = m^3 that (vi m < moi ni)
    root, exact = gmpy2.iroot(X, e)
    return exact, long_to_bytes(int(root))


def main():
    print("[1] common modulus ->", common_modulus())
    exact, m = hastad()
    print(f"[2] Hastad broadcast: can chinh xac={exact} -> {m}")


if __name__ == "__main__":
    main()
