# Lab 4.5: Nonce reuse (fixed-nonce AES-CTR)

Script giải cho Bài 4.5. 12 thông điệp mã bằng AES-CTR dùng chung một nonce (lỗi nonce reuse) chính là two-time pad ở quy mô nhiều bản. Một thông điệp chứa flag. Khôi phục không dùng key.

## Chạy

```bash
python3 gen.py      # (tuy chon) sinh lai ciphertexts.txt, key/nonce co dinh
python3 solve.py
```

Cần `pycryptodome`. `ciphertexts.txt` là dữ liệu challenge (hex, mỗi dòng một bản mã). `transcript.txt` là output thật.

## File

- `gen.py`: tạo đề (AES-CTR cùng nonce), giấu flag vào một dòng.
- `ciphertexts.txt`: 12 ciphertext hex.
- `solve.py`: bước 1 dùng mẹo dấu cách đọc được phần lớn; bước 2 nhận ra trọn một câu, dùng nó làm known-plaintext để suy full keystream và lộ flag đầy đủ.
- `transcript.txt`: output thật.

## Ý chính

Cùng (key, nonce) cho cùng keystream, nên `Ci XOR Cj = Pi XOR Pj`. Mẹo dấu cách khôi phục đa số keystream; biết trọn một plaintext thì `K = C XOR P` cho toàn bộ keystream, giải mọi bản còn lại. Flag: `flag{n0nce_reuse_is_tw0_time_pad}`.
