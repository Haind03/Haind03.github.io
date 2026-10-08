# Lab 6.6: Bo giai RSA da tang (tong hop)

Script giải mẫu cho Bài 6.6. Một `solve(n, e, c)` tự dispatch qua small e, Wiener, Fermat; là bộ khung để gắn thêm tầng (factordb, common modulus, Hastad, shared prime, Coppersmith).

## Chạy

```bash
python3 solve.py              # tu kiem ba ca A/B/C
python3 gen/generate_cases.py # sinh vai challenge mau ra file text
```

Cần `gmpy2`, `pycryptodome`, `sympy`. `transcript.txt` là output thật.

## File

- `solve.py`: các tầng `small_e_root`, `wiener`, `fermat` và hàm điều phối `solve`; `__main__` tự sinh và giải ba ca.
- `gen/generate_cases.py`: sinh challenge mẫu (small e, Fermat, Wiener) ra file để tự luyện.
- `transcript.txt`: output thật.

## Ý chính

Triage trước khi gõ: in `n.bit_length()`, `e`, `e.bit_length()`. e nhỏ thử căn bậc e, e to thử Wiener, p/q gần thử Fermat. `solve` trả về `(ten_don, flag)`: A -> `small_e_root`, B -> `fermat`, C -> `wiener`.
