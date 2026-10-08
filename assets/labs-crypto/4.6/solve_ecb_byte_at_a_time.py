import os, base64
from Crypto.Cipher import AES

KEY = os.urandom(16)
BS = 16
SECRET = base64.b64decode(
    "Um9sbGluJyBpbiBteSA1LjAKV2l0aCBteSByYWctdG9wIGRvd24gc28gbXkg"
    "aGFpciBjYW4gYmxvdwpUaGUgZ2lybGllcyBvbiBzdGFuZGJ5IHdhdmluZyBq"
    "dXN0IHRvIHNheSBoaQpEaWQgeW91IHN0b3A/IE5vLCBJIGp1c3QgZHJvdmUgYnkK")

def oracle(attacker: bytes) -> bytes:
    data = attacker + SECRET
    pad_len = BS - (len(data) % BS)
    data = data + bytes([pad_len]) * pad_len
    return AES.new(KEY, AES.MODE_ECB).encrypt(data)

def detect_block_size() -> int:
    base = len(oracle(b""))
    i = 1
    while True:
        n = len(oracle(b"A" * i))
        if n != base:
            return n - base
        i += 1

def is_ecb() -> bool:
    ct = oracle(b"A" * 64)
    blocks = [ct[i:i+BS] for i in range(0, len(ct), BS)]
    return len(blocks) != len(set(blocks))

def attack() -> bytes:
    bs = detect_block_size()
    assert bs == BS, "block size bat ngo"
    assert is_ecb(), "khong phai ECB"
    total = len(oracle(b""))
    recovered = b""
    for _ in range(total):
        pad_len = bs - 1 - (len(recovered) % bs)
        prefix = b"A" * pad_len
        block_index = (pad_len + len(recovered)) // bs
        lo, hi = block_index * bs, block_index * bs + bs
        target = oracle(prefix)[lo:hi]
        found = None
        for b in range(256):
            guess = prefix + recovered + bytes([b])
            if oracle(guess)[lo:hi] == target:
                found = b
                break
        if found is None:
            break
        recovered += bytes([found])
    if recovered and recovered[-1] == 1:
        recovered = recovered[:-1]
    return recovered

if __name__ == "__main__":
    print("block size:", detect_block_size())
    print("la ECB    :", is_ecb())
    out = attack()
    print("--- SECRET khoi phuc ---")
    print(out.decode(errors="replace"))
    assert out == SECRET
    print("--- OK, moi het SECRET ma khong biet key ---")
