# Lab 9.3: Double free va tcache poisoning (safe-linking, glibc 2.39)

Bai loi cua phan heap. Chuong trinh "heap note" co menu alloc/free/edit/show voi
chunk size co dinh `0x30`. BUG: `free` khong xoa con tro nen co the doc (show) va ghi
(edit) tren chunk da free (UAF).

## Moi truong da kiem

- Ubuntu 24.04.4 LTS, glibc 2.39-0ubuntu8.9, gcc 13.3.0. ASLR BAT. Exploit chay on dinh.

## File

- `src.c`: heap note. `hook` la con tro ham toan cuc `__attribute__((aligned(16)))`.
- `build.sh`: `-no-pie -fno-stack-protector -O0 -g` ra `poison`.
- `exploit.py`: tcache poisoning -> ghi `&win` vao `hook` -> `run-hook` lay shell.
- `dfree.py`: demo double free bi chan + cach xoa key de vuot qua.
- `transcript.txt`: output that cua ca hai script.

## Ba diem phai dung tren glibc 2.39

1. Safe-linking (tu glibc 2.32): con tro `fd` trong tcache bi obfuscate theo cong thuc
   `stored = (chunk_addr >> 12) XOR next`. Khi poison phai tinh dung phep nay.
2. tcache key (tu glibc 2.29): moi chunk free co truong `key`. Free lai lan hai vao
   cung bin se bi phat hien ("double free detected in tcache 2"). Phai xoa/ghi de key,
   hoac dung 2 chunk khac nhau.
3. Alignment: dia chi target ma malloc tra ve phai can 16 (`aligned_OK` trong
   `tcache_get`), neu khong se abort "malloc(): unaligned tcache chunk detected".

## Vi sao free 2 chunk chu khong phai single-free

Da test: single-free (count=1) KHONG du. Sau malloc dau tien count ve 0, va malloc
thu hai bo qua tcache (chi lay tu tcache khi `counts[idx] > 0`), nen con tro poison
khong duoc dung. Phai free 2 chunk de `count=2`, khi do malloc thu hai tra ve target.

## Chay

```bash
./build.sh
python3 exploit.py   # lay shell
python3 dfree.py     # xem double free bi chan + cach xoa key
```
