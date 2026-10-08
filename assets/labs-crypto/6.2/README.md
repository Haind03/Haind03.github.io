# Lab 6.2: RSA tham so yeu (small e, Fermat, factordb)

Script giải cho Bài 6.2. Ba lỗi tham số kinh điển, mỗi cái một flag, sinh tại chỗ để tái lập được.

## Chạy

```bash
python3 solve.py
```

Cần `gmpy2`, `pycryptodome`, `sympy`. Phần factordb gọi `http://factordb.com/api` (có mạng) và tự fallback sang `sympy.factorint` khi offline. `transcript.txt` là output thật.

## File

- `solve.py`: (1) `e=3` không padding, `m^3 < n`, căn bậc ba; (2) `q = nextprime(p+2^20)` nên p, q gần nhau, Fermat factor; (3) n nhỏ, factordb hoặc factorint.
- `transcript.txt`: output thật.

## Ý chính

- small e: `CTF{sm4ll_e_m3ans_cub3_r00t}` lấy ra bằng một phép căn, không cần d.
- Fermat: `CTF{q_is_nextprime_of_p_oops}`, tách n ra ngay ở bước 0 vì p, q sát nhau.
- factordb: n nhỏ thì tra cộng đồng hoặc factor offline, rồi dựng flag từ hai thừa số.
