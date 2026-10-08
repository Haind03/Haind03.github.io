#!/usr/bin/env python3
# c17_padding_oracle.py: Cryptopals set 1->2 challenge 17 - CBC padding oracle attack
# Server giu key bi mat, cho: (1) mot ciphertext (IV + blocks), (2) mot oracle noi
# "padding co hop le khong". Chi tu tin hieu dung/sai do, ta giai het plaintext.
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os

KEY = os.urandom(16)
BS = 16

def encrypt():
    pt = b"flag{p4dding_0racle_l34ks_th3_wh0le_plaintext}"
    iv = os.urandom(BS)
    ct = AES.new(KEY, AES.MODE_CBC, iv).encrypt(pad(pt, BS))
    return iv + ct

def oracle(iv_ct):
    # Tra ve True neu padding PKCS#7 hop le sau khi giai ma. Day la ro ri duy nhat.
    iv, ct = iv_ct[:BS], iv_ct[BS:]
    dec = AES.new(KEY, AES.MODE_CBC, iv).decrypt(ct)
    try:
        unpad(dec, BS)
        return True
    except ValueError:
        return False

def attack(iv_ct):
    blocks = [iv_ct[i:i+BS] for i in range(0, len(iv_ct), BS)]
    recovered = b""
    # giai tung block sau (dung block truoc lam "IV" de dieu khien)
    for bi in range(1, len(blocks)):
        prev, cur = blocks[bi-1], blocks[bi]
        inter = bytearray(BS)   # gia tri trung gian D(cur)
        for pad_val in range(1, BS + 1):
            pos = BS - pad_val
            for guess in range(256):
                forged = bytearray(BS)
                for j in range(pos + 1, BS):
                    forged[j] = inter[j] ^ pad_val         # ep cac byte sau thanh pad_val
                forged[pos] = guess
                if oracle(bytes(forged) + cur):
                    # loai nhieu: xac nhan khong phai do byte ke tiep (chi voi pad_val=1)
                    if pad_val == 1:
                        forged[pos-1] ^= 0xff
                        if not oracle(bytes(forged) + cur):
                            continue
                    inter[pos] = guess ^ pad_val
                    break
        recovered += bytes(inter[j] ^ prev[j] for j in range(BS))
    return recovered

if __name__ == "__main__":
    iv_ct = encrypt()
    pt = attack(iv_ct)
    print("plaintext (co padding):", pt)
    print("flag:", unpad(pt, BS).decode())
