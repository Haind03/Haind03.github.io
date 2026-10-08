#!/usr/bin/env python3
# solve.py: khoi phuc private key ECDSA tu hai chu ky DUNG LAI nonce (secp256k1).
# Co che: hai chu ky cung k -> cung r. Giai ra k, roi ra d, roi giai ma flag.
# Tu chua. Yeu cau: pip install pycryptodome
import hashlib
from Crypto.Cipher import AES

# ===== secp256k1 =====
n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141  # bac nhom

# ===== De bai: public key, hai chu ky, va flag da ma hoa =====
# (hai thong diep khac nhau, nhung co cung r -> lo ngay la dung lai nonce)
m1 = b"POST /transfer amount=100 to=alice"
m2 = b"POST /transfer amount=999 to=mallory"
r  = 0x5f81956d5826bad7d30daed2b5c8c98e72046c1ec8323da336445476183fb7ca
s1 = 0x8fbb25ea8158351cb3281b3f229f9caf463a25e19556102b4ddae8ced66ba7fa
s2 = 0xe2f450aa2bd3c02902580fd1fb8ad059dd76b08b7cf98ea9e68576adf0bb6ded
ct  = bytes.fromhex("5d26f9cb5b39af3b59964fce8cb2bc2a2fa519b6c47093a1f0cb6b67")
tag = bytes.fromhex("6fee81ddf3f34a77cabc0d690cd4e3f4")

def H(msg):
    return int.from_bytes(hashlib.sha256(msg).digest(), "big") % n

def main():
    z1, z2 = H(m1), H(m2)
    # k = (z1 - z2) / (s1 - s2) mod n
    k = (z1 - z2) * pow(s1 - s2, -1, n) % n
    # d = (s1*k - z1) / r mod n
    d = (s1 * k - z1) * pow(r, -1, n) % n
    print("[*] nonce k khoi phuc =", hex(k))
    print("[*] private key d     =", hex(d))

    key = hashlib.sha256(str(d).encode()).digest()
    cipher = AES.new(key, AES.MODE_GCM, nonce=b"labnonce1234")
    flag = cipher.decrypt_and_verify(ct, tag)   # verify tag -> dung d moi giai duoc
    print("[+] flag =", flag.decode())

if __name__ == "__main__":
    main()
