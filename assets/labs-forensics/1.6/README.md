# Lab 1.6: ext4 - inode, timestamp, superblock, khoi phuc

Lab chay that tren Linux (khong can root): `mkfs.ext4` tren file thuong, `debugfs` ghi file/thu muc
ma khong mount, Sleuth Kit doc nguoc.

## Cong cu
`mkfs.ext4`, `debugfs`, `dumpe2fs` (e2fsprogs), `fls`, `icat`, `istat` (Sleuth Kit), `md5sum`.

## Chay lab
```bash
bash make.sh     # tao lab16.ext4 (block 1024), ghi /baocao.txt va /hoso/ketoan.csv
bash solve.sh    # dumpe2fs, fls -r, icat, istat, roi xoa va khoi phuc
```
`transcript.txt` la output THAT. Image `lab16.ext4` (16MB) khong giu trong repo, chay `make.sh` tao lai.
Chon block size 1024 de image 16MB co 2 block group, nhin ro backup superblock.

## Nhiem vu
1. Dung `dumpe2fs` tim block size, inode size, va vi tri backup superblock (lab nay: block 8193).
2. Tao file, ghi noi dung, dung `istat` (hoac `debugfs -R "stat <inode>"`) doc du 4 timestamp. Chi ra dau la
   create time that cua ext4, va giai thich vi sao `stat` thuong khong in no (truong `crtime` moi co tu ext4,
   nhieu phien ban `stat` userland khong hien).
3. Xoa file, `fls -r` xac nhan dau `*`, roi `icat` theo inode. Trong lab nay `icat` van ra noi dung (md5 khop).
   Giai thich vi sao tren o ext4 MOUNT that thi `icat` thuong ra rong, va neu rong thi cuu bang cach nao.

## Dap an
Xem `solution.md`. Output that: `transcript.txt`.
