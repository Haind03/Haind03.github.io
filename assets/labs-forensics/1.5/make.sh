#!/usr/bin/env bash
# Lab 1.5 - NTFS: tao image NTFS nho bang mkntfs (khong can root), trich 1 MFT record tho.
set -eu
cd "$(dirname "$0")"
IMG=lab15.ntfs
rm -f "$IMG" mft_rec0.bin mft_rec5.bin

dd if=/dev/zero of="$IMG" bs=1M count=10 status=none
mkntfs -Q -F -L LABNTFS "$IMG" >/dev/null 2>&1

# $MFT la inode 0; moi record 1024 byte. Trich record 0 ($MFT) va record 5 (root dir).
icat "$IMG" 0 2>/dev/null | head -c 1024 > mft_rec0.bin
icat "$IMG" 0 2>/dev/null | dd bs=1024 skip=5 count=1 2>/dev/null > mft_rec5.bin

echo "[make] da tao $IMG, trich mft_rec0.bin ($(stat -c%s mft_rec0.bin)B) va mft_rec5.bin ($(stat -c%s mft_rec5.bin)B)"
ls -l "$IMG" mft_rec0.bin mft_rec5.bin
