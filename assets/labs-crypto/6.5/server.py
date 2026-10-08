#!/usr/bin/env python3
# server.py: "nan nhan" cho Bai 6.5. Sinh khoa RSA nho (256 bit cho nhanh), ma flag
# bang PKCS#1 v1.5, va cung cap mot padding oracle chi tra ve yes/no.
# Ben tan cong (solve.py) chi duoc dung: n, e, k, c_target, oracle(). KHONG dung d.
import os
from Crypto.Util.number import getPrime, inverse, bytes_to_long, long_to_bytes

BITS = 256                                  # khoa nho de demo chay trong ~15-20s


def _gen():
    p = getPrime(BITS // 2)
    q = getPrime(BITS // 2)
    n = p * q
    while n.bit_length() != BITS:
        p = getPrime(BITS // 2)
        q = getPrime(BITS // 2)
        n = p * q
    e = 65537
    d = inverse(e, (p - 1) * (q - 1))
    return n, e, d


_n, _e, _d = _gen()
n, e = _n, _e
k = (n.bit_length() + 7) // 8               # so byte cua n


def pkcs15_pad(msg):
    ps_len = k - 3 - len(msg)
    assert ps_len >= 8, "thong diep qua dai cho PKCS#1 v1.5"
    ps = bytes(b or 1 for b in os.urandom(ps_len))
    return b"\x00\x02" + ps + b"\x00" + msg


def oracle(ct):
    # chi tra ve mot bit: hai byte dau co phai 00 02 khong
    em = long_to_bytes(pow(ct, _d, n), k)
    return em[0] == 0 and em[1] == 2


FLAG = b"flag{pkcs1_v15_bb}"
c_target = pow(bytes_to_long(pkcs15_pad(FLAG)), e, n)
