# Lab 5.2: Length extension attack (SHA-256)

Script giải cho Bài 5.2. Minh họa tấn công length extension trên construction Merkle-Damgard: server ký cookie bằng `tag = SHA256(secret || data)`, kẻ tấn công giả mạo được cookie mới mà không biết `secret`.

## Chạy

```bash
python3 solve.py
```

Chỉ dùng thư viện chuẩn (`hashlib`, `struct`, `os`). Phần SHA-256 được hiện thực thuần Python để có thể nạp lại trạng thái hash và tiếp tục, đó chính là mấu chốt của đòn tấn công. `transcript.txt` là output thật của một lần chạy.

## File

- `solve.py`: SHA-256 thuần Python cho phép nạp state, server ký/kiểm, và hàm `forge` giả mạo.
- `transcript.txt`: output thật.

## Ý chính

`H(secret || msg)` không phải MAC an toàn. Biết `H(secret||msg)` và độ dài secret là nối thêm được dữ liệu tùy ý và tính ra tag hợp lệ mới. Dùng HMAC thay cho construction tự chế này.
