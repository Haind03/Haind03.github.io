# Dap an Lab 1.6

## Nhiem vu 1: dumpe2fs

Tu `transcript.txt` B1:
- Block size: 1024 byte.
- Inode size: 256 byte (du cho truong `crtime` = create time).
- Blocks per group: 8192. Primary superblock o block 1, backup superblock o block 8193 (dau block group 2).
  Backup superblock giup cuu file system khi superblock chinh hong: `mke2fs -n` liet ke het vi tri, `fsck -b 8193` dung ban backup.

## Nhiem vu 2: 4 timestamp

`istat` in 4 moc:
- Accessed (atime), File Modified (mtime), Inode Modified (ctime), File Created (crtime).
`File Created` la create time THAT cua ext4, luu trong truong `crtime` cua inode (chi co khi inode size >= 256).
Lenh `stat` userland co ban thuong khong in crtime vi API `stat()` cu khong tra ve no; phai dung `debugfs -R "stat <inode>"`
hoac `statx()` moi thay. Trong lab ca 4 moc bang nhau vi file vua tao xong.

## Nhiem vu 3: xoa va khoi phuc

- Sau `debugfs rm /baocao.txt`, `fls -r` hien `r/r * 13: baocao.txt` (dau `*` = deleted).
- Trong lab nay `icat lab16.ext4 13` VAN ra noi dung, md5 khop ban goc (`96ca51f8...`): voi image tao bang debugfs,
  con tro extent trong inode chua bi xoa nen TSK doc lai duoc.
- TREN O EXT4 MOUNT THAT: khi xoa, kernel thuong zero cac con tro extent/block trong inode, nen `icat` ra RONG du data block
  van con tren dia. Hai huong cuu khi do:
  1. Carving / doc truc tiep vung unallocated: `blkls` trich unallocated roi `strings`/carve (bai 3.2, 3.3); hoac doc journal.
  2. Cong cu chuyen ext: `extundelete`, `ext4magic` (doc journal de dung lai mapping block vua bi xoa).

## Ghi nho
- Luon lam viec tren ban sao, mount `ro,noatime` neu phai mount (khong lam ban atime).
- inode giu metadata + con tro block (extent); xoa file ext4 that hay xoa con tro -> phai carve/journal de cuu.
- crtime chi doc duoc qua `debugfs stat` hoac `istat`, khong phai `stat` thuong.
