#!/usr/bin/env python3
# solve.py: pha Vigenere cho Bai 2.2.
# Ciphertext ngan, co nhieu ky tu khong phai chu cai (leet), nen IoC nhieu.
# Chien thuat: dung crib "FLAG" lay 4 ky tu dau cua khoa, roi brute 2 ky tu con
# lai (khoa dai 6) va cham diem bang cach de-leet roi dem tu tieng Anh.
import re
import string

CT = "HCYV{o1u3p3ic_r1iv3t_1j_l0i_l4tg}"
CRIB = "FLAG"          # flag mo dau bang FLAG
KEYLEN = 6             # goi y: do dai khoa la 6

# tu tieng Anh pho bien de cham diem ban giai (sau khi de-leet)
WORDS = {"the", "is", "not", "and", "cipher", "safe", "key", "code",
         "secret", "vigenere", "crypto", "flag", "weak", "broken", "este"}


def decrypt(text, key):
    out, ki = [], 0
    for ch in text:
        if ch.isalpha():
            base = 65 if ch.isupper() else 97
            k = ord(key[ki % len(key)].upper()) - 65
            out.append(chr((ord(ch) - base - k) % 26 + base))
            ki += 1
        else:
            out.append(ch)
    return "".join(out)


def deleet(s):
    # 0->o 1->i 3->e 4->a 5->s 7->t
    return s.translate(str.maketrans("013457", "oieast"))


def score(pt):
    toks = re.split(r"[^a-z0-9]+", pt.lower())
    return sum(len(deleet(t)) for t in toks if deleet(t) in WORDS)


def main():
    letters = [c for c in CT if c.isalpha()]
    # Buoc 1: tu crib FLAG -> 4 ky tu dau cua khoa
    partial = "".join(chr((ord(h) - ord(w)) % 26 + 65)
                      for h, w in zip(letters[:len(CRIB)], CRIB))
    print("Khoa tung phan tu crib 'FLAG':", partial)

    # Buoc 2: brute 2 ky tu con lai, chon ban giai giong tieng Anh nhat
    best = None
    for a in string.ascii_uppercase:
        for b in string.ascii_uppercase:
            key = partial + a + b
            pt = decrypt(CT, key)
            sc = score(pt)
            if best is None or sc > best[0]:
                best = (sc, key, pt)
    _, key, pt = best
    print("Khoa khoi phuc             :", key)
    print("Ban ro                     :", pt)
    flag = re.search(r"FLAG\{[^}]*\}", pt)
    print("FLAG                       :", flag.group(0) if flag else "KHONG THAY")


if __name__ == "__main__":
    main()
