# Lab 9.1: Quan sat chunk, bin va tcache (glibc 2.39)

Demo quan sat, khong co khai thac. Muc tieu: nhin thay bang so that cau truc chunk
(size, PREV_INUSE), vong doi free vao tcache, va co che safe-linking cua con tro `fd`.

## Moi truong da kiem

- Ubuntu 24.04.4 LTS, glibc 2.39-0ubuntu8.9, gcc 13.3.0, gdb 15.1.

## File

- `src.c`: chuong trinh tu doc byte header va fd de in ra so that (khong can pwndbg).
- `build.sh`: bien dich `-no-pie -fno-stack-protector -O0 -g` ra `heapview`.
- `look.gdb`: script gdb (plain) xem header + fd + key + vung heap.
- `transcript.txt`: output that da chay tren server.

## Chay

```bash
./build.sh
setarch -R ./heapview              # ASLR off cho so on dinh khi hoc
gdb -q -nx -x look.gdb ./heapview  # xem bang gdb
```

## Neu co pwndbg/GEF

Cac lenh tuong duong de nhin dep hon (may server trong bai khong cai pwndbg nen
transcript dung gdb thuan):

```
vis_heap_chunks     # ve so do chunk mau
heap                # liet ke chunk
bins                # xem tcache / fastbin / unsorted / small / large
tcache              # xem rieng tcache va count tung bin
```

## Diem rut ra

- `malloc(0x30)` -> chunk `0x40`: cong 8 byte header, lam tron len boi so 16.
- `size_field = 0x41`: `0x40` la size, bit thap `0x1` la PREV_INUSE.
- `free` dau tien vao tcache rong: `fd = PROTECT(mem, NULL) = mem >> 12` (safe-linking).
- `PROTECT(pos, ptr) = (pos >> 12) XOR ptr`, `REVEAL` la phep nguoc lai.
- `key` la gia tri ngau nhien 64-bit cua tien trinh, dung de phat hien double free.
