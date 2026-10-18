# Dap an Lab 3.3

## Nhiem vu 1: khoi phuc tren ext4 va FAT

ext4 (`ext.img`):
- `fls -rd` -> `r/r * 12: baocao.txt`. `istat` -> `Not Allocated`, co them moc `Deleted`.
- `icat ext.img 12` cho noi dung; md5 cuu = md5 goc = `dd486ead3cbc22982c89bb5d01b169f8` -> khop tung byte.

FAT (`fat.img`):
- `fls -rd` -> `r/r * 4: _OTE.TXT` (byte dau ten bi thay 0xE5, TSK hien `_`). `istat` -> `Not Allocated`, Size 30.
- `icat fat.img 4` cho noi dung; md5 cuu = md5 goc = `6345e5f3b2b8ffc682a52f3f363ca90c` -> khop tung byte.

## Nhiem vu 2: so metadata

- FAT: ten 8.3, chi vai moc thoi gian (Written day du, Created/Accessed thuong rong), mat chuoi cluster khi xoa.
- ext4: 4 timestamp + moc Deleted, con tro extent.
- NTFS (bai 1.5): giu `$SI` va `$FN` day du + duong dan qua parent MFT entry -> khoi phuc giau thong tin nhat.

## Nhiem vu 3: ghi de lam mat du lieu

Sau khi xoa NOTE.TXT (cluster 2 duoc free), ta chep OTHER.TXT va no tai su dung dung cluster 2.
`icat` lai entry da xoa (inode 4) gio doc ra noi dung MOI (`DU LIEU MOI DE LEN CLUSTER CU ...`), khong con la noi dung cu.
Bai hoc cot loi: xoa chi go metadata, du lieu con tren dia cho den khi bi GHI DE. Vi vay khi can khoi phuc phai ngung ghi
vao o ngay lap tuc (tat may dung cach, tao image lam viec, khong cai dat gi len o do).

## Nhiem vu 4-5 (bai tap Windows)

- NTFS resident: file < ~700 byte nam ngay trong record `$MFT` (attribute `$DATA` resident). Xoa roi `istat` van thay data trong record,
  khoi phuc khong can cluster ngoai. Moi truong khong-root o day khong ghi duoc file vao NTFS; xem co che record o bai 1.5.
- Recycle Bin: moi file xoa sinh cap `$I<id>` (metadata: duong dan goc + thoi diem xoa) va `$R<id>` (noi dung). Doc `$I` bang hex
  hoac RBCmd -> biet AI xoa (SID trong duong dan), XOA GI (duong dan goc), KHI NAO, va NOI DUNG ($R).

## Ghi nho
- `fls -rd` liet ke deleted, `istat` xem metadata, `icat` moi du lieu.
- NTFS khoi phuc sach hon FAT; FAT mat chuoi cluster nen file phan manh phai carve (bai 3.2).
- Ghi de = mat vinh vien: ngung dung o ngay khi can khoi phuc.
