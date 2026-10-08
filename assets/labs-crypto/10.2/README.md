# Lab 10.2: Phá custom PRNG bằng Z3

Kèm Bài 10.2 (Z3 và SMT cho crypto). Khôi phục seed của một custom xorshift32 PRNG từ known-plaintext rồi giải mã toàn bộ ra flag.

## File

- `gen.py`: sinh challenge. Mã hóa flag bằng stream cipher dùng keystream từ xorshift32, seed `0xC0FFEE42`. Ghi ciphertext ra `ct.hex`.
- `ct.hex`: ciphertext (hex) đã sinh sẵn, dùng ngay không cần chạy `gen.py`.
- `solve.py`: bộ giải Z3. Chỉ cần biết 5 byte đầu flag là `flag{`, mô hình hóa xorshift bằng BitVec, tìm seed, rồi giải mã hết.
- `modeq.py`: demo phụ, giải một hệ phương trình modular hai ẩn bằng Z3.

## Chạy

```bash
python3 solve.py
```

## Kết quả mong đợi

```
seed tim duoc : 0xc0ffee42
flag          : flag{z3_cr4ck5_cu5t0m_prng_1n_0ne_sh0t}
```

Xem `transcript.txt` để đối chiếu output thật của cả ba script.

## Điểm mấu chốt

- Phiên bản symbolic của xorshift phải dùng `LShR` cho dịch phải không dấu, không dùng `>>` (vốn là dịch phải số học trên BitVec).
- 5 byte known-plaintext (40 bit) đủ pin một seed 32 bit về nghiệm duy nhất. Ít hơn thì Z3 có thể trả seed khác cũng `sat` nhưng sai.
