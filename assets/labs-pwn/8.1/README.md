# Lab 8.1: GOT overwrite bằng format string

Kèm bài [8.1 GOT overwrite](../../phan-08-got-plt/8.1-got-overwrite.md).

## Mục tiêu

Ghi đè ô GOT của `puts` thành địa chỉ `win()` bằng lỗ hổng format string, để lời gọi `puts("tam biet")` kế tiếp chạy vào `win()` và mở shell, lấy flag.

## File

- `src.c`: chương trình có lỗ hổng `printf(buf)` (format string) và hàm `win`.
- `build.sh`: biên dịch Partial RELRO. Tạo cả `flag.txt`.
- `exploit.py`: khai thác bằng pwntools `fmtstr_payload`.
- `transcript.txt`: log chạy thật trên server (Ubuntu 24.04, glibc 2.39, gcc 13.3).

## Môi trường

Ubuntu 24.04.4, glibc 2.39, gcc 13.3.0. Binary: No PIE, No canary, NX enabled, Partial RELRO.

Quan trọng: toolchain glibc 2.39 mặc định Full RELRO (khóa GOT chỉ đọc). Lab phải biên dịch Partial RELRO để GOT ghi được:

```
gcc -fno-stack-protector -no-pie -fcf-protection=none -z relro -z lazy -O0 -g -o fmtgot src.c
```

## Chạy

```bash
bash build.sh
checksec --file=fmtgot      # xac nhan: Partial RELRO
python3 exploit.py
```

## Kết quả mong đợi

Exploit tự kiểm bằng `assert`: in ra `uid=0(root)` và nội dung `flag{got_overwrite_via_format_string}`, rồi báo `GOT overwrite OK`.

## Ý chính

- Offset format string của buffer là 6 (dò bằng marker 8 byte + `%N$p`).
- `fmtstr_payload(6, {elf.got['puts']: elf.sym['win']})` lo phần ghi từng byte bằng `%hhn`.
- `win` dùng `write` chứ không dùng `puts` để tránh đệ quy vô hạn (vì `puts@got` đã trỏ về `win`).
