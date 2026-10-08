# Lab 9.2: Use-after-free + type confusion

Binary note don gian co mot BUG kinh dien: sau khi `free(o)` khong gan `o = NULL`,
nen con tro `o` van dung duoc (dangling pointer). Them vao do, option "use" goi
`o->action()` ngay ca khi object da bi free.

## Moi truong da kiem

- Ubuntu 24.04.4 LTS, glibc 2.39-0ubuntu8.9, gcc 13.3.0. ASLR BAT.

## File

- `src.c`: menu create/use/free/spray. `Obj` co con tro ham `action` o offset 0x18.
- `build.sh`: `-no-pie -fno-stack-protector -O0 -g` ra `uaf`.
- `exploit.py`: khai thac bang pwntools, tu kiem bang `assert`.
- `transcript.txt`: output that.

## Y tuong khai thac

1. `create`: cap phat `Obj` (24 byte info + con tro `action`). `action = say_hi`.
2. `free`: giai phong, nhung `o` van tro vao chunk cu (UAF).
3. `spray`: `malloc` cung kich thuoc -> lay lai dung chunk vua free. Ta ghi 24 byte
   padding roi 8 byte dia chi `win`. Day la type confusion: byte raw cua buffer spray
   duoc dien giai thanh con tro ham cua `Obj`.
4. `use`: goi `o->action()`, bay gio tro toi `win()` -> `system("/bin/sh")`.

## Chay

```bash
./build.sh
python3 exploit.py
```

## Tai sao chiem lai dung chunk

Chunk `Obj` (size 0x20 -> chunk 0x30) sau khi free vao tcache. `malloc` cung size keo
dung chunk do ra khoi tcache. Vi vay `o` (cu) va `p` (moi spray) tro cung mot vung.
