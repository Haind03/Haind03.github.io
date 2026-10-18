# Dap an Lab 1.3

## Nhiem vu giay but: parse 64 byte partition table

Dump cho san (entry #1 bat dau o 0x1BE, entry #2 o 0x1CE):

```
000001b0: .... .... .... .... .... .... .... ..80
000001c0: 0101 000b fe3f 8600 0800 0000 f82f 0300
000001d0: 00fe ffff 0083 feff ff00 3800 0300 c800
000001f0: 0000 0000 0000 0000 0000 0000 0000 55aa
```

Entry #1 (16 byte tu 0x1BE): `80 01 01 00 0B FE 3F 86 00 08 00 00 00 F8 2F 03`
- Boot flag = `0x80`: active.
- Type = `0x0B`: FAT32 (CHS).
- LBA start = byte 8..11 = `00 08 00 00` -> little-endian `0x00000800` = 2048 sector -> 2048 * 512 = 1048576 byte (1 MiB).
- So sector = byte 12..15 = `00 F8 2F 03` -> little-endian `0x032FF800` = 53475328 sector (gia tri minh hoa de luyen dao little-endian).
- LBA end = 2048 + 53475328 - 1 = 53477375.

Entry #2 (16 byte tu 0x1CE): `00 FE FF FF 83 FE FF FF 00 38 00 03 00 C8 00 00`
- Boot flag = `0x00`: khong active.
- Type = `0x83`: Linux.
- LBA start = byte 8..11 = `00 38 00 03` -> little-endian `0x03003800` = 50345984 sector.
- So sector = byte 12..15 = `00 C8 00 00` -> little-endian `0x0000C800` = 51200 sector = 25 MiB.

Diem chot: luon dao little-endian truoc khi cong, roi nhan sector size (512) de ra offset byte.

## Nhiem vu 2-3 (chay lab, so khop voi mmls)

MBR do `mkmbr.py` tao (xem `transcript.txt`):
- Entry #1: byte tai 0x1BE la `80 fe ff ff 0b fe ff ff 00 08 00 00 00 50 00 00`. LBA start `00 08 00 00` = 2048, so sector `00 50 00 00` = 0x5000 = 20480. `mmls` xac nhan: Win95 FAT32 (0x0b), Start 2048, Length 20480.
- Entry #2: LBA start 22528, Length 20480, type Linux (0x83). `mmls` khop.
- Hai phan vung lien nhau (22528 = 2048 + 20480), khong co khoang trong giua; chi co 2048 sector unallocated dau dia (truoc phan vung 1).

GPT do `mkgpt.py` tao:
- `xxd -s 512` thay chu ky `EFI PART` tai LBA 1.
- `mmls` liet ke GPT Header (LBA 1), Partition Table (LBA 2..33), EFI System (2048..10239), Linux root (10240..40959).
- Sector cuoi (43007) co backup header `EFI PART` (GPT luu 2 ban: dau va cuoi dia).

## Ghi nho
- MBR: bang phan vung o cuoi sector 0, 4 entry * 16 byte tu 0x1BE, chu ky `55 AA` o 0x1FE.
- GPT: protective MBR type `0xEE` o LBA 0, header `EFI PART` o LBA 1, entry array tu LBA 2, co ban backup o cuoi dia; CRC32 phai dung thi parser moi chap nhan.
