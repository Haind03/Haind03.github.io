# Lab 8.2: ret2plt và ret2dlresolve

Kèm bài [8.2 ret2plt và ret2dlresolve](../../phan-08-got-plt/8.2-ret2plt-ret2dlresolve.md).

## Mục tiêu

Lấy shell mà KHÔNG leak libc, bằng hai kỹ thuật:

- ret2plt: gọi lại `system@plt` (đã có PLT entry, địa chỉ cố định) với chuỗi `/bin/sh` có sẵn trong binary.
- ret2dlresolve: khi binary không có `system` và không leak được, ép `_dl_runtime_resolve` phân giải `system` bằng cấu trúc Elf giả.

## File

- `ret2plt.c` / `dlresolve.c`: hai binary nguồn.
- `build.sh`: biên dịch cả hai, Partial RELRO (giữ lazy binding).
- `exploit_ret2plt.py`: khai thác ret2plt.
- `exploit_dlresolve.py`: khai thác ret2dlresolve bằng pwntools `Ret2dlresolvePayload`.
- `transcript.txt`: log chạy thật trên server (Ubuntu 24.04, glibc 2.39, gcc 13.3).

## Môi trường

Ubuntu 24.04.4, glibc 2.39, gcc 13.3.0. Cả hai binary: No PIE, No canary, NX enabled, Partial RELRO.

ret2dlresolve chỉ chạy khi binary còn lazy binding, tức Partial RELRO. Full RELRO (mặc định glibc 2.39) sẽ chặn. Lab biên dịch:

```
gcc -fno-stack-protector -no-pie -fcf-protection=none -z relro -z lazy -O0 -g -o <bin> <src>.c
```

gcc 13 No-PIE không còn `pop rdi ; ret` sẵn, nên mỗi source tự nhét khối gadget `pop rdi/rsi/rdx ; ret` bằng inline asm.

## Chạy

```bash
bash build.sh
checksec --file=ret2plt      # Partial RELRO
checksec --file=dlresolve    # Partial RELRO
python3 exploit_ret2plt.py
python3 exploit_dlresolve.py
```

## Kết quả mong đợi

Cả hai exploit tự kiểm bằng `assert` và in `uid=0(root)`:

- ret2plt: `===PWNED_8_2_PLT===` rồi `ret2plt OK`.
- ret2dlresolve: `===PWNED_8_2_DL===` rồi `ret2dlresolve OK`.

## Ý chính

- Offset tới saved RIP: 72 (`buf[64]` + saved rbp 8).
- ret2plt cần hàm đã có PLT entry; nếu không có thì mới cần ret2dlresolve.
- ret2dlresolve dựng hai giai đoạn: `read(0, data_addr, len)` nạp blob cấu trúc giả vào `.bss`, rồi `ret2dlresolve` ép resolve. Cần một `ret` căn alignment 16 byte trước `system`.
- Binary demo có DT_VERSYM. pwntools bản mới vẫn xử lý được trên glibc 2.39.
