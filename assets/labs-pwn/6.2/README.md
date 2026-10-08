# Lab 6.2: Leak libc qua GOT rồi ret2libc

Binary có `puts` và overflow, NX bật, no-PIE, Partial RELRO, không canary. Chạy với ASLR BẬT. Mục tiêu: leak một địa chỉ libc runtime, tính base, rồi ret2libc lấy shell. Exploit hai giai đoạn.

## File

- `src.c`: nguồn. Có nhét sẵn một gadget `pop rdi ; ret` (asm inline) vì gcc 13 no-PIE không để lại gadget sạch, mà giai đoạn leak chưa biết base libc nên chưa lấy gadget libc được.
- `build.sh`: biên dịch với `-fno-stack-protector -no-pie -fcf-protection=none -O0 -g`.
- `exploit.py`: giai đoạn 1 gọi `puts(puts@got)` rồi `ret` về `main`; giai đoạn 2 tính base libc động rồi ret2libc.
- `transcript.txt`: output thật trên server (Ubuntu 24.04, glibc 2.39, gcc 13.3).

## Chạy

```bash
bash build.sh
python3 exploit.py
```

## Ghi chú kỹ thuật (glibc 2.39, gcc 13.3)

- Gadget `pop rdi ; ret` nhét sẵn trong binary tại 0x401146 (cố định vì no-PIE), ROPgadget tìm thấy.
- Offset libc tính ĐỘNG từ libc server, không hardcode. Lần chạy ví dụ:
  - puts @ libc = 0x76cb7ca87cc0 -> libc base = 0x76cb7ca00000 (puts offset 0x87cc0)
  - `system` = base + 0x58750
  - `/bin/sh` = base + 0x1cc42f
- Kiểm `libc.address & 0xfff == 0` để chắc chắn đúng phiên bản libc.
- Giai đoạn 2 vẫn cần một `ret` căn alignment 16 byte cho `system`.
- offset tới saved RIP = 72.
- Timing: sau khi gửi payload giai đoạn 2, `sleep` một nhịp rồi mới gửi lệnh shell (tránh bị nuốt vào lần read của `vuln`).
