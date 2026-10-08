#!/usr/bin/env python3
# c08_detect_ecb.py: Cryptopals set 1 challenge 8 - phat hien AES-ECB
# ECB ma hoa moi block 16 byte doc lap => plaintext co block lap -> ciphertext co block lap.
from Crypto.Cipher import AES
import os

key = os.urandom(16)
# plaintext co 3 block giong het nhau (vi du du lieu co cau truc lap)
pt = b"YELLOW SUBMARINE" * 3 + b"and some tail xx"   # 4 block, 3 block dau giong nhau
ecb = AES.new(key, AES.MODE_ECB).encrypt(pt)
cbc = AES.new(key, AES.MODE_CBC, iv=os.urandom(16)).encrypt(pt)

def dup_blocks(ct, bs=16):
    blocks = [ct[i:i+bs] for i in range(0, len(ct), bs)]
    return len(blocks) - len(set(blocks))

print("so block trung (ECB):", dup_blocks(ecb), "-> day la ECB" if dup_blocks(ecb) else "")
print("so block trung (CBC):", dup_blocks(cbc), "-> khong lo pattern")
