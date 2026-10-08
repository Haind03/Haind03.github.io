# Lab 4.1: viet shellcode execve("/bin/sh") va nap vao RWX

Bai: [4.1-viet-shellcode-execve.md](../../phan-04-shellcode/4.1-viet-shellcode-execve.md)

## File

- `src.c`: loader, xin mot trang RWX bang mmap, doc shellcode tho tu stdin, chep vao roi nhay vao.
- `build.sh`: bien dich loader (`gcc -O0 -g -o loader src.c`).
- `exploit.py`: viet shellcode execve("/bin/sh",0,0) bang tay (null-free, 23 byte), so sanh voi `shellcraft.amd64.linux.sh()` (48 byte), nap vao loader, lay shell.
- `transcript.txt`: output THAT khi chay tren server.

## Chay

```bash
bash build.sh
/root/techlabs/venv/bin/python3 exploit.py
```

## Moi truong kiem thu

Ubuntu 24.04.4, glibc 2.39, gcc 13.3.0, pwntools. Chay lai 8/8 deu lay shell (uid=0).

## Ket qua

- shellcode viet tay: 23 byte, null-free, hex `31f65648bf2f62696e2f2f736857545f31d26a3b580f05`.
- `shellcraft.amd64.linux.sh()`: 48 byte.
- Loader nhay vao vung RWX, execve chay `/bin/sh`, go duoc `id` ra `uid=0(root)`.
