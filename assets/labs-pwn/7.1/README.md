# Lab 7.1: Format string leak

Binary `leak` co loi `printf(buf)` truc tiep. Muc tieu: tim offset tham so cua chuoi
ban nhap tren stack, roi leak canary, libc base va PIE base; cuoi cung dung `%s`
doc bo nho tuy dia chi (doc chuoi `secret` trong binary).

## Moi truong da kiem
- Ubuntu 24.04.4 LTS, glibc 2.39, gcc 13.3.0
- ASLR bat (`/proc/sys/kernel/randomize_va_space` = 2)
- pwntools (venv)

## Protections (checksec)
Full RELRO, Canary found, NX enabled, PIE enabled. FORTIFY tat luc build.
Canary va PIE con nguyen la co y: bai nay can co chung de LEAK.

## Build va chay
```bash
bash build.sh          # tao ./leak
python3 exploit.py     # leak offset=8, canary, libc base, PIE base, %s doc secret
```

## Ket qua (xem transcript.txt)
- Offset chuoi cua ta tren stack: **8** (marker `AAAAAAAA` = `0x4141414141414141` hien o `%8$p`).
- Canary: `%25$p` (ket thuc byte `00`, doi moi lan chay).
- libc base: `%27$p - 0x2a1ca` (dia chi tra ve trong `__libc_start_call_main`).
- PIE base: `%51$p - main_offset` (con tro toi `main` ma `__libc_start_main` luu lai).
- `%s` doc duoc `FLAG{f0rmat_str1ng_arb1trary_r3ad}` tai `PIE base + &secret`.

Vi ASLR bat, moi lan chay cac base khac nhau. Exploit tinh base DONG tu leak nen
luon dung. Leak va doc nam trong cung mot tien trinh (binary doc nhieu luot) nen
base khong doi giua buoc leak va buoc doc.

## Files
- `src.c` nguon chuong trinh co loi
- `build.sh` lenh bien dich (FORTIFY tat, giu canary + PIE)
- `exploit.py` script leak bang pwntools
- `transcript.txt` log chay that
