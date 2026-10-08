# Lab 3.3: Pha repeating-key XOR (kieu Cryptopals set 1 challenge 6)

Script giải đầy đủ cho Bài 3.3. Khôi phục khóa và plaintext (có flag) từ một ciphertext mã bằng repeating-key XOR rồi encode base64.

## Chạy

```bash
python3 solve_xor.py challenge.b64
```

Chỉ dùng thư viện chuẩn (`base64`, `itertools`). `transcript.txt` là output thật.

Sinh lại đề (ra cùng `challenge.b64`):

```bash
python3 gen_challenge.py   # ghi challenge_gen.b64, bytewise bang challenge.b64
```

## File

- `solve_xor.py`: pipeline Hamming distance -> chẻ cột -> brute single-byte -> rút chu kỳ nhỏ nhất.
- `gen_challenge.py`: tạo đề, chứng minh `challenge.b64` là STRIKE XOR plaintext.
- `challenge.b64`: dữ liệu challenge.
- `transcript.txt`: output thật.

## Ý chính

Khóa `STRIKE` (6 byte), flag `flag{h4mming_distance_unlocks_the_keysize}`. Ứng viên keysize tốt nhất thường là bội số của độ dài thật, nên lấy cái nhỏ nhất trong nhóm top rồi rút về chu kỳ nhỏ nhất.
