#!/usr/bin/env python3
# solve.py: bo giai RSA da tang cho Bai 6.6, thu lan luot cac tan cong pho bien.
# Khung de gan them tang (factordb, common modulus, Hastad, shared prime, Coppersmith).
# Phan __main__ tu kiem bang ba ca sinh tai cho.
import gmpy2
from Crypto.Util.number import long_to_bytes, inverse


def fermat(n, max_steps=1_000_000):
    a = gmpy2.isqrt(n)
    if a * a < n:
        a += 1
    for _ in range(max_steps):
        b2 = a * a - n
        b, exact = gmpy2.iroot(b2, 2)
        if exact:
            return int(a - b), int(a + b)
        a += 1
    return None


def decrypt_with_pq(n, e, c, p, q):
    d = inverse(e, (p - 1) * (q - 1))
    return long_to_bytes(pow(c, d, n))


def small_e_root(n, e, c):
    for k in range(5000):
        r, exact = gmpy2.iroot(c + k * n, e)
        if exact:
            return long_to_bytes(int(r))
    return None


def cf_expansion(a, b):
    while b:
        q = a // b
        yield q
        a, b = b, a - q * b


def convergents(cf):
    n0, n1, d0, d1 = 0, 1, 1, 0
    for q in cf:
        num = q * n1 + n0
        den = q * d1 + d0
        yield num, den
        n0, n1, d0, d1 = n1, num, d1, den


def wiener(e, n):
    for k, d in convergents(cf_expansion(e, n)):
        if k == 0:
            continue
        if (e * d - 1) % k:
            continue
        phi = (e * d - 1) // k
        b = n - phi + 1
        disc = b * b - 4 * n
        if disc < 0:
            continue
        s, ok = gmpy2.iroot(disc, 2)
        if ok and (b + s) % 2 == 0:
            return int(d)
    return None


def solve(n, e, c):
    if e <= 7:
        r = small_e_root(n, e, c)
        if r:
            return ("small_e_root", r)
    if e.bit_length() > n.bit_length() - 10:
        d = wiener(e, n)
        if d:
            return ("wiener", long_to_bytes(pow(c, d, n)))
    fac = fermat(n, max_steps=200000)
    if fac:
        p, q = fac
        return ("fermat", decrypt_with_pq(n, e, c, p, q))
    return (None, None)


if __name__ == "__main__":
    from Crypto.Util.number import bytes_to_long, getPrime
    from sympy import nextprime
    # Ca A: small e = 3
    p, q = getPrime(512), getPrime(512); n = p * q; e = 3
    c = pow(bytes_to_long(b"FLAG{easy_small_e}"), e, n)
    print("A:", solve(n, e, c))
    # Ca B: Fermat (p, q gan nhau)
    p = nextprime(2**255); q = nextprime(p + 2**20); n = int(p * q); e = 65537
    c = pow(bytes_to_long(b"FLAG{fermat_me}"), e, n)
    print("B:", solve(n, e, c))
    # Ca C: Wiener (d nho)
    p, q = getPrime(512), getPrime(512); n = p * q; phi = (p - 1) * (q - 1)
    d = getPrime(80)
    while gmpy2.gcd(d, phi) != 1:
        d = getPrime(80)
    e = inverse(d, phi)
    c = pow(bytes_to_long(b"FLAG{wiener}"), e, n)
    print("C:", solve(n, e, c))
