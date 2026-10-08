# Lab 9.4 (capstone): Heap note -> shell bang tcache poisoning

Chuong trinh "Note Manager" kieu CTF: menu `add/del/edit/view/exit`, note size tuy chon.
BUG: `del` khong xoa con tro (UAF). Muc tieu: lay shell va doc `flag.txt` bang tcache
poisoning, ghi de mot o GOT thanh `backdoor()`.

## Moi truong da kiem

- Ubuntu 24.04.4 LTS, glibc 2.39-0ubuntu8.9, gcc 13.3.0. ASLR BAT. Exploit chay on dinh.

## File

- `src.c`: note app co UAF. `backdoor()` chay `system("/bin/sh")` (no-PIE: dia chi co dinh).
- `build.sh`: `-no-pie -fno-stack-protector -O0 -g` ra `noteapp`, tao san `flag.txt`.
- `exploit.py`: chuoi khai thac day du, tu kiem bang `assert`.
- `flag.txt`: flag doc duoc sau khi co shell.
- `transcript.txt`: output that.

## Chuoi khai thac

1. `add(0)`, `add(1)` hai note cung bin `0x40`.
2. `del(0)`, `del(1)` -> tcache count=2, head=note1.
3. `view(0)` doc `fd` da obfuscate cua note0 = `note0>>12` = `heap_base>>12` (leak heap).
4. Poison `note1.fd = (heap_base>>12) XOR atoi@got` (safe-linking). Vi note0 va note1
   cung trang, `note1>>12 = heap_base>>12`, nen khong can biet offset chunh xac.
5. `add(2)` -> note1, `add(3)` -> `atoi@got` (nho da can 16 -> qua `aligned_OK`).
6. `edit(3)` ghi `&backdoor` vao `atoi@got`.
7. Nhap mot so bat ky o menu -> `getint()` goi `atoi()` -> `backdoor()` -> shell -> `cat flag.txt`.

## Dieu kien va cam bay (glibc 2.39)

- Partial RELRO: `.got.plt` ghi duoc. Full RELRO se chan buoc 6 (doi sang ghi de con
  tro ham trong chuong trinh, nhu lab 9.3).
- Phai free 2 chunk (khong phai single-free) vi "count gate" (xem 9.3).
- Target phai can 16. Tranh o GOT dau tien (`free@got`) vi header chunk do de len cac
  o GOT reserved cua loader (GOT[1]/GOT[2]); chon `atoi@got` (0x404050, da can 16).

## Chay

```bash
./build.sh
python3 exploit.py
```
