# Lab 7.2: Format string ghi %n -> GOT overwrite -> shell

Binary `writen` co loi `printf(buf)` truc tiep va goi `exit(0)` qua PLT/GOT sau do.
Muc tieu: dung `%n` ghi de `exit@got` thanh dia chi `win()`, khi `exit(0)` chay se
nhay vao `win()` -> `system("/bin/sh")` -> shell.

## Moi truong da kiem
- Ubuntu 24.04.4 LTS, glibc 2.39, gcc 13.3.0
- ASLR bat (`/proc/sys/kernel/randomize_va_space` = 2)
- pwntools (venv)

## Protections (checksec)
Partial RELRO, No canary, NX enabled, No PIE. FORTIFY tat luc build.
- **No PIE**: dia chi `win` (0x401186) va `exit@got` (0x404030) CO DINH, khong doi
  du ASLR bat (ASLR chi dung toi libc/stack/heap, khong dung toi vung binary no-PIE).
  Nho vay buoc ghi khong can leak gi truoc.
- **Partial RELRO**: `.got.plt` ghi duoc -> dieu kien de ghi de GOT. Neu Full RELRO
  (mac dinh gcc 13) thi GOT chi doc, phai doi muc tieu (xem bai hoc 7.2).

## Build va chay
```bash
bash build.sh          # tao ./writen
python3 exploit.py     # METHOD=auto: pwntools fmtstr_payload -> shell
```

## Ket qua (xem transcript.txt)
- Offset chuoi cua ta tren stack: **6**.
- `fmtstr_payload(6, {exit@got: win})` ghi `0x401186` vao `0x404030` chi trong 1 lan `printf`.
- `exit(0)` -> `win()` chay -> shell. Transcript co `uid=0(root)` sau marker `===PWNED_7_2===`.

## Hai cach ghi (doi `METHOD` trong exploit.py)
- `auto`: `fmtstr_payload` cua pwntools, tu chia ghi theo `%hn`/`%hhn`.
- `manual`: tu tay mot lenh `%<4486>c%8$hn`. Vi `win = 0x401186` ma `exit@got`
  san co byte thu 3 = `0x40`, nen chi can ghi 2 byte thap `0x1186`. Ca hai deu ra shell.

## Files
- `src.c` nguon chuong trinh co loi (co `win()`)
- `build.sh` lenh bien dich (no-PIE, Partial RELRO, khong canary, FORTIFY tat)
- `exploit.py` script ghi %n bang pwntools (va cach thu cong)
- `transcript.txt` log chay that
