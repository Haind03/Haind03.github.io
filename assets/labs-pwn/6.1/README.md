# Lab 6.1: ret2libc

Binary dính overflow, NX bật, no-PIE, không canary. Mục tiêu: gọi `system("/bin/sh")` lấy shell bằng kỹ thuật ret2libc.

## File

- `src.c`: nguồn (hàm `vuln` đọc 256 byte vào `buf[64]`).
- `build.sh`: biên dịch với `-fno-stack-protector -no-pie -fcf-protection=none -O0 -g`.
- `exploit.py`: exploit pwntools, chạy local tới khi lấy shell và chạy `id`.
- `transcript.txt`: output thật khi chạy trên server (Ubuntu 24.04, glibc 2.39, gcc 13.3).

## Chạy

```bash
bash build.sh
python3 exploit.py
```

## Ghi chú kỹ thuật (glibc 2.39, gcc 13.3)

- gcc 13 no-PIE KHÔNG để lại `pop rdi ; ret` sạch trong binary nhỏ (ROPgadget xác nhận "none clean"), nên exploit lấy gadget từ chính libc qua `ROP([elf, libc])` sau khi đã biết base libc.
- Mọi offset libc tính ĐỘNG từ libc của tiến trình, không hardcode offset 2.35. Lần chạy ví dụ:
  - libc base = 0x700b2f200000 (ngẫu nhiên theo ASLR mỗi lần)
  - `pop rdi ; ret` (trong libc) = base + 0x10c08d
  - `system` = base + 0x58750
  - `/bin/sh` = base + 0x1cc42f
- Base libc của tiến trình local lấy qua `io.libc.address` (pwntools đọc `/proc/<pid>/maps`), đúng cả khi ASLR bật. Trên remote thật phải leak (xem Lab 6.2).
- Cần một gadget `ret` trước `system` để căn rsp bội số 16 (lệnh `movaps` trong `system` của glibc mới).
- offset tới saved RIP = 72 (buf[64] + 8 byte saved rbp).
- Lưu ý timing: `read(0,buf,256)` chỉ gọi read một lần, phải `sleep` một nhịp sau khi gửi payload rồi mới gửi lệnh shell, nếu không lệnh bị nuốt chung vào lần read đó.
