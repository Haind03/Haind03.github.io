# Lab 1.3: Bang phan vung MBR va GPT

Lab chay that: dung raw image co bang phan vung HOP LE bang python `struct`, roi parse nguoc bang `mmls` + `xxd` de doi chieu con so minh tu tinh.

## Cong cu
`python3`, `mmls` (Sleuth Kit), `xxd`.

## Chay lab
```bash
bash solve.sh    # tao mbr.dd va gpt.dd, parse bang mmls + xxd
```
`mkmbr.py` dung MBR 2 primary (FAT32 active + Linux). `mkgpt.py` dung GPT day du (protective MBR, primary/backup header, entry array, CRC32 dung). `transcript.txt` la output THAT.

Luu y: `mbr.dd` va `gpt.dd` la file sparse ~21MB, khong giu trong repo, chay `solve.sh` de tao lai.

## Nhiem vu
1. Bai tap giay but (xem `solution.md` muc "Nhiem vu giay but"): cho 64 byte partition table, tach entry #1 va #2, doc boot flag, type, LBA start, so sector, doi ra offset byte, tinh LBA end, kiem xem co khoang trong unallocated khong.
2. Chay lab MBR: dung `mkmbr.py`, xem 64 byte bang phan vung bang `xxd -s 0x1b0`, tu parse LBA start (byte 8..11 cua moi entry, little-endian), roi so khop voi `mmls`.
3. Chay lab GPT: dung `mkgpt.py`, tim chu ky `EFI PART` o LBA 1 bang `xxd`, so `mmls` voi so partition, va tim backup header o sector cuoi.

## Dap an
Xem `solution.md`. Output that: `transcript.txt`.
