# Lab 8.2: ECDSA nonce reuse tren secp256k1

Lab di kem Bai 8.2. Khoi phuc private key ECDSA khi ky hai thong diep bang CUNG mot nonce `k`.

## De bai

Curve: secp256k1 (`n` la bac nhom chuan). Ta chan duoc hai chu ky cua cung mot private key:

- `m1 = "POST /transfer amount=100 to=alice"` -> `(r, s1)`
- `m2 = "POST /transfer amount=999 to=mallory"` -> `(r, s2)`

Hai chu ky co cung `r`. Ngoai ra co mot flag da ma hoa AES-GCM, khoa la `sha256(str(d))`. Lay lai `d`, giai ma flag `ECC{...}`.

Tham so cu the nam trong `solve.py`.

## Dau hieu

Hai chu ky khac thong diep nhung `r1 == r2`. Vi `r` la hoanh do cua `R = k*G`, `r` trung nhau nghia la `k` trung nhau. Day la loi chet nguoi.

## Co che

- `s1 = k^-1 (z1 + r*d)`, `s2 = k^-1 (z2 + r*d)` mod n.
- Tru nhau khu `d`: `k = (z1 - z2) / (s1 - s2) mod n`.
- Co `k` roi: `d = (s1*k - z1) / r mod n`.

Tat ca la so hoc mod `n`, khong can mot phep EC nao.

## Chay

```
python3 solve.py
```

Yeu cau: `pip install pycryptodome`. Script tu chua.

## Ket qua

Xem `transcript.txt`. Flag: `ECC{n0nce_reuse_k1lls_ecdsa}`.

## Bai hoc

`k` phai ngau nhien, bi mat, va KHAC NHAU moi lan ky. Chuan RFC 6979 sinh `k` tat dinh tu `d` va thong diep de tranh ca loi RNG yeu lan loi dung lai. Lo mot `k`, hoac chi can hai chu ky trung `k`, la mat sach private key.
