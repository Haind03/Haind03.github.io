import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

KEY = os.urandom(16)
BS = 16
PRE  = b"comment1=cooking%20MCs;userdata="
POST = b";comment2=%20like%20a%20pound%20of%20bacon"

def submit(userdata: bytes) -> bytes:
    userdata = userdata.replace(b";", b"%3B").replace(b"=", b"%3D")
    data = PRE + userdata + POST
    iv = os.urandom(BS)
    c = AES.new(KEY, AES.MODE_CBC, iv)
    return iv + c.encrypt(pad(data, BS))

def is_admin(ct: bytes) -> bool:
    iv, body = ct[:BS], ct[BS:]
    c = AES.new(KEY, AES.MODE_CBC, iv)
    pt = unpad(c.decrypt(body), BS)
    return b";admin=true" in pt

if __name__ == "__main__":
    filler = b"A" * 16
    target = b"AAAAA?admin?true"
    ct = bytearray(submit(filler + target))
    off = 48
    ct[off + 5]  ^= ord('?') ^ ord(';')
    ct[off + 11] ^= ord('?') ^ ord('=')
    print("is_admin sau khi lat bit:", is_admin(bytes(ct)))
    assert is_admin(bytes(ct))
    print("OK, da gia mao ;admin=true ma khong biet key")
