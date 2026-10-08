#!/usr/bin/env python3
# solve.py: pha nonce reuse (fixed-nonce CTR) cho Bai 4.5.
# Khong dung key. Hai buoc:
#   1) meo dau cach (space 0x20): doan keystream tung cot, doc duoc phan lon.
#   2) known-plaintext: tu phan doc duoc o buoc 1 ta nhan ra tron ven mot cau,
#      cung cap lai lam ban ro that -> suy full keystream -> giai mach cac cau,
#      lo ra flag day du.
import re

# Cau da biet (index 3). Trong CTF, buoc 1 cho ban doc gan het cau nay roi
# ban tu nhan ra va cung cap ban ro day du.
KNOWN_INDEX = 3
KNOWN_PT = b"cryptography is the study of secure communication in the presence of adversaries"


def load():
    with open("ciphertexts.txt") as f:
        return [bytes.fromhex(line.strip()) for line in f if line.strip()]


def recover_keystream_space(cts):
    n = min(len(c) for c in cts)
    ks = bytearray(n)
    for col in range(n):
        best_k, best_score = 0, -10 ** 9
        for i in range(len(cts)):
            cand = cts[i][col] ^ 0x20
            score = 0
            for c in cts:
                p = c[col] ^ cand
                if p == 0x20 or (65 <= p <= 90) or (97 <= p <= 122):
                    score += 1
                elif not (0x20 <= p < 0x7f):
                    score -= 1
            if score > best_score:
                best_score, best_k = score, cand
        ks[col] = best_k
    return bytes(ks)


def xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def main():
    cts = load()
    L = min(len(c) for c in cts)

    print("=== Buoc 1: meo dau cach (doc duoc phan lon) ===")
    ks1 = recover_keystream_space(cts)
    for c in cts:
        print(xor(c, ks1).decode(errors="replace"))

    print("=== Buoc 2: known-plaintext tren cau da nhan ra -> full keystream ===")
    ks2 = xor(cts[KNOWN_INDEX], KNOWN_PT[:L])
    texts = [xor(c, ks2).decode(errors="replace") for c in cts]
    for t in texts:
        print(t)

    m = re.search(r"flag\{[^}]*\}", "\n".join(texts))
    print("FLAG:", m.group(0) if m else "KHONG THAY")


if __name__ == "__main__":
    main()
