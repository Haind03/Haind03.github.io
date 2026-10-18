# Dap an Lab 1.4

## Nhiem vu giay but: parse 1 directory entry FAT32 (32 byte)

```
42 41 4f 43 41 4f 20 20 44 4f 43 20 00 00 50 8e
48 5d 48 5d 03 00 50 8e 48 5d 11 20 00 40 00 00
```

- Ten (byte 0..7) = `42 41 4f 43 41 4f 20 20` = "BAOCAO  ", ext (byte 8..10) = `44 4f 43` = "DOC" -> BAOCAO.DOC.
- Attribute (byte 11) = `0x20` = ARCHIVE (file thuong).
- First cluster HIGH (byte 20..21) = `03 00` = 0x0003; LOW (byte 26..27) = `11 20` = 0x2011.
  Ghep: (0x0003 << 16) | 0x2011 = 0x32011 = 204817.
- File size (byte 28..31) = `00 40 00 00` little-endian = 0x00004000 = 16384 byte.

Bay high word: cluster 204817 > 65535. Neu quen high word ban ra nham 0x2011 = 8209, sai hoan toan.

## Nhiem vu 2-3 (chay lab)

- `fsstat` cho layout (xem `transcript.txt`): Reserved 0-3, FAT0 4-35, FAT1 36-67, Root Directory 68-99, Cluster Area tu 100. Cluster 2 bat dau o sector 100.
- `xxd -l 64 lab14.fat` doc BPB: bytes/sector = `00 02` = 512, sectors/cluster = `04`, reserved = `04 00` = 4, so FAT = `02`, media = 0xF8, sectors/FAT = `20 00` = 32.
- `fls` liet ke: volume label LABFAT (inode 3), NOTE.TXT (4), LUONG.TXT (5). `istat` NOTE.TXT: Size 42, first cluster 2 -> sector 100.
- Xoa LUONG.TXT: `fatdel.py` dat byte dau entry = 0xE5 va free FAT chain. `fls -rd` thay `r/r * 5: _UONG.TXT` (ten dau bi thay `_`, dau `*` la deleted). `icat lab14.fat 5` doc lai noi dung. `md5sum` truoc va sau trung: `a8885a7164761b6649ea30adc4f2e60e` -> khoi phuc khop tung byte.

## Vi sao FAT khoi phuc duoc file 1 cluster du da free FAT chain

Entry directory van giu first cluster va file size. Khi FAT chain bi free (ta set ve 0), TSK gia dinh file nam lien tiep tu first cluster theo so byte trong size. File 1 cluster thi lien tiep tuyet doi -> khoi phuc nguyen ven. File nhieu cluster va bi phan manh thi mat chain se khong khoi phuc dung thu tu -> phai carve (bai 3.2).

## Ghi nho
- FAT directory entry 32 byte; first cluster tach high (0x14) + low (0x1A); nam lay tu bit 15-9 cua date cong 1980.
- Xoa FAT = doi byte dau entry thanh 0xE5 + free chain; du lieu cluster van con.
