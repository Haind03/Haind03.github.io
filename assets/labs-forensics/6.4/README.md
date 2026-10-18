# Lab 6.4: Moi credential va payload -enc fileless tu RAM

Lab chay that cho Bai 6.4. Mot tien trinh giu password, token, mot dong hash kieu NTLM
va mot chuoi `-enc` kieu PowerShell trong RAM. Ta dump bo nho no, moi credential bang
`strings`/`grep`, va giai chuoi `-enc` (base64 UTF-16LE) ra lenh that, dung cach dieu
tra fileless. Chay that tren Linux, khong can root, khong tai gi.

## An toan

Moi credential/hash deu GIA (khong phai cua he thong that). Chuoi `-enc` giai ra mot
lenh `Write-Output '...'` VO HAI; khong co gi duoc thuc thi. Day chi minh hoa quy trinh.

## Vi sao secret nam trong RAM

Mot chuong trinh phai giu password/token o dang ro trong bo nho de dung chung (ket noi
DB, goi API, xac thuc), du tren dia chung co the da ma hoa. Tren Windows, `lsass.exe`
giu hash NTLM va cac secret; do la ly do `hashdump`/`lsadump` moi duoc credential tu
anh RAM. Fileless con nang hon: payload chi song trong RAM, tat may la mat.

## Chay

```bash
DUMPDIR=_dump python3 -I capture.py   # chup bo nho tien trinh
DUMPDIR=_dump bash solve.sh           # moi credential + giai -enc
```

## Ket qua (xem transcript.txt)

1. `strings | grep` lay ra `password=Pa$$w0rd_LAB64` va `api_token=tok_live_LAB64_...`.
2. Dong hash kieu NTLM (`user:rid:lm:nt`) lo ra, dung dang `hashdump` tra ve.
3. Chuoi `PSENC=<base64>` nam trong RAM (kieu PowerShell `-enc`).
4. Giai `base64 -d | iconv -f UTF-16LE` ra lenh that:
   `Write-Output 'lab64 fileless demo: would DownloadString http://198.51.100.77/a.ps1'`.
   Thieu buoc `iconv UTF-16LE` se ra chuoi co byte null xen ke, trong nhu rac.

## Lenh Volatility 3 tuong ung (anh RAM Windows that cua ban)

Khong tai anh mau co malware. Khi co anh hop phap:

```bash
vol -f mem.raw windows.hashdump                  # NTLM local (SAM+SYSTEM)
vol -f mem.raw windows.lsadump                    # LSA secret, hay lo plaintext
vol -f mem.raw windows.cachedump                  # MSCASHv2 domain cache
vol -o out -f mem.raw windows.memmap --pid <lsass_pid> --dump
pypykatz lsa minidump out/pid.<lsass_pid>.dmp     # moi sau hon tu lsass dump
vol -f mem.raw windows.cmdline | grep -i powershell
# giai -enc lay tu cmdline:
echo '<base64>' | base64 -d | iconv -f UTF-16LE -t UTF-8
```

## Luu y phap ly

Credential moi duoc la BANG CHUNG, khong phai ve dang nhap vao he thong khac. Chi thao
tac tren dump cua he thong ban co quyen dieu tra.

## Files

- `victim.py`: giu credential/token/hash gia + chuoi `-enc` trong RAM.
- `capture.py`: chup bo nho tien trinh qua `/proc/<pid>/mem`.
- `solve.sh`: moi credential + giai `-enc`.
- `transcript.txt`: output that.

## Don dep

```bash
rm -rf _dump /tmp/mem6_4
```
