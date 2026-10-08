# Lab 11.2: Writeup ECDSA nonce reuse

Kèm Bài 11.2 (viết writeup CTF crypto). Challenge ECDSA trên secp256k1 ký hai message bằng cùng một nonce. Khôi phục private key, private key chính là flag.

## File

- `chall.py`: "server" ECDSA (secp256k1 viết tay). Lỗi: dùng lại cùng nonce `k` cho hai chữ ký. Chạy sẽ in public key, hai chữ ký, và ghi `sigs.txt`.
- `sigs.txt`: dữ liệu challenge đã sinh sẵn (public key, hai cặp (r, s), hai message).
- `solve.py`: đọc `sigs.txt`, kiểm `r1 == r2`, khôi phục nonce rồi private key bằng hai phép chia modular, in flag.

## Chạy

```bash
python3 chall.py   # sinh lai sigs.txt (tuy chon, da co san)
python3 solve.py
```

## Kết quả mong đợi

```
nonce k khoi phuc : 0x1337c0debeef1337c0debeef1337c0debeef
private key d     : 0x666c61677b65636473615f6b5f7265753565217d
flag              : flag{ecdsa_k_reu5e!}
```

Xem `transcript.txt` để đối chiếu output thật.

## Yêu cầu

PyCryptodome (`bytes_to_long`, `long_to_bytes`). Python 3.8 trở lên cho `pow(x, -1, n)`.

## Công thức

Hai chữ ký cùng nonce k, cùng r:

```
k = (z1 - z2) * (s1 - s2)^(-1)  mod n
d = (s1*k - z1) * r^(-1)        mod n
```

với z = SHA-256(message) rút xuống mod n, n là bậc của secp256k1.
