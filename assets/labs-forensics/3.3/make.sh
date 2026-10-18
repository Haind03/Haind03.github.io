#!/usr/bin/env bash
# Lab 3.3 - khoi phuc file da xoa tren ext4 va FAT (khong can root).
set -eu
cd "$(dirname "$0")"
rm -f ext.img fat.img baocao.txt note.txt big.bin

# --- ext4: tao file roi xoa bang debugfs ---
dd if=/dev/zero of=ext.img bs=1M count=8 status=none
mkfs.ext4 -q -F -b 1024 ext.img
printf 'so lieu quy 3: doanh thu 12.5 ty, chi 9.1 ty\n' > baocao.txt
debugfs -w -R "write baocao.txt baocao.txt" ext.img >/dev/null 2>&1
debugfs -w -R "rm /baocao.txt" ext.img >/dev/null 2>&1

# --- FAT: tao file roi xoa kieu 0xE5 ---
dd if=/dev/zero of=fat.img bs=1M count=16 status=none
mkfs.vfat -F 16 -n LABFAT fat.img >/dev/null 2>&1
printf 'mat khau wifi: Sun#Shine#2024\n' > note.txt
python3 -I fatput.py fat.img NOTE.TXT note.txt >/dev/null
python3 -I fatdel.py fat.img NOTE.TXT >/dev/null

echo "[make] da tao ext.img (baocao.txt da xoa) va fat.img (NOTE.TXT da xoa)"
ls -l ext.img fat.img
