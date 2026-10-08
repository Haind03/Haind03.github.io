# Lab 5.2 - Stack canary: leak qua format string roi overflow

Thuoc Bai 5.2. Leak canary bang lo format string, ghi LAI dung canary khi
overflow de qua epilogue, roi ret2win lay shell.

## File

- `src.c` - co 2 lo: `printf(buf)` (format string, de leak canary) va read lan
  hai (overflow). `win()` in banner roi `system("/bin/sh")`.
- `build.sh` - `gcc -fstack-protector-all -no-pie -fcf-protection=none -O0 -g`.
- `exploit.py` - leak canary (%15$p) -> overflow ghi lai canary -> win -> shell.
- `transcript.txt` - output THAT (gom ca truong hop canary sai -> stack smashing).

## Build va chay

```bash
bash build.sh
python3 exploit.py
# [+] canary = 0x....00
# ===SHELL_OK===
# uid=0(root) ...
```

## So lieu (do, khong doan)

- Layout (disas vuln): `buf = rbp-0x50`, `canary = rbp-0x8` => buf toi canary
  = 72, buf toi saved RIP = 88.
- Format offset canary = `%15$p` (gia tri 8 byte ket thuc 00).
- `win` = 0x401176, `ret` gadget = 0x40101a (can stack 16 byte truoc system).

## Diem chot

- Byte thap nhat cua canary luon 00 (thiet ke glibc x86-64) - dung
  `assert canary & 0xff == 0` de nhan biet leak dung o.
- Canary doi moi lan exec; exploit leak lai moi lan nen an dinh (3/3 run lay shell).
- Khong ghi lai dung canary => `*** stack smashing detected ***: terminated`.

## Moi truong

Ubuntu 24.04.4, glibc 2.39, gcc 13.3.0. ASLR = 2 (bat).
