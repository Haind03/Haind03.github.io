# Lab 1.5: NTFS va MFT record

Lab chay that tren Linux (khong can root): `mkntfs` tao NTFS image tren file thuong, Sleuth Kit
doc MFT record bang `istat`, va ta trich 1 record tho de tu parse byte.

## Cong cu
`mkntfs` (ntfs-3g), `python3`, `fsstat`, `istat`, `icat`, `xxd`.

## Chay lab
```bash
bash make.sh     # tao lab15.ntfs, trich mft_rec0.bin ($MFT) va mft_rec5.bin (root dir)
bash solve.sh    # fsstat, istat record 0 va 5, parse record tho, convert FILETIME
```
`transcript.txt` la output THAT. `mft_rec0.bin` / `mft_rec5.bin` (1024 byte moi cai) GIU trong repo
de luyen parse. Image `lab15.ntfs` (10MB) khong giu, chay `make.sh` tao lai.

## Nhiem vu (co lab chay that)
1. Parse tay 1 MFT record tho (`mft_rec0.bin`): tim signature `FILE`, offset toi attribute dau (byte 0x14),
   flags (byte 0x16: file hay thu muc, in-use hay deleted), roi liet ke attribute `$STANDARD_INFORMATION` (0x10)
   va `$FILE_NAME` (0x30). Kiem lai bang `mftparse.py`.
2. Dung `istat` doc record 0 (`$MFT`) va record 5 (root dir). So `$SI` va `$FN`: ca hai deu co 4 timestamp.
   Day chinh la cho de phat hien timestomp (bai 10.1): tool timestomp thuong chi sua `$SI`, `$FN` van giu gio that.
3. Convert FILETIME sang gio nguoi doc bang python (xem `solution.md`). Nho FILETIME trong record la little-endian,
   phai dao byte truoc khi dua vao.

## Nhiem vu la bai tap (can Windows hoac NTFS ghi duoc, khong tai lap trong lab khong-root nay)
4. Tao file, timestomp bang tool sua `$SI`, roi phat hien lai bang cach so `$SI` voi `$FN` va nhin phan giay (cot `SI<FN` cua MFTECmd).
5. Giau 1 chuoi vao ADS cua file, tim lai bang `dir /r` va PowerShell; doc `Zone.Identifier` cua file vua tai ve.

## Dap an
Xem `solution.md`. Output that: `transcript.txt`.
