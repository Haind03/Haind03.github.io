# Lab 1.2: Sector, cluster, slack va du lieu cu con sot

Lab chay that tren Linux (khong can root), dung `debugfs` thao tac tren ext4 image ma khong mount.

## Cong cu
`mkfs.ext4`, `debugfs`, `fsstat`, `fls`, `istat`, `blkls`, `blkcat`, `strings`, `xxd` (Sleuth Kit + e2fsprogs).

## Chay lab
```bash
bash make.sh     # tao lab12.ext4 (block 1024): ghi file lon, xoa, ghi file nho
bash solve.sh    # doc lai du lieu cu bang blkls/blkcat
```
`transcript.txt` la output THAT. `blocks.txt` ghi so block de solve.sh tro toi dung cho.

Luu y: image `lab12.ext4` (8MB) va `unalloc.raw` khong giu trong repo cho nhe, chay `make.sh` de tao lai.

## Nhiem vu
1. Tinh tay (xem `solution.md`): sector 512 byte, cluster 8192 byte, file 20000 byte. Hoi: so cluster, byte cap phat, RAM slack, drive slack, offset tuyet doi cua phan vung bat dau o LBA 2048.
2. Chay lab: xac dinh block size bang `fsstat`. Dung `istat` xem file nho chiem tron 1 block du noi dung chi 19 byte (do la ban chat file slack).
3. Trich toan bo vung unallocated bang `blkls`, dung `strings` tim pattern `OLD-SECRET-DATA` cua file da xoa. Dung `blkcat` doc truc tiep mot block cu.
4. Hieu gioi han lab khong-root: `debugfs write` zero-pad tron block cua file moi nen slack ngay trong block do doc ra 0; tren o that qua mount, OS khong zero duoi block nen slack giu du lieu cu. Du vay du lieu cu van con o cac block unallocated.

## Dap an
Xem `solution.md`. Output that: `transcript.txt`.
