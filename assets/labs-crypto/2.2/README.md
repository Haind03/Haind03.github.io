# Lab 2.2: Pha Vigenere (crib + phan tich tan suat)

Script giải cho phần Lab của Bài 2.2. Ciphertext `HCYV{...}` là Vigenere khóa một từ tiếng Anh. Vì chuỗi ngắn và chứa nhiều ký tự leet nên IoC nhiễu, ta không tìm độ dài khóa bằng IoC mà dùng crib `FLAG`.

## Chạy

```bash
python3 solve.py
```

Chỉ dùng thư viện chuẩn (`re`, `string`). `transcript.txt` là output thật.

## File

- `solve.py`: suy 4 ký tự đầu của khóa từ crib `FLAG`, rồi brute 2 ký tự còn lại (khóa dài 6) và chấm điểm bằng cách de-leet rồi đếm từ tiếng Anh.
- `transcript.txt`: output thật.

## Ý chính

Bốn chữ `HCYV` ở đầu giải ra `FLAG` cho ngay 4 ký tự khóa `CRYP`. Từ đó khóa hoàn chỉnh là `CRYPTO` (một từ quen trong giới crypto), giải ra flag. Với ciphertext ngắn, crib và kiến thức về định dạng flag mạnh hơn thống kê thuần.
