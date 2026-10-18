#!/usr/bin/env bash
# Lab 1.2 - slack / du lieu cu con sot: tao ext4 image (block 1024), ghi file lon,
# xoa, roi ghi file nho hon. Khong can root (dung debugfs, khong mount).
set -eu
cd "$(dirname "$0")"
IMG=lab12.ext4
rm -f "$IMG" big.bin small.bin blocks.txt

dd if=/dev/zero of="$IMG" bs=1M count=8 status=none
mkfs.ext4 -q -F -b 1024 "$IMG"

# File lon voi pattern de nhan ra, roi ghi vao image
python3 -c "open('big.bin','wb').write(b'OLD-SECRET-DATA-'*4000)"   # ~64000 byte
debugfs -w -R "write big.bin big.bin" "$IMG" >/dev/null 2>&1

# Ghi lai cac block cua file lon TRUOC khi xoa (de lab tro toi mot block cu)
FIRST=$(istat "$IMG" 12 2>/dev/null | awk '/Direct Blocks/{getline; print $1; exit}')
echo "big_first_block=$FIRST" > blocks.txt
echo "probe_block=$((FIRST+5))" >> blocks.txt   # mot block cu, gan nhu chac khong bi tai su dung

# Xoa file lon
debugfs -w -R "rm /big.bin" "$IMG" >/dev/null 2>&1

# Ghi mot file nho hon (chi vai byte) -> chiem tron 1 block, phan con lai la slack
printf 'DU LIEU MOI (ngan)\n' > small.bin
debugfs -w -R "write small.bin small.bin" "$IMG" >/dev/null 2>&1

echo "[make] xong. $(cat blocks.txt | tr '\n' ' ')"
ls -l "$IMG"
