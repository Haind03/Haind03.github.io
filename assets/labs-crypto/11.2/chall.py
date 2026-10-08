#!/usr/bin/env python3
# chall.py: "server" ECDSA tren secp256k1. Loi: dung LAI cung mot nonce k cho hai chu ky.
import hashlib
from Crypto.Util.number import bytes_to_long

# --- Tham so secp256k1 ---
p  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
a, b = 0, 7
Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
n  = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G  = (Gx, Gy)

def inv(x, m): return pow(x, -1, m)

def point_add(P, Q):
    if P is None: return Q
    if Q is None: return P
    if P[0] == Q[0] and (P[1] + Q[1]) % p == 0: return None
    if P == Q:
        lam = (3 * P[0] * P[0] + a) * inv(2 * P[1], p) % p
    else:
        lam = (Q[1] - P[1]) * inv(Q[0] - P[0], p) % p
    x = (lam * lam - P[0] - Q[0]) % p
    y = (lam * (P[0] - x) - P[1]) % p
    return (x, y)

def scalar_mul(k, P):
    R, Q = None, P
    while k:
        if k & 1: R = point_add(R, Q)
        Q = point_add(Q, Q)
        k >>= 1
    return R

def H(msg):
    return bytes_to_long(hashlib.sha256(msg).digest()) % n

def sign(msg, d, k):
    z = H(msg)
    R = scalar_mul(k, G)
    r = R[0] % n
    s = inv(k, n) * (z + r * d) % n
    return r, s

if __name__ == "__main__":
    # Khoa bi mat = flag ma hoa thanh so (flag ngan de d < n)
    flag = b"flag{ecdsa_k_reu5e!}"
    d = bytes_to_long(flag)
    assert d < n
    Pub = scalar_mul(d, G)                 # khoa cong khai, cong bo duoc

    m1 = b"transfer 10 coins to alice"
    m2 = b"transfer 99 coins to mallory"
    k = 0x1337C0DEBEEF1337C0DEBEEF1337C0DEBEEF  # BUG: nonce co dinh, dung lai
    r1, s1 = sign(m1, d, k)
    r2, s2 = sign(m2, d, k)

    print("# public key Pub:")
    print("Pub_x =", hex(Pub[0]))
    print("Pub_y =", hex(Pub[1]))
    print("# hai chu ky (chu y r1 == r2, dau hieu chet nguoi):")
    print("m1 =", m1); print("r1 =", hex(r1)); print("s1 =", hex(s1))
    print("m2 =", m2); print("r2 =", hex(r2)); print("s2 =", hex(s2))
    print("r1 == r2 ?", r1 == r2)
    # luu ra file cho solver
    with open("sigs.txt", "w") as f:
        f.write(repr({"Pub": Pub, "m1": m1, "r1": r1, "s1": s1,
                      "m2": m2, "r2": r2, "s2": s2}))
