#!/usr/bin/env python3
# server.py: giao thuc "session token" tu che co nhieu loi thiet ke.
#   Loi 1: AES-CTR dung NONCE CO DINH (keystream lap lai giua cac token).
#   Loi 2: KHONG co MAC/chu ky -> ciphertext deo duoc (malleable).
#   Loi 3: tin tuong hoan toan noi dung sau giai ma.
from Crypto.Cipher import AES

_KEY = b"an_example_key!!"          # bi mat, nam trong server
_NONCE = b"\x00" * 8                 # BUG: nonce co dinh dung cho moi token
FLAG = "flag{m4lle4ble_ctr_n0_m4c_equals_g4me_0ver}"

def _ctr():
    # CTR voi nonce co dinh: keystream giong het nhau moi lan -> loi nang
    return AES.new(_KEY, AES.MODE_CTR, nonce=_NONCE)

def issue_token(username):
    # chi cho phep role=guest khi phat token
    assert "&" not in username and "=" not in username
    plaintext = f"user={username}&role=guest".encode()
    return _ctr().encrypt(plaintext)        # tra ve ciphertext tho (bytes)

def is_admin(token):
    data = _ctr().decrypt(token)
    try:
        fields = dict(kv.split("=", 1) for kv in data.decode().split("&"))
    except Exception:
        return False, None
    if fields.get("role") == "admin":
        return True, FLAG
    return False, None
