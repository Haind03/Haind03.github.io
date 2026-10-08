# Lab 3.4 - Chuoi challenge ret2win tu de toi kho

Thuoc Bai 3.4. Ba challenge ret2win do kho tang dan.

## File

- `chall1.c` - de: ret2win khong tham so (win dung syscall).
- `chall2.c` - trung binh: 1 tham so (pop rdi), win goi system.
- `chall3.c` - kho hon: 2 tham so (pop rdi + pop rsi), win goi system.
- `build.sh` - bien dich ca ba, tao `flag.txt` (FLAG{ret2win_level_cleared}).
- `exp_chall1.py`, `exp_chall2.py`, `exp_chall3.py` - khai thac tung bai.
- `exploit.py` - driver chay lan luot ca ba.
- `transcript.txt` - output THAT.

## Build va chay

```bash
bash build.sh
python3 exploit.py       # chay ca ba
# hoac tung bai:
python3 exp_chall1.py    # -> Flag: FLAG{ret2win_level_cleared}
python3 exp_chall2.py    # -> ===SHELL_OK=== uid=...
python3 exp_chall3.py    # -> ===SHELL_OK=== uid=...
```

## Offset va gadget (do bang cyclic, khong doan)

- chall1 = 56, chall2 = 40, chall3 = 56.
- chall1 win = 0x401176.
- chall2: `pop rdi ; ret` = 0x401166, win = 0x401168, `ret` = 0x40101a.
- chall3: `pop rdi ; ret` = 0x401166, `pop rsi ; ret` = 0x401168, win = 0x40116a.

chall2 va chall3 can 1 gadget `ret` can stack 16 byte truoc khi vao win (system).

## Flag bien dich

`gcc -fno-stack-protector -no-pie -fcf-protection=none -O0 -g`.

## Moi truong

Ubuntu 24.04.4, glibc 2.39, gcc 13.3.0.
