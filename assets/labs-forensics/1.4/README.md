# Lab 1.4: FAT16 - cau truc, directory entry, khoi phuc file da xoa

Lab chay that tren Linux (khong can root). Moi truong nay KHONG co mtools va khong mount duoc,
nen de chep file vao FAT ta dung `fatput.py` (ghi thang directory entry + FAT + cluster theo BPB).
Doc va khoi phuc thi dung Sleuth Kit chay thang tren file image.

## Cong cu
`mkfs.vfat`, `python3`, `fsstat`, `fls`, `istat`, `icat`, `xxd`, `md5sum`.

## Chay lab
```bash
bash make.sh     # tao lab14.fat (FAT16), chep NOTE.TXT va LUONG.TXT
bash solve.sh    # fsstat/fls/istat, xoa LUONG.TXT, khoi phuc bang icat, so MD5
```
`transcript.txt` la output THAT. Image `lab14.fat` (16MB) khong giu trong repo, chay `make.sh` tao lai.

## Scripts
- `fatput.py IMG NAME.EXT datafile` : chep 1 file (<= 1 cluster) vao slot root trong, cluster trong dau tien.
- `fatdel.py IMG NAME.EXT`          : xoa file kieu FAT (dat byte dau entry = 0xE5, free FAT chain).

## Nhiem vu
1. Parse tay 1 directory entry (32 byte) trong `solution.md` muc "Nhiem vu giay but": tim ten day du, attribute, first cluster (ghep high + low word), file size. Chu y bay high word.
2. Chay lab: dung `fsstat` doc layout (reserved / FAT0 / FAT1 / root dir / data). `xxd -l 64` doc BPB. `fls` liet ke file. `istat` doc first cluster + sector + size cua NOTE.TXT.
3. Khoi phuc file da xoa: solve.sh xoa LUONG.TXT, roi `fls -rd` thay `_UONG.TXT` (ten dau bi thay 0xE5), `icat` lay lai noi dung, `md5sum` chung minh khop tung byte voi ban goc.

## Dap an
Xem `solution.md`. Output that: `transcript.txt`.
