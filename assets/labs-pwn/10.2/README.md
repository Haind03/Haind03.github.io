# Lab 10.2 - Guestbook (writeup mau: leak libc + ret2libc)

Binary challenge tu dung cho bai 10.2. Dang bai dien hinh trong CTF: mot overflow
stack, co `puts` de leak libc, No PIE. Muc tieu: lay shell va doc `flag.txt`.

## Moi truong da kiem

- Ubuntu 24.04.4 LTS, glibc 2.39-0ubuntu8.9, gcc 13.3.0
- pwntools (venv), ROPgadget 7.7
- ASLR BAT (`/proc/sys/kernel/randomize_va_space = 2`)

## Mitigation

```
RELRO: Partial | Canary: No | NX: enabled | PIE: No (0x400000)
```

## File

| File | Vai tro |
|---|---|
| `src.c` | Source challenge. Co chu thich bug nam o dau. |
| `build.sh` | Bien dich (`-fno-stack-protector -no-pie -fcf-protection=none -O0 -g`) va tao `flag.txt`. |
| `exploit.py` | Exploit hai giai doan: leak libc qua `puts(puts@got)` -> ret2libc. |
| `transcript.txt` | Log chay THAT tren server, 3 lan lien tiep (base libc doi moi lan -> ASLR that su bat). |

## Chay

```bash
bash build.sh
./exploit.py            # local
# ./exploit.py REMOTE HOST=<ip> PORT=<port>   # neu phuc vu qua socat
```

## Y tuong (tom tat, chi tiet xem bai 10.2)

1. Offset toi saved RIP = 72 (buf tai `rbp-0x40`).
2. gcc 13 no-PIE khong con `pop rdi ; ret` san -> source tu nhet mot gadget `g_pop_rdi`.
3. Giai doan 1: `puts(puts@got)` in dia chi libc that cua `puts`, roi `ret` ve `main`.
4. Tinh `libc.address = leak - libc.sym['puts']`, kiem can trang.
5. Giai doan 2: ret2libc `system("/bin/sh")`, nho `ret` can alignment 16 byte.

## Cam bay da dinh (va cach xu ly trong exploit)

- Race voi `read`: sau khi gui payload giai doan 2, phai cho `read()` nuot xong
  payload va spawn `/bin/sh` TRUOC khi gui lenh shell. Neu gui lien tay, `read(256)`
  nuot luon dong lenh. Exploit dung `time.sleep(0.5)`.
- Dung sai file libc: offset `system`/`/bin/sh` tinh dong tu libc that, khong hardcode.
