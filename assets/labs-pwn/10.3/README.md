# Lab 10.3 - Secret Diary (do an cuoi: fmtstr leak canary + libc -> ret2libc)

Binary capstone cho bai 10.3. Ghep ba ky thuat da hoc:

- format string (Phan 7.1) de LEAK canary va dia chi libc
- canary (Phan 5.2): phai ghi lai dung canary khi tran de khong bi `__stack_chk_fail` abort
- ret2libc (Phan 6.1/6.2): goi `system("/bin/sh")`

Muc tieu: lay shell va doc `flag.txt`. Lam trong MOT lan chay (single-shot, hai bug).

## Moi truong da kiem

- Ubuntu 24.04.4 LTS, glibc 2.39-0ubuntu8.9, gcc 13.3.0
- pwntools (venv), ROPgadget 7.7
- ASLR BAT (`/proc/sys/kernel/randomize_va_space = 2`)

## Mitigation

```
RELRO: Partial | Canary: YES | NX: enabled | PIE: No (0x400000)
```

Chu y khac lab 10.2: o day canary BAT (`-fstack-protector-all`), nen bat buoc phai leak canary.

## File

| File | Vai tro |
|---|---|
| `src.c` | Source. Bug 1 (`printf(buf)` format string) va bug 2 (`read` 400 byte vao `buf[128]`). |
| `build.sh` | Bien dich (`-fstack-protector-all -no-pie -fcf-protection=none -O0 -g`) va tao `flag.txt`. |
| `exploit.py` | Single-shot: fmtstr leak canary + libc, roi overflow ghi dung canary -> ret2libc. |
| `transcript.txt` | Log chay THAT, 3 lan lien tiep (canary va base libc doi moi lan). |

## Chay

```bash
bash build.sh
./exploit.py
```

## So do stack (do bang objdump)

```
buf tai rbp-0x90 (144)
  buf -> canary    = 136   (canary tai rbp-8)
  buf -> saved RBP = 144
  buf -> saved RIP = 152
```

## Vi tri format string (do bang probe %p)

- Input bat dau o positional index 8 (`%8$p` = buf+0).
- Canary tai buf+136 -> index 8 + 136/8 = `%25$p`.
- De leak libc: dat con tro `puts@got` tai buf+24 (index 11) roi dung `%11$s`.

## Cam bay da dinh

- `%11$s` deref con tro chi hoat dong vi `puts` da duoc resolve (banner goi `puts` truoc).
- Con tro `puts@got` chua null byte o byte cao -> phai dat SAU cac format specifier
  (null se cat chuoi format), nen specifier tham chieu theo positional index.
- Race voi `read` giai doan 2: dung `time.sleep(0.5)` truoc khi gui lenh shell.
- `%s` in dia chi libc co the dung som neu dia chi chua null giua chung (hiem, ~2%):
  chay lai la duoc.
