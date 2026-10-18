# Lab 3.3: Khoi phuc file da xoa

Lab chay that tren Linux (khong can root): khoi phuc file da xoa tren ext4 (debugfs rm) va FAT (xoa kieu 0xE5),
va demo vi sao ghi de lam mat du lieu.

## Cong cu
`mkfs.ext4`, `debugfs`, `mkfs.vfat`, `python3`, `fls`, `istat`, `icat`, `md5sum`.

## Chay lab
```bash
bash make.sh     # tao ext.img (baocao.txt da xoa) va fat.img (NOTE.TXT da xoa)
bash solve.sh    # fls -rd, istat, icat khoi phuc, so MD5, va demo ghi de
```
`transcript.txt` la output THAT. Image khong giu trong repo, chay `make.sh` tao lai.
`fatput.py` / `fatdel.py` chep/xoa file FAT (vi khong co mtools/mount).

## Nhiem vu (co lab chay that)
1. Tren ca hai image, dung `fls -rd` tim file da xoa, `istat` xem metadata, `icat` khoi phuc. So MD5 truoc va sau:
   ca ext4 va FAT deu khoi phuc khop tung byte voi file 1 cluster/lien tuc.
2. So sanh metadata: NTFS (bai 1.5) giu du timestamp va duong dan; FAT ngheo hon (ten 8.3, it moc thoi gian);
   ext4 giu 4 timestamp + co moc Deleted.
3. Tinh huong ghi de: sau khi xoa file tren FAT, chep file khac de len dung cluster do roi thu `icat` lai entry da xoa.
   Noi dung cu da bi thay -> khong cuu dung nua. Rut ra: ngung dung o NGAY khi can khoi phuc.

## Nhiem vu la bai tap (can Windows / NTFS ghi duoc)
4. NTFS: tao file nho (<700 byte) de thanh resident trong `$MFT`, xoa, roi `istat` thay noi dung nam ngay trong record,
   khoi phuc khong phu thuoc cluster ngoai. (Moi truong khong-root nay khong ghi duoc file vao NTFS, xem khai niem o bai 1.5.)
5. Recycle Bin: xoa file qua thung rac Windows, tim cap `$I`/`$R` trong `C:\$Recycle.Bin\<SID>\`, doc `$I` bang hex
   lay duong dan goc va thoi diem xoa, roi khoi phuc `$R`. Doi chieu bang RBCmd.

## Dap an
Xem `solution.md`. Output that: `transcript.txt`.
