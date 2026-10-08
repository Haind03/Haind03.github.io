import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

KEY = os.urandom(16)
BS = 16

def encrypt(msg: bytes) -> bytes:
    iv = os.urandom(BS)
    return iv + AES.new(KEY, AES.MODE_CBC, iv).encrypt(pad(msg, BS))

def padding_ok(ct: bytes) -> bool:
    iv, body = ct[:BS], ct[BS:]
    try:
        unpad(AES.new(KEY, AES.MODE_CBC, iv).decrypt(body), BS)
        return True
    except ValueError:
        return False

def decrypt_block(prev: bytes, cur: bytes) -> bytes:
    inter = bytearray(BS)
    out = bytearray(BS)
    for pad_val in range(1, BS + 1):
        pos = BS - pad_val
        forged = bytearray(BS)
        for i in range(pos + 1, BS):
            forged[i] = inter[i] ^ pad_val
        for guess in range(256):
            forged[pos] = guess
            if padding_ok(bytes(forged) + cur):
                if pad_val == 1:
                    forged[pos - 1] ^= 1
                    if not padding_ok(bytes(forged) + cur):
                        continue
                inter[pos] = guess ^ pad_val
                out[pos] = inter[pos] ^ prev[pos]
                break
        else:
            raise RuntimeError(f"ket o vi tri {pos}")
    return bytes(out)

def attack(ct: bytes) -> bytes:
    blocks = [ct[i:i+BS] for i in range(0, len(ct), BS)]
    out = b"".join(decrypt_block(blocks[i-1], blocks[i]) for i in range(1, len(blocks)))
    return unpad(out, BS)

if __name__ == "__main__":
    secret = b"flag{ecb_and_padding_oracle_both_fall_without_the_key}"
    ct = encrypt(secret)
    rec = attack(ct)
    print("khoi phuc:", rec)
    assert rec == secret
    print("OK, giai ma khong biet key")
