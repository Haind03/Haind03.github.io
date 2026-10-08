# Lab 4.4: CBC bit flipping

Script giải cho Bài 4.4. Giả mạo chuỗi `;admin=true` qua AES-CBC dù input bị lọc ký tự `;` và `=`, không biết key.

## Chạy

```bash
python3 solve.py
```

Cần `pycryptodome`. `transcript.txt` là output thật.

## File

- `solve.py`: `submit`/`is_admin` phía server, phía tấn công nhét block đệm (bị hi sinh) rồi lật đúng hai byte trong ciphertext block trước để biến `?` thành `;` và `=`.
- `transcript.txt`: output thật.

## Ý chính

Lật byte j của `C(i-1)` thì `Pi[j]` bị XOR đúng delta đó: đặt `delta = old XOR want`. Giá phải trả là block `P(i-1)` nát, nên ta hi sinh một block đệm. Authenticated encryption (GCM) chặn đứng đòn này.
