# Lab 4.3: Padding oracle attack (AES-CBC, PKCS#7)

Script giải cho Bài 4.3. Tự dựng cả oracle (biết key) lẫn kẻ tấn công (chỉ gọi `padding_ok`), giải mã toàn bộ ciphertext mà không biết key.

## Chạy

```bash
python3 solve.py
```

Cần `pycryptodome` (`pip install pycryptodome`). `transcript.txt` là output thật (ciphertext ngẫu nhiên mỗi lần, plaintext khôi phục cố định).

## File

- `solve.py`: oracle AES-CBC + hàm `attack` moi intermediate value từng byte bằng cách ép padding hợp lệ, có xử lý trùng hợp ở byte cuối (N=1).
- `transcript.txt`: output thật.

## Ý chính

`Pi = D(Ci) XOR C(i-1)`. Ta điều khiển `C(i-1)`, ép padding `01, 02, ...` để moi `D(Ci)` từng byte. Flag: `flag{padding_oracle_is_dangerous_ok}`. Chỉ cần một bit đúng/sai là đủ, gốc bệnh là CBC trần thiếu integrity.
