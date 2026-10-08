# Lab 3.2 - ret2win (do offset toi saved RIP)

Thuoc Bai 3.2. De saved RIP bang dia chi ham `win` co san.

## File

- `ret2win.c` - demo: `buf[64]`, win dung syscall (khong vuong movaps).
- `jump.c` - lab: `buf[120]`, offset khac han kich thuoc buffer.
- `build.sh` - bien dich, tao `flag.txt` (picoCTF{fake_flag_for_demo}).
- `exp_ret2win.py` - khai thac ret2win (offset 72).
- `exploit.py` - khai thac jump (offset 136), co `conn()` doi local/REMOTE.
- `transcript.txt` - output THAT.

## Build va chay

```bash
bash build.sh
python3 exp_ret2win.py   # -> [+] win() da chay. Flag: picoCTF{fake_flag_for_demo}
python3 exploit.py       # -> WIN: picoCTF{fake_flag_for_demo}
```

## Offset (do bang cyclic, khong doan)

- `ret2win` = 72 (buf 64 + saved RBP 8).
- `jump` = 136 (buf 120 + padding + saved RBP).

Do bang `cyclic(n=8)` nap vao binary roi doc saved RIP tu corefile (xem
transcript.txt). `win` cua ret2win tai 0x401176.

## Flag bien dich

`gcc -fno-stack-protector -no-pie -fcf-protection=none -O0 -g`.

## Moi truong

Ubuntu 24.04.4, glibc 2.39, gcc 13.3.0. Offset khop moi truong tham chieu cu.
