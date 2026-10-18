# Dap an Lab 1.5

## Nhiem vu 1: parse MFT record tho (mft_rec0.bin la record $MFT)

4 byte dau: `46 49 4C 45` = "FILE" (record hop le; neu la `BAAD` thi record hong).

Header (so tu `mftparse.py`, xem `transcript.txt` B5):
- Offset toi update sequence (0x04) = 48, count = 3.
- Offset toi attribute dau (0x14) = 56 (0x38).
- Flags (0x16) = 0x0001 -> IN_USE + FILE (bit 0x01 = dang dung, bit 0x02 = directory; record nay la file, dang dung).
- Used / Allocated = 408 / 1024 byte.
- Attributes: `$STANDARD_INFORMATION` (0x10, resident), `$FILE_NAME` (0x30, resident), `$DATA` (0x80, non-resident), `$BITMAP` (0xB0, non-resident), roi END marker 0xFFFFFFFF.

## Nhiem vu 2: istat record 0 va 5

- Record 0 = `$MFT`: Allocated File, co `$STANDARD_INFORMATION` voi 4 timestamp.
- Record 5 = root directory: Allocated Directory, co CA `$STANDARD_INFORMATION` VA `$FILE_NAME`.
  Diem quan trong: `$SI` va `$FN` deu luu Created/Modified/MFT-Modified/Accessed. Tool timestomp pho thong
  chi ghi de `$SI`, con `$FN` (chi kernel cap nhat) van giu gio that -> so hai cum nay la cach phat hien timestomp.

## Nhiem vu 3: convert FILETIME

FILETIME = so don vi 100ns ke tu 1601-01-01 UTC. Mot dong python:
```
python3 -c "import datetime; v=0x01DA6F1C4B2E9A30; print(datetime.datetime(1601,1,1)+datetime.timedelta(microseconds=v//10))"
# -> 2024-03-05 16:43:47.196369
```
Luu y: byte trong record la little-endian, phai dao byte (vd `30 9A 2E 4B 1C 6F DA 01` -> 0x01DA6F1C4B2E9A30) truoc khi dua vao.

## Nhiem vu 4-5 (bai tap, can Windows)

- Timestomp: dung `SetMACE`/`nTimestomp` sua `$SI`, roi MFTECmd cot `SI<FN` = true la dau hieu. Trong lab khong-root
  ta khong co file NTFS ghi duoc, nhung da hieu CO CHE qua nhiem vu 2.
- ADS: `echo secret > file.txt:hidden` tao stream an; `dir /r` va `Get-Item -Stream *` liet ke; `Get-Content file.txt:Zone.Identifier`
  doc nguon tai ve (MOTW). ADS chi song tren NTFS, copy sang FAT la mat. Chi tiet ADS trong bai 3.4.

## Ghi nho
- MFT record 1024 byte, signature `FILE`, offset attribute dau o 0x14, flags o 0x16.
- `$SI` sua duoc boi user-mode (timestomp), `$FN` thi khong -> so hai cum de bat gia mao.
