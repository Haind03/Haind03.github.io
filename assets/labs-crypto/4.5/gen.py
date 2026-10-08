#!/usr/bin/env python3
# gen.py: sinh de lab 4.5. 12 thong diep tieng Anh ma bang AES-CTR DUNG CHUNG nonce
# (loi nonce reuse). Mot thong diep chua flag. Ghi ciphertext hex ra ciphertexts.txt.
# Key/nonce co dinh cho de tai lap duoc; ben tan cong KHONG dung toi key.
from Crypto.Cipher import AES

MSGS = [
    b"we must never ever reuse a nonce since doing that leaks the whole keystream",
    b"the password for the staging server sits inside a locked vault that is offline",
    b"please come meet me at the old stone bridge tonight when the clock strikes nine",
    b"cryptography is the study of secure communication in the presence of adversaries",
    b"always authenticate the ciphertext or an attacker is completely free to modify it",
    b"the quick brown fox jumps over the lazy dog and then it runs along a quiet river",
    b"the stolen key you wanted is flag{n0nce_reuse_is_tw0_time_pad} keep it secret now",
    b"send the reinforcements over to the eastern gate well before the morning sun rises",
    b"a stream cipher is really just a fancy keystream that you xor with the plaintext",
    b"keep the plaintext rather short and the key material truly hard for anyone to guess",
    b"do not ever trust a communication channel that you are unable to verify end to end",
    b"the weekly staff meeting has now been moved down to the second basement of block b",
]
KEY = bytes(range(16))
NONCE = bytes(range(8))


def main():
    L = min(len(m) for m in MSGS)
    cts = [AES.new(KEY, AES.MODE_CTR, nonce=NONCE).encrypt(m[:L]) for m in MSGS]
    with open("ciphertexts.txt", "w") as f:
        for c in cts:
            f.write(c.hex() + "\n")
    print("Da ghi ciphertexts.txt:", len(cts), "dong, moi dong", L, "byte")


if __name__ == "__main__":
    main()
