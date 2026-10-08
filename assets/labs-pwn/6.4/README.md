# Lab 6.4: ROP Emporium (bản tương đương chạy local)

Không tải được binary gốc từ ropemporium.com trên server, nên lab tự dựng bốn binary tương đương: cùng lỗ hổng (overflow trong `pwnme`, buf 32 byte), cùng mitigation (no-PIE, NX bật, không canary), gadget nhét sẵn giống bản gốc. Giải trọn bộ ret2win, split, callme, write4.

## File

- `ret2win.c`, `split.c`, `callme.c`, `write4.c`: nguồn bốn bài.
- `build.sh`: biên dịch cả bốn (`-fno-stack-protector -no-pie -fcf-protection=none -O0 -g`) và tạo `flag.txt`.
- `exploit_ret2win.py`, `exploit_split.py`, `exploit_callme.py`, `exploit_write4.py`: bốn exploit, đều lấy được flag.
- `transcript.txt`: output thật gộp cả bốn bài (Ubuntu 24.04, glibc 2.39, gcc 13.3). Kèm `transcript_<bai>.txt` từng bài.

## Chạy

```bash
bash build.sh                 # tạo cả 4 binary + flag.txt
python3 exploit_ret2win.py
python3 exploit_split.py
python3 exploit_callme.py
python3 exploit_write4.py
```

Chạy script CÙNG thư mục với `flag.txt` (các bài mở file theo đường dẫn tương đối).

## Ghi chú kỹ thuật (glibc 2.39, gcc 13.3), địa chỉ lần build ví dụ

- offset tới saved RIP = 40 (buf 32 + 8 saved rbp), đúng khung ROP Emporium.
- ret2win: chỉ cần nhảy vào `ret2win()` (0x401166), chèn một `ret` (0x40101a) căn alignment cho `system`.
- split: `pop rdi ; ret` (0x40116c, gadget nhét sẵn) đặt rdi = `usefulString` (0x404030 = "/bin/cat flag.txt"), gọi `system@plt` (0x401030). Có `ret` căn alignment.
- callme: gadget gộp `pop rdi ; pop rsi ; pop rdx ; ret` (0x401301), gọi callme_one (0x401176), callme_two (0x4011f1), callme_three (0x401277) đúng thứ tự với ba tham số đúng. QUAN TRỌNG: callme_three gọi `system("/bin/cat flag.txt")`, phải chèn một `ret` trước chain để căn alignment, nếu không `system` crash ở `movaps` và không in được flag (đã gặp và vá).
- write4: ghi "flag.txt" vào .bss (0x404150) bằng `pop r14 ; pop r15 ; ret` (0x401203) + `mov [r14], r15 ; ret` (0x401208), rồi `pop rdi ; ret` (0x401201) trỏ vào đó và gọi `print_file`.
- gcc 13 no-PIE không để lại `pop rdi ; ret` (và các gadget ghi bộ nhớ) sạch, nên source nhét sẵn gadget trong `usefulGadgets` đúng tinh thần ROP Emporium.
