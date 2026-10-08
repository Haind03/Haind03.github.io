#!/usr/bin/env python3
# solve.py: khoi phuc private key tu ECDSA nonce reuse, roi doc flag.
import hashlib
from Crypto.Util.number import bytes_to_long, long_to_bytes

n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

def H(msg):
    return bytes_to_long(hashlib.sha256(msg).digest()) % n

def recover(m1, r, s1, m2, s2):
    z1, z2 = H(m1), H(m2)
    # Hai chu ky cung k, cung r:
    #   s1 = k^-1 (z1 + r d),  s2 = k^-1 (z2 + r d)
    #   => s1 - s2 = k^-1 (z1 - z2)  => k = (z1 - z2) / (s1 - s2) mod n
    k = (z1 - z2) * pow(s1 - s2, -1, n) % n
    #   s1 k = z1 + r d  => d = (s1 k - z1) / r mod n
    d = (s1 * k - z1) * pow(r, -1, n) % n
    return k, d

if __name__ == "__main__":
    data = eval(open("sigs.txt").read())
    assert data["r1"] == data["r2"], "r khac nhau, khong phai nonce reuse"
    k, d = recover(data["m1"], data["r1"], data["s1"], data["m2"], data["s2"])
    print("nonce k khoi phuc :", hex(k))
    print("private key d     :", hex(d))
    print("flag              :", long_to_bytes(d).decode())
