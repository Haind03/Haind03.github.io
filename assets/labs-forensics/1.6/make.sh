#!/usr/bin/env bash
# Lab 1.6 - ext4: tao image bang mkfs.ext4, ghi file + thu muc bang debugfs (khong mount, khong root).
set -eu
cd "$(dirname "$0")"
IMG=lab16.ext4
rm -f "$IMG" baocao.txt ketoan.csv

dd if=/dev/zero of="$IMG" bs=1M count=16 status=none
mkfs.ext4 -q -F -b 1024 -L LAB16 "$IMG"   # block 1024 de co nhieu block group (xem backup superblock)

printf 'bao cao dieu tra - noi dung mat quy 3\n' > baocao.txt
printf 'thang,doanh thu\n9,1250000000\n10,980000000\n' > ketoan.csv

debugfs -w "$IMG" >/dev/null 2>&1 <<'EOF'
mkdir /hoso
write baocao.txt baocao.txt
write ketoan.csv /hoso/ketoan.csv
EOF

echo "[make] da tao $IMG voi /baocao.txt, /hoso/ketoan.csv"
ls -l "$IMG"
