# Lab 3.1 - Ghi de bien cuc bo

Thuoc Bai 3.1 (phan-03-buffer-overflow). Ghi de mot bien cuc bo nam ngay sau
buffer de doi nhanh `if`.

## File

- `login.c` - demo: tran `buf[32]` de ghi `authed` (offset 32) roi `win()` -> shell.
- `admin.c` - lab: tran `name[48]` de ghi `role = 0x80000001` (offset 48) -> in flag.
- `build.sh` - bien dich (ghi ro flag), tao `flag.txt`.
- `exp_login.py` - khai thac login (demo shell).
- `exploit.py` - khai thac admin (lab, in flag).
- `transcript.txt` - output THAT khi chay tren server verify.

## Build va chay

```bash
bash build.sh
python3 exploit.py     # admin -> Flag: FLAG{ban_da_ghi_de_bien_cuc_bo}
python3 exp_login.py   # login -> shell (===SHELL_OK===, uid=...)
```

## Offset (do, khong doan)

Hai bien nam trong `struct` nen offset = `offsetof`: `name -> role = 48`,
`buf -> authed = 32`. Xac minh bang gdb (`p &u.name`, `p &u.role`): role cao
hon name dung 0x30 = 48 byte (xem transcript.txt).

## Flag bien dich

`gcc -fno-stack-protector -no-pie -fcf-protection=none -O0 -g` (No canary, No PIE).

## Moi truong

Da kiem tren Ubuntu 24.04.4, glibc 2.39, gcc 13.3.0. ca hai binary deu dat muc tieu.
