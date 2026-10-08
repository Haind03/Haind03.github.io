#!/usr/bin/env python3
# solve.py: ba lo tham so yeu cua Bai 6.2.
#   1) small e=3 khong padding -> can bac ba.
#   2) p, q gan nhau -> Fermat factorization.
#   3) n nho -> factordb (co mang) hoac sympy.factorint (offline).
# Cac challenge duoc sinh tai cho de tai lap duoc; ben "tan cong" chi dung (n, e, c).
import gmpy2
from Crypto.Util.number import bytes_to_long, long_to_bytes, inverse
from sympy import nextprime, factorint


# ---------- 1) small e cube root ----------
def challenge_small_e():
    e = 3
    p = int(nextprime(2 ** 511))
    q = int(nextprime(2 ** 512))           # n ~ 1024 bit, co dinh
    n = p * q
    flag = b"CTF{sm4ll_e_m3ans_cub3_r00t}"
    c = pow(bytes_to_long(flag), e, n)
    # tan cong: m^3 < n nen c = m^3 tren so nguyen
    root, exact = gmpy2.iroot(c, 3)
    return exact, long_to_bytes(int(root))


# ---------- 2) Fermat ----------
def fermat(n, max_steps=1_000_000):
    a = gmpy2.isqrt(n)
    if a * a < n:
        a += 1
    for s in range(max_steps):
        b2 = a * a - n
        b, exact = gmpy2.iroot(b2, 2)
        if exact:
            return int(a - b), int(a + b), s
        a += 1
    return None


def challenge_fermat():
    p = int(nextprime(2 ** 1024))
    q = int(nextprime(p + 2 ** 20))        # q = nextprime gan p -> p, q gan nhau
    n = p * q
    e = 65537
    flag = b"CTF{q_is_nextprime_of_p_oops}"
    c = pow(bytes_to_long(flag), e, n)
    fp, fq, steps = fermat(n)
    d = inverse(e, (fp - 1) * (fq - 1))
    return steps, long_to_bytes(pow(c, d, n))


# ---------- 3) factordb / small n ----------
def factordb(n, timeout=6):
    try:
        import urllib.request
        import json
        r = urllib.request.urlopen(
            "http://factordb.com/api?query=" + str(n), timeout=timeout)
        data = json.loads(r.read())
        factors = []
        for f, mult in data.get("factors", []):
            factors.extend([int(f)] * int(mult))
        if len(factors) >= 2:
            return "factordb", factors
    except Exception:
        pass
    fac = factorint(n)
    factors = []
    for f, mult in fac.items():
        factors.extend([int(f)] * int(mult))
    return "sympy.factorint", factors


def challenge_factordb():
    n = 1000036000099                      # = 1000003 * 1000033 (vi du trong bai)
    src, factors = factordb(n)
    p, q = factors[0], factors[1]
    flag = f"CTF{{factordb_{p}_x_{q}}}".encode()
    return src, flag


def main():
    exact, m = challenge_small_e()
    print(f"[1] small e cube root: exact={exact} -> {m}")
    steps, m = challenge_fermat()
    print(f"[2] Fermat: sau {steps} buoc -> {m}")
    src, flag = challenge_factordb()
    print(f"[3] factor n nho qua {src} -> {flag}")


if __name__ == "__main__":
    main()
