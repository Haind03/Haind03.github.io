#!/usr/bin/env python3
# solve.py: pha transposition cho Bai 2.3.
# Ciphertext la rail fence. IoC cao nhu text thuong (chi xao vi tri, khong doi chu),
# nen day la transposition, khong phai thay the. Brute so rail roi cham diem.
# Luu y: chi-squared tren CHU DON vo dung o day, vi hoan vi khong doi tan suat chu don.
# Phai dung diem BIGRAM (nhay cam voi thu tu) moi phan biet duoc ban doc duoc.

CT = "WECRLTEERDSOEEFEAOCAIVDEN"

# Tan suat (xap xi, phan tram) cua cac bigram tieng Anh hay gap, dung lam diem.
BIGRAM = {
    'th': 2.71, 'he': 2.33, 'in': 2.03, 'er': 1.78, 'an': 1.61, 're': 1.41,
    'es': 1.32, 'on': 1.32, 'st': 1.25, 'nt': 1.17, 'en': 1.13, 'at': 1.12,
    'ed': 1.08, 'nd': 1.07, 'to': 1.07, 'or': 1.06, 'ea': 1.00, 'ti': 0.99,
    'ar': 0.98, 'te': 0.98, 'co': 0.79, 'de': 0.76, 'is': 0.86, 'le': 0.72,
    've': 0.70, 'ce': 0.65, 'di': 0.50, 'ee': 0.40, 'nc': 0.40, 'fl': 0.30,
    'sc': 0.30, 'ov': 0.20,
}


def ioc(text):
    letters = [c.upper() for c in text if c.isalpha()]
    n = len(letters)
    if n <= 1:
        return 0.0
    return sum(letters.count(ch) * (letters.count(ch) - 1)
               for ch in set(letters)) / (n * (n - 1))


def bigram_score(text):
    t = text.lower()
    return sum(BIGRAM.get(t[i:i + 2], 0) for i in range(len(t) - 1))


def rail_decode(cipher, rails):
    if rails < 2:
        return cipher
    pattern = []
    r, step = 0, 1
    for _ in range(len(cipher)):
        pattern.append(r)
        if r == 0:
            step = 1
        elif r == rails - 1:
            step = -1
        r += step
    counts = [pattern.count(i) for i in range(rails)]
    rows, idx = [], 0
    for c in counts:
        rows.append(list(cipher[idx:idx + c]))
        idx += c
    pos = [0] * rails
    out = []
    for r in pattern:
        out.append(rows[r][pos[r]])
        pos[r] += 1
    return "".join(out)


def main():
    print("IoC cua ciphertext:", round(ioc(CT), 4),
          "(cao nhu text thuong -> transposition, khong phai thay the)")
    print("--- brute so rail (diem bigram, cao = giong tieng Anh) ---")
    best = None
    for rails in range(2, 8):
        dec = rail_decode(CT, rails)
        sc = bigram_score(dec)
        print(f"rails={rails}: {dec}   (bigram={sc:.2f})")
        if best is None or sc > best[0]:
            best = (sc, rails, dec)
    print("Chon rail:", best[1])
    print("Ban ro   :", best[2])


if __name__ == "__main__":
    main()
