# Lab 9.2: Khôi phục MT19937 và phá LCG

Script giải cho Bài 9.2.

- Phần A: lấy 624 output 32-bit của MT19937 (PRNG mặc định của Python), untemper để dựng lại toàn bộ trạng thái, clone PRNG rồi dự đoán đúng các số kế tiếp.
- Phần B: cho một dãy output của LCG `X_{n+1} = (a*X_n + c) mod m`, khôi phục `m`, `a`, `c` rồi dự đoán số kế tiếp.

## Chạy

```bash
python3 solve.py
```

Chỉ dùng thư viện chuẩn (`random`, `math`, `functools`). Seed của nạn nhân là seed hệ thống, script không hề dùng tới nó. `transcript.txt` là output thật.

## File

- `solve.py`: `untemper`, `clone_mt`, và `recover_lcg`.
- `transcript.txt`: output thật.

## Ý chính

MT19937 và LCG không an toàn mật mã. Quan sát đủ output là khôi phục trạng thái và dự đoán tương lai. Cần random cho bảo mật thì dùng CSPRNG (`secrets`, `os.urandom`).
