#!/usr/bin/env python3
# solve.py: length extension attack tren SHA-256, tu chua (chi dung stdlib).
#
# Kich ban: server ky cookie bang tag = SHA256(secret || data).
# Ke tan cong biet data, tag va do dai secret (doan hoac brute-force),
# NHUNG khong biet secret. Van gia mao duoc mot cookie moi data' hop le,
# bang cach "noi tiep" trang thai hash tu tag da co (Merkle-Damgard).
#
# Chay:  python3 solve.py
import struct
import hashlib
import os

# ---------------------------------------------------------------------------
# 1. SHA-256 thuan Python, cho phep NAP trang thai dau (H) va bu do dai da hash
#    (prelen). Day chinh la dieu kien de noi tiep hash ma khong biet secret.
# ---------------------------------------------------------------------------
_K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1,
    0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
    0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
    0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
    0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a,
    0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]

_H0 = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
       0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]


def _rotr(x, n):
    return ((x >> n) | (x << (32 - n))) & 0xffffffff


def _compress(H, block):
    w = list(struct.unpack(">16I", block))
    for i in range(16, 64):
        s0 = _rotr(w[i - 15], 7) ^ _rotr(w[i - 15], 18) ^ (w[i - 15] >> 3)
        s1 = _rotr(w[i - 2], 17) ^ _rotr(w[i - 2], 19) ^ (w[i - 2] >> 10)
        w.append((w[i - 16] + s0 + w[i - 7] + s1) & 0xffffffff)
    a, b, c, d, e, f, g, h = H
    for i in range(64):
        S1 = _rotr(e, 6) ^ _rotr(e, 11) ^ _rotr(e, 25)
        ch = (e & f) ^ ((~e) & g)
        t1 = (h + S1 + ch + _K[i] + w[i]) & 0xffffffff
        S0 = _rotr(a, 2) ^ _rotr(a, 13) ^ _rotr(a, 22)
        maj = (a & b) ^ (a & c) ^ (b & c)
        t2 = (S0 + maj) & 0xffffffff
        h, g, f, e, d, c, b, a = g, f, e, (d + t1) & 0xffffffff, c, b, a, (t1 + t2) & 0xffffffff
    return [(x + y) & 0xffffffff for x, y in zip(H, [a, b, c, d, e, f, g, h])]


def sha256_padding(msglen):
    # padding MD/SHA cho mot thong diep dai msglen byte
    pad = b"\x80"
    pad += b"\x00" * ((56 - (msglen + 1)) % 64)
    pad += struct.pack(">Q", msglen * 8)
    return pad


def sha256(msg, H=None, prelen=0):
    # H     : trang thai dau (8 word). None = gia tri IV chuan.
    # prelen: so byte da duoc hash TRUOC msg (dung cho length extension).
    H = list(_H0) if H is None else list(H)
    data = msg + sha256_padding(prelen + len(msg))
    for i in range(0, len(data), 64):
        H = _compress(H, data[i:i + 64])
    return b"".join(struct.pack(">I", x) for x in H)


# ---------------------------------------------------------------------------
# 2. Phia server: ky va kiem cookie bang H(secret || data). Secret bi an.
# ---------------------------------------------------------------------------
SECRET = os.urandom(16)   # ke tan cong KHONG biet gia tri nay


def sign(data):
    return hashlib.sha256(SECRET + data).hexdigest()


def verify(data, tag):
    return hashlib.sha256(SECRET + data).hexdigest() == tag


# ---------------------------------------------------------------------------
# 3. Phia tan cong: chi biet (data, tag, do_dai_secret), khong biet secret.
# ---------------------------------------------------------------------------
def forge(data, tag, append, secret_len):
    # nap lai trang thai hash tu tag (8 word big-endian)
    H = struct.unpack(">8I", bytes.fromhex(tag))
    glue = sha256_padding(secret_len + len(data))       # padding server da them
    forged_data = data + glue + append
    # tiep tuc hash `append` tu trang thai H, voi phan dau da chiem prelen byte
    prelen = secret_len + len(data) + len(glue)
    forged_tag = sha256(append, H=H, prelen=prelen).hex()
    return forged_data, forged_tag


def main():
    # kiem tra SHA-256 thuan Python khop hashlib truoc da
    for s in [b"", b"abc", b"a" * 100, os.urandom(200)]:
        assert sha256(s) == hashlib.sha256(s).digest()
    print("[*] SHA-256 thuan Python khop hashlib: OK")

    data = b"user=guest&role=user"
    tag = sign(data)
    print("[*] cookie goc :", data.decode())
    print("[*] tag goc    :", tag)

    # gia su doan duoc do dai secret = 16 (co the brute-force tu 1..64)
    append = b"&role=admin"
    forged_data, forged_tag = forge(data, tag, append, secret_len=16)

    print("[*] them vao   :", append.decode())
    print("[*] cookie gia :", forged_data)
    print("[*] tag gia    :", forged_tag)
    ok = verify(forged_data, forged_tag)
    print("[*] server chap nhan cookie gia?", ok)
    assert ok, "forgery that bai"
    print("[+] length extension THANH CONG, khong he biet secret")

    # bonus: neu khong biet do dai secret, quet thu tu 1..32
    print()
    print("[*] khi chua biet do dai secret, quet thu:")
    for slen in range(8, 20):
        fd, ft = forge(data, tag, append, secret_len=slen)
        if verify(fd, ft):
            print("    do dai secret dung =", slen)
            break


if __name__ == "__main__":
    main()
