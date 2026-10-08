# Lab 6.5: Bleichenbacher padding oracle (PKCS#1 v1.5)

Script giải cho Bài 6.5. Chỉ từ một oracle trả lời "padding PKCS#1 v1.5 hợp lệ hay không", giải mã được ciphertext mà không biết private key.

## Chạy

```bash
python3 solve.py
```

Cần `pycryptodome`. `transcript.txt` là output thật.

## Lưu ý tốc độ

Khóa được rút xuống **256 bit** (trong `server.py`) để demo chạy nhanh: thực đo khoảng **vài giây tới hơn một phút**, cỡ **vài chục tới vài trăm nghìn** truy vấn oracle (số dao động mạnh theo khóa ngẫu nhiên mỗi lần, ví dụ các lần chạy đo được 7 giây / 59k và 33 giây / 288k). RSA-1024 nguyên lý y hệt nhưng tốn hàng trăm nghìn tới vài triệu truy vấn.

## File

- `server.py`: "nạn nhân", sinh khóa RSA 256 bit, mã flag bằng PKCS#1 v1.5, expose `n, e, k, c_target, oracle`. Không lộ `d`.
- `solve.py`: Bleichenbacher ba bước (tìm s đầu, thu hẹp khoảng, hội tụ), chỉ gọi `oracle`.
- `transcript.txt`: output thật.

## Ý chính

Tính thuần nhân `c*s^e = (m*s)^e` cho phép mỗi `s` hợp lệ cắt bớt khoảng chứa m (`2B <= m*s mod n < 3B` với `B = 2^(8*(k-2))`). Gom đủ ràng buộc, khoảng co về một điểm là m. Flag: `flag{pkcs1_v15_bb}`. OAEP chặn được vì ngẫu nhiên hóa và all-or-nothing.
