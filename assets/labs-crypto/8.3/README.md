# Lab 8.3: Pohlig-Hellman tren Elliptic Curve (bac nhom tron)

Lab di kem Bai 8.3. Giai ECDLP (tim `k` sao cho `k*G = P`) khi bac nhom diem tron (smooth).

## De bai

Curve `y^2 = x^3 + a*x + b mod p`:

- `p = 10007`, `a = 3`, `b = 5`
- bac nhom `N = 10125 = 3^4 * 5^3`
- `G = (1, 3)`, `P = (5324, 8290) = secret * G`

Flag ma hoa AES-GCM, khoa `sha256(str(secret))`. Tim `secret`, giai ma flag `ECC{...}`.

## Dau hieu

Bac nhom diem `N` factor ra toan thua so nho (3 va 5). Y het Pohlig-Hellman tren `Fp*` o Bai 7.2, nhung lan nay nhom la nhom diem EC: chieu `G, P` xuong tung nhom con bac `q^e`, giai ECDLP nho bang baby-step giant-step tren EC, roi ghep bang CRT.

## Chay

```
python3 solve.py
```

Yeu cau: `pip install pycryptodome sympy`. Script tu chua (co san toan hoc EC thuan Python).

## Ket qua

Xem `transcript.txt`. `secret = 7391`, flag: `ECC{p0hlig_hellman_0n_curves}`.

## Bai hoc

Curve chuan (P-256, secp256k1, Curve25519) deu co bac nhom nguyen to hoac gan nguyen to (cofactor nho), nen Pohlig-Hellman vo dung. Curve tu che hay curve khong ro nguon goc co the co bac tron: luon kiem factor cua bac nhom truoc khi tin.
