# Lab 4.6: Byte-at-a-time ECB va padding oracle

Hai script giải cho Bài 4.6, gộp hai challenge kinh điển của Cryptopals Set 2/3.

## Chạy

```bash
python3 solve_ecb_byte_at_a_time.py   # moi SECRET qua oracle ECB(attacker || SECRET)
python3 solve_padding_oracle.py       # giai ma CBC qua oracle padding
```

Cần `pycryptodome`. `transcript.txt` là output thật của cả hai.

## File

- `solve_ecb_byte_at_a_time.py`: tự dò block size, xác nhận ECB, rồi moi SECRET từng byte bằng cách căn byte bí mật kế tiếp vào cuối block và thử 256 giá trị.
- `solve_padding_oracle.py`: bộ giải mã CBC nhiều block qua oracle padding, xử lý trùng hợp byte cuối.
- `transcript.txt`: output thật.

## Ý chính

Byte-at-a-time ECB sống vì ECB để lộ "cùng input thì cùng output" ở mức block. Padding oracle sống vì CBC trần không xác thực. Cả hai moi plaintext mà không cần key. SECRET của bài 1 là lyrics "Rollin' in my 5.0...", flag của bài 2 là `flag{ecb_and_padding_oracle_both_fall_without_the_key}`.
