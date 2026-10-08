# Lab 6.3: ret2syscall (binary static)

Binary build STATIC, NX bật, no-PIE, overflow. Mục tiêu: gọi `execve("/bin/sh", 0, 0)` bằng một ROP chain đặt rax/rdi/rsi/rdx rồi `syscall`.

## File

- `src.c`: nguồn. Tự khai báo `char shell[] = "/bin/sh"` để `elf.search` chắc chắn thấy chuỗi, và nhét sẵn bộ gadget sạch `pop rax/rdi/rsi/rdx ; ret` + `syscall ; ret`.
- `build.sh`: biên dịch `-static -fno-stack-protector -no-pie -fcf-protection=none -O0 -g`.
- `exploit.py`: dùng `rop.execve(binsh, 0, 0)` để pwntools tự dựng chain.
- `exploit_manual.py`: bản làm tay, đặt từng thanh ghi rõ ràng (pop rax=59, pop rdi=&"/bin/sh", pop rsi=0, pop rdx=0, syscall).
- `transcript.txt`, `transcript_manual.txt`: output thật trên server (Ubuntu 24.04, glibc 2.39, gcc 13.3).

## Chạy

```bash
bash build.sh
python3 exploit.py          # bản auto
python3 exploit_manual.py   # bản làm tay
```

## Ghi chú kỹ thuật (glibc 2.39, gcc 13.3)

- Binary static gcc 13 thực tế CÓ `pop rax ; ret` và `syscall`, nhưng KHÔNG có `pop rdi/rsi/rdx ; ret` sạch (chỉ nằm trong các dãy lệnh rác), nên source nhét sẵn bộ gadget sạch kiểu ROP Emporium để chain ret2syscall chạy đúng như lý thuyết. Địa chỉ gadget nhét (lần build ví dụ): pop rax=0x401885, pop rdi=0x401887, pop rsi=0x401889, pop rdx=0x40188b, syscall=0x4012a4.
- Chuỗi `/bin/sh` @ 0x4aa0d0 (trong .data của binary).
- Chú ý khác biệt auto vs manual: `rop.execve` của pwntools trên toolchain này KHÔNG xếp pop rax/rdi/... như mong đợi mà chọn SROP (sigreturn, `SYS_rt_sigreturn`) để dựng khung execve. Cả hai cách đều lấy được shell. Bản `exploit_manual.py` mới là chain đặt từng thanh ghi đúng như phần lý thuyết mô tả.
- Binary no-PIE static nên địa chỉ gadget cố định, ASLR không ảnh hưởng.
- offset tới saved RIP = 72.
- `checksec` báo "Canary found" là canary của các hàm glibc nhúng vào, không phải của `vuln()`; `vuln()` vẫn overflow thẳng.
