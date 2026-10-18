#!/usr/bin/env bash
# Lab 1.6 - solve: dumpe2fs, fls -r, icat, istat (4 timestamp), roi xoa va khoi phuc.
set -u
cd "$(dirname "$0")"
IMG=lab16.ext4

echo "=== B1: dumpe2fs - block size, inode size, backup superblock ==="
dumpe2fs "$IMG" 2>/dev/null | grep -iE 'Block size|Inode size|Blocks per group|superblock at' | head

echo
echo "=== B2: fls -r - cay thu muc + inode ==="
fls -r "$IMG" 2>&1 | head

echo
echo "=== B3: icat doc noi dung theo inode ==="
INO=$(fls -r "$IMG" 2>/dev/null | awk '/baocao.txt/{gsub(/:/,"",$2);print $2;exit}')
echo "inode baocao.txt = $INO"
icat "$IMG" "$INO" 2>&1

echo
echo "=== B4: istat - 4 timestamp (co ca File Created cua ext4) ==="
istat "$IMG" "$INO" 2>&1 | sed -n '1,22p'

echo
echo "=== B5: xoa /baocao.txt roi kiem fls -r (dau *) va icat khoi phuc ==="
echo -n "MD5 goc: "; md5sum baocao.txt | awk '{print $1}'
debugfs -w -R "rm /baocao.txt" "$IMG" >/dev/null 2>&1
fls -r "$IMG" 2>&1 | grep -i baocao
echo -n "icat inode $INO sau xoa: "; icat "$IMG" "$INO" 2>/dev/null | md5sum | awk '{print $1 "  (md5 noi dung khoi phuc)"}'
