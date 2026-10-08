# Lab 7.2: Pohlig-Hellman tren DH co p-1 tron

Lab di kem Bai 7.2. Phat discrete log khi `p-1` chi gom cac thua so nguyen to nho (smooth).

## De bai

Cho tham so Diffie-Hellman cong khai:

- `p = 7962994002710200590936746770260937501` (so nguyen to 123-bit)
- `g = 24` (primitive root, bac bang `p-1`)
- `A = g^a mod p = 1019641922916465058952932203248509729`

Khoa bi mat `a` chinh la flag o dang so nguyen (`bytes_to_long`). Khoi phuc `a`, doi ra bytes se duoc flag dang `DH{...}`.

## Dau hieu

Factor `p-1` ra thay toan thua so nho (lon nhat la 23). Nhom nhan mod p vo ra thanh tich cac nhom con be xiu, moi cai giai discrete log rieng rat nhanh, roi ghep lai bang CRT. Do la Pohlig-Hellman.

## Chay

```
python3 solve.py
```

Yeu cau: `pip install sympy`. Script tu chua, khong can file ngoai.

## Ket qua

Xem `transcript.txt`. Flag: `DH{sm0oth_dl0g}`.

## Bai hoc

Tham so DH an toan phai dung safe prime `p = 2q + 1` voi `q` nguyen to lon, de nhom con lon nhat co bac `q` khong the brute. `p-1` tron la an tu, du `p` co 2048-bit cung vo.
