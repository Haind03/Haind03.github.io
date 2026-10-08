# Lab 5.3 - ASLR/PIE: leak con tro, tinh base, ret2win

Thuoc Bai 5.3. Binary PIE, ASLR bat. Leak mot con tro .text qua format string,
tinh base = leak - offset, roi overflow nhay toi `win()`.

## File

- `src.c` - 2 lo: `printf(buf)` (leak) va read lan hai (overflow). `win()` in
  banner roi `system("/bin/sh")`.
- `build.sh` - `gcc -fno-stack-protector -fpie -pie -fcf-protection=none -O0 -g`.
- `exploit.py` - leak `%15$p` -> base = leak - 0x1244 -> overflow -> win -> shell.
- `transcript.txt` - output THAT (chay voi ASLR bat, base khac moi lan).

## Build va chay

```bash
bash build.sh
# nho bat ASLR that: cat /proc/sys/kernel/randomize_va_space  (phai la 1 hoac 2)
python3 exploit.py
# [+] leak       = 0x....244
# [+] image base = 0x....000
# ===SHELL_OK===
# uid=0(root) ...
```

## So lieu (do, khong doan)

- Offset static (file PIE): `win = 0x1179`, `main = 0x121d`, `vuln = 0x119e`,
  `ret` gadget = 0x101a.
- Format offset leak = `%15$p` = `base + 0x1244` (return-into-main, con tro
  .text). Xac dinh bang cach doi chieu `%N$p` voi `/proc/<pid>/maps`.
  (`%17$p` = `base_libc + 0x2a1ca`, dung neu muon leak libc.)
- Overflow offset toi saved RIP = 72 (buf = rbp-0x40, +8 saved RBP; khong canary).

## Diem chot

- PIE nen phai leak base truoc, khong hardcode dia chi `win` duoc.
- `base = leak - 0x1244`; kiem `base & 0xfff == 0` (can trang) de chac tru dung.
- Chay 3/3 lan voi ASLR bat deu lay shell, base khac nhau moi lan.

## Moi truong

Ubuntu 24.04.4, glibc 2.39, gcc 13.3.0. ASLR = 2 (bat).
