# Lab 6.3: Common modulus va Hastad broadcast

Script giải cho Bài 6.3. Hai tấn công khai thác cùng một thông điệp bị mã nhiều lần, không cần factor n, không cần d.

## Chạy

```bash
python3 solve.py
```

Cần `gmpy2`, `pycryptodome`. `transcript.txt` là output thật.

## File

- `solve.py`: (1) common modulus, cùng n hai e `gcd=1`, extended Euclid `m = c1^a * c2^b`; (2) Hastad, cùng m cùng `e=3` ba modulus, CRT rồi căn bậc ba.
- `transcript.txt`: output thật.

## Ý chính

- Common modulus: `CTF{common_modulus_no_d_needed}`. Một trong hai số mũ âm, phải invert ciphertext trước khi lũy thừa.
- Hastad: `CTF{hastad_broadcast_crt_cube}`. Cần đúng `e` bản mã để `m^e` nhỏ hơn tích các modulus, CRT ghép ra `m^e` nguyên vẹn.
